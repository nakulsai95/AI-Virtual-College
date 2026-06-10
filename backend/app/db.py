"""SQLite persistence — the college survives restarts.

Everything the app shows lives here: the curriculum, faculty (with live
grades + methodology versions), the learner's lessons/board/exams/mastery,
the channels, the reward feed, and LLM usage for the credit budget.

Single-learner local model: one college row, one student row, one file
(backend/aula.db, git-ignored). Connections are opened per call — cheap for
SQLite and safe across FastAPI's threadpool.
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
from contextlib import contextmanager
from datetime import date, datetime

from .config import BASE_DIR

DB_PATH = BASE_DIR / "aula.db"

DEFAULT_METHODOLOGY = {
    "pacing": "normal",
    "sequence": "concept → practice",
    "modality": "blog + diagrams",
    "examples": "medium",
    "probe": "after-read",
}

# What the Provost falls back to when no LLM is connected.
EXAMPLES_FIRST_METHODOLOGY = {
    "pacing": "slow",
    "sequence": "examples → theory",
    "modality": "blog + worked examples",
    "examples": "high",
    "probe": "after-practice",
}

DEFAULT_BUDGET_CAP = 5.0  # USD of LLM credits before agents fall back to demo mode

# XP awards (the Registrar applies these; they only ever go up)
XP = {"checkin": 5, "probe_pass": 40, "probe_fail": 10, "exam_pass": 100, "exam_fail": 20}
RANK_THRESHOLDS = [0, 400, 1200, 2600]  # xp needed for tier 0..3

ROLE_HUES = {
    "principal": "#6e8efb", "provost": "#46d6ad", "examiner": "#f0846b",
    "registrar": "#e6c06a", "guide": "#9b6cff", "counselor": "#2dd4bf",
}
PROF_HUES = ["#f5a623", "#3b82f6", "#e6c06a", "#2dd4bf", "#9b6cff", "#46d6ad"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS college(
  id INTEGER PRIMARY KEY CHECK (id = 1),
  goal TEXT, level TEXT, mission TEXT, weeks INTEGER, summary TEXT,
  started_at REAL
);
CREATE TABLE IF NOT EXISTS student(
  id INTEGER PRIMARY KEY CHECK (id = 1),
  name TEXT DEFAULT 'You', handle TEXT DEFAULT '@you', level TEXT DEFAULT 'intermediate',
  xp INTEGER DEFAULT 0, streak INTEGER DEFAULT 0,
  days_active INTEGER DEFAULT 0, last_active TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS faculty(
  id TEXT PRIMARY KEY, role TEXT, name TEXT, subject TEXT DEFAULT '',
  model TEXT DEFAULT '', hue TEXT DEFAULT '', status TEXT DEFAULT 'active',
  score INTEGER DEFAULT 78, version INTEGER DEFAULT 1,
  methodology TEXT DEFAULT '{}', note TEXT DEFAULT '', history TEXT DEFAULT '[78]'
);
CREATE TABLE IF NOT EXISTS subjects(
  id TEXT PRIMARY KEY, title TEXT, professor_id TEXT, prof_name TEXT,
  hue TEXT, sandboxes TEXT DEFAULT '[]', position INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS modules(
  id TEXT PRIMARY KEY, subject_id TEXT, position INTEGER,
  title TEXT, status TEXT DEFAULT 'locked', exam_status TEXT DEFAULT 'pending'
);
CREATE TABLE IF NOT EXISTS mastery(
  id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id TEXT, module_id TEXT,
  concept TEXT, level REAL DEFAULT 0, seen_at REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS lessons(
  id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id TEXT, subject TEXT,
  title TEXT, author TEXT, read_time TEXT DEFAULT '6 min', intro TEXT,
  sections TEXT DEFAULT '[]', probe TEXT DEFAULT '{}',
  sandbox TEXT DEFAULT 'python', code_language TEXT DEFAULT 'python',
  code_starter TEXT DEFAULT '', tag TEXT DEFAULT '', state TEXT DEFAULT 'new',
  created_at REAL
);
CREATE TABLE IF NOT EXISTS board(
  id INTEGER PRIMARY KEY AUTOINCREMENT, col TEXT, type TEXT, title TEXT,
  subject TEXT, meta TEXT DEFAULT '', tool INTEGER DEFAULT 0, good INTEGER,
  lesson_id INTEGER, created_at REAL
);
CREATE TABLE IF NOT EXISTS exams(
  id INTEGER PRIMARY KEY AUTOINCREMENT, module_id TEXT, subject TEXT,
  title TEXT, type TEXT DEFAULT 'Unit exam', week INTEGER DEFAULT 1,
  bar INTEGER DEFAULT 70, questions TEXT DEFAULT '[]',
  score INTEGER, status TEXT DEFAULT 'upcoming', feedback TEXT DEFAULT '',
  created_at REAL, taken_at REAL
);
CREATE TABLE IF NOT EXISTS channels(
  id TEXT PRIMARY KEY, kind TEXT, name TEXT, sub TEXT DEFAULT '',
  hue TEXT DEFAULT '', unread INTEGER DEFAULT 0, position INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS messages(
  id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id TEXT, who TEXT,
  role TEXT DEFAULT '', hue TEXT DEFAULT '', text TEXT, created_at REAL
);
CREATE TABLE IF NOT EXISTS feed(
  id INTEGER PRIMARY KEY AUTOINCREMENT, who TEXT, text TEXT,
  kind TEXT DEFAULT 'neutral', created_at REAL
);
CREATE TABLE IF NOT EXISTS usage(
  id INTEGER PRIMARY KEY AUTOINCREMENT, agent TEXT, provider TEXT, model TEXT,
  action TEXT DEFAULT '', input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0, cost REAL DEFAULT 0, created_at REAL
);
CREATE TABLE IF NOT EXISTS materials(
  id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id TEXT DEFAULT '',
  subject TEXT DEFAULT '', kind TEXT DEFAULT 'link', title TEXT,
  authors TEXT DEFAULT '', url TEXT DEFAULT '', summary TEXT DEFAULT '',
  tools TEXT DEFAULT '[]', added_by TEXT DEFAULT '', created_at REAL
);
CREATE TABLE IF NOT EXISTS catalog(
  id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id TEXT, module_id TEXT,
  topic TEXT, position INTEGER DEFAULT 0, status TEXT DEFAULT 'planned',
  lesson_id INTEGER, created_at REAL
);
CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY, value TEXT);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.executescript(_SCHEMA)
        # Lightweight migrations for columns added after first release.
        cols = [r["name"] for r in c.execute("PRAGMA table_info(lessons)")]
        if "refs" not in cols:
            c.execute("ALTER TABLE lessons ADD COLUMN refs TEXT DEFAULT '[]'")
        cols = [r["name"] for r in c.execute("PRAGMA table_info(modules)")]
        if "topics" not in cols:
            c.execute("ALTER TABLE modules ADD COLUMN topics TEXT DEFAULT '[]'")
        cols = [r["name"] for r in c.execute("PRAGMA table_info(materials)")]
        if "content" not in cols:
            c.execute("ALTER TABLE materials ADD COLUMN content TEXT DEFAULT ''")
        cols = [r["name"] for r in c.execute("PRAGMA table_info(lessons)")]
        if "objectives" not in cols:
            c.execute("ALTER TABLE lessons ADD COLUMN objectives TEXT DEFAULT '[]'")
        if "takeaways" not in cols:
            c.execute("ALTER TABLE lessons ADD COLUMN takeaways TEXT DEFAULT '[]'")


def reset_college() -> None:
    """Wipe the college (re-onboarding) but keep budget config + usage history."""
    with connect() as c:
        for t in ("college", "student", "faculty", "subjects", "modules", "mastery",
                  "lessons", "board", "exams", "channels", "messages", "feed",
                  "materials", "catalog"):
            c.execute(f"DELETE FROM {t}")
        c.execute("DELETE FROM config WHERE key='build_status'")


# --- config / budget ------------------------------------------------------

def get_config(key: str, default: str = "") -> str:
    with connect() as c:
        row = c.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


def set_config(key: str, value: str) -> None:
    with connect() as c:
        c.execute("INSERT INTO config(key,value) VALUES(?,?) "
                  "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


def budget_cap() -> float:
    try:
        return float(get_config("budget_cap", str(DEFAULT_BUDGET_CAP)))
    except ValueError:
        return DEFAULT_BUDGET_CAP


def set_budget_cap(cap: float) -> None:
    set_config("budget_cap", str(max(0.0, cap)))


def usage_total() -> float:
    with connect() as c:
        row = c.execute("SELECT COALESCE(SUM(cost),0) AS total FROM usage").fetchone()
        return float(row["total"])


def record_usage(agent: str, provider: str, model: str, action: str,
                 input_tokens: int, output_tokens: int, cost: float) -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO usage(agent,provider,model,action,input_tokens,output_tokens,cost,created_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (agent, provider, model, action, input_tokens, output_tokens, cost, time.time()))


def usage_summary() -> dict:
    cap = budget_cap()
    with connect() as c:
        by_agent = [dict(r) for r in c.execute(
            "SELECT agent, COUNT(*) AS calls, SUM(input_tokens) AS input_tokens, "
            "SUM(output_tokens) AS output_tokens, SUM(cost) AS cost "
            "FROM usage GROUP BY agent ORDER BY cost DESC")]
        recent = [dict(r) for r in c.execute(
            "SELECT agent, provider, model, action, input_tokens, output_tokens, cost, created_at "
            "FROM usage ORDER BY id DESC LIMIT 20")]
    used = sum(a["cost"] or 0 for a in by_agent)
    for r in recent:
        r["t"] = _rel(r.pop("created_at"))
    return {"cap": round(cap, 2), "used": round(used, 4),
            "remaining": round(max(0.0, cap - used), 4),
            "by_agent": by_agent, "recent": recent}


# --- feed -----------------------------------------------------------------

def log_feed(who: str, text: str, kind: str = "neutral") -> None:
    with connect() as c:
        c.execute("INSERT INTO feed(who,text,kind,created_at) VALUES(?,?,?,?)",
                  (who, text, kind, time.time()))


# --- college build (the semester-prep pipeline) ------------------------------

def set_build_status(stage: str, message: str, done: int, total: int,
                     finished: bool = False) -> None:
    set_config("build_status", json.dumps({
        "stage": stage, "message": message, "done": done, "total": total,
        "finished": finished,
    }))


def build_status() -> dict | None:
    raw = get_config("build_status", "")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


# --- materials (what the professors scrape into the library) -----------------

def add_material(subject_id: str, subject: str, kind: str, title: str,
                 authors: str = "", url: str = "", summary: str = "",
                 tools: list[str] | None = None, added_by: str = "",
                 content: str = "") -> None:
    with connect() as c:
        exists = c.execute("SELECT 1 FROM materials WHERE url=? AND url!=''",
                           (url,)).fetchone()
        if exists:
            return
        c.execute(
            "INSERT INTO materials(subject_id,subject,kind,title,authors,url,summary,tools,added_by,created_at,content) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (subject_id, subject, kind, title, authors, url, summary,
             json.dumps(tools or []), added_by, time.time(), content))


def materials_context(subject_id: str, topic: str = "",
                      limit: int = 8) -> tuple[str, list[dict]]:
    """The teaching corpus: the subject's most relevant materials for a topic.

    Returns (prompt_text, refs). What the professor teaches is extracted from
    this — titles, authors, and the summaries scraped from the sources.
    """
    with connect() as c:
        rows = [dict(r) for r in c.execute(
            "SELECT * FROM materials WHERE subject_id=?", (subject_id,)).fetchall()]
    if not rows:
        return "", []
    words = set(re.findall(r"[a-z]{3,}", (topic or "").lower()))

    def relevance(m: dict) -> int:
        text = (m["title"] + " " + (m.get("content") or m["summary"] or "")[:1500]).lower()
        depth = 2 if m.get("content") else 1 if m["summary"] else 0
        return sum(2 for w in words if w in text) + depth

    rows.sort(key=relevance, reverse=True)
    top = rows[:limit]
    lines = []
    for m in top:
        line = f"- [{m['kind']}] {m['title']}"
        if m["authors"]:
            line += f" — {m['authors']}"
        # Full scraped text (textbooks, articles) beats a one-line summary.
        body = (m.get("content") or "")[:900] or (m["summary"] or "")[:400]
        if body:
            line += f". {body}"
        lines.append(line)
    refs = [{"title": m["title"], "url": m["url"], "kind": m["kind"]} for m in top]
    return "\n".join(lines), refs


# --- onboarding seed ------------------------------------------------------

def seed_from_curriculum(curriculum: dict, goal: str, level: str) -> None:
    """Persist the Principal's curriculum as the whole college."""
    reset_college()
    now = time.time()
    faculty = curriculum.get("faculty", [])
    subjects = curriculum.get("subjects", [])

    with connect() as c:
        c.execute("INSERT INTO college(id,goal,level,mission,weeks,summary,started_at) "
                  "VALUES(1,?,?,?,?,?,?)",
                  (goal, level, curriculum.get("mission", goal),
                   int(curriculum.get("weeks", 12)), curriculum.get("summary", ""), now))
        c.execute("INSERT INTO student(id,level) VALUES(1,?)", (level,))

        prof_i = 0
        for f in faculty:
            role = f.get("role", "")
            hue = ROLE_HUES.get(role) or PROF_HUES[prof_i % len(PROF_HUES)]
            if role == "professor":
                prof_i += 1
            c.execute(
                "INSERT OR REPLACE INTO faculty(id,role,name,subject,model,hue,status,score,version,methodology,note,history) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (f.get("id") or f"{role}-{prof_i}", role, f.get("name", role.title()),
                 f.get("subject") or "", f.get("model", ""), hue,
                 "teaching" if role == "professor" else "active",
                 78, 1, json.dumps(DEFAULT_METHODOLOGY),
                 "Just hired — fresh methodology.", json.dumps([78])))

        for i, s in enumerate(subjects):
            sid = s.get("id") or f"s{i+1}"
            prof = next((f for f in faculty
                         if f.get("role") == "professor" and f.get("subject") == s.get("title")), None)
            c.execute("INSERT OR REPLACE INTO subjects(id,title,professor_id,prof_name,hue,sandboxes,position) "
                      "VALUES(?,?,?,?,?,?,?)",
                      (sid, s.get("title", f"Subject {i+1}"),
                       (prof or {}).get("id", ""), s.get("professor", (prof or {}).get("name", "")),
                       PROF_HUES[i % len(PROF_HUES)], json.dumps(s.get("sandboxes", [])), i))
            for j, m in enumerate(s.get("modules", [])):
                mid = m.get("id") or f"{sid}m{j+1}"
                c.execute("INSERT OR REPLACE INTO modules(id,subject_id,position,title,status,exam_status) "
                          "VALUES(?,?,?,?,?,?)",
                          (mid, sid, j, m.get("title", f"Module {j+1}"),
                           "active" if j == 0 else "locked", "pending"))
                c.execute("INSERT INTO mastery(subject_id,module_id,concept,level,seen_at) "
                          "VALUES(?,?,?,?,0)",
                          (sid, mid, m.get("title", f"Module {j+1}"), 0.0))

    _seed_channels()
    log_feed(_name("principal"), "College staffed — faculty hired.", "update")


def _seed_channels() -> None:
    now = time.time()
    with connect() as c:
        profs = c.execute("SELECT * FROM faculty WHERE role='professor'").fetchall()
        guide = c.execute("SELECT * FROM faculty WHERE role='guide'").fetchone()
        principal = c.execute("SELECT * FROM faculty WHERE role='principal'").fetchone()

        c.execute("INSERT INTO channels(id,kind,name,sub,hue,unread,position) VALUES(?,?,?,?,?,?,?)",
                  ("faculty-room", "room", "Faculty Room",
                   "where your teachers talk about your progress", "", 1, 0))
        if principal:
            c.execute("INSERT INTO messages(channel_id,who,role,hue,text,created_at) VALUES(?,?,?,?,?,?)",
                      ("faculty-room", principal["name"], "principal", principal["hue"],
                       "College is live. Professors — first modules are unlocked; keep me posted.", now))
        for i, p in enumerate(profs):
            c.execute("INSERT INTO messages(channel_id,who,role,hue,text,created_at) VALUES(?,?,?,?,?,?)",
                      ("faculty-room", p["name"], "professor", p["hue"],
                       f"Ready to teach {p['subject']}. First lesson on request.", now + i))
            c.execute("INSERT INTO channels(id,kind,name,sub,hue,unread,position) VALUES(?,?,?,?,?,?,?)",
                      (f"dm-{p['id']}", "dm", p["name"], f"{p['subject']} · Professor",
                       p["hue"], 0, i + 1))
            c.execute("INSERT INTO messages(channel_id,who,role,hue,text,created_at) VALUES(?,?,?,?,?,?)",
                      (f"dm-{p['id']}", p["name"], "professor", p["hue"],
                       f"Hi — I'm {p['name']}, your {p['subject']} professor. Ask me anything about the subject.", now))
        if guide:
            c.execute("INSERT INTO channels(id,kind,name,sub,hue,unread,position) VALUES(?,?,?,?,?,?,?)",
                      (f"dm-{guide['id']}", "dm", guide["name"], "Personal Guide · always on",
                       guide["hue"], 0, len(profs) + 1))
            c.execute("INSERT INTO messages(channel_id,who,role,hue,text,created_at) VALUES(?,?,?,?,?,?)",
                      (f"dm-{guide['id']}", guide["name"], "guide", guide["hue"],
                       "Stuck on anything? Ask me and I'll bring the right teacher in.", now))


# --- faculty / reward loop ------------------------------------------------

def _name(role: str) -> str:
    with connect() as c:
        row = c.execute("SELECT name FROM faculty WHERE role=?", (role,)).fetchone()
        return row["name"] if row else role.title()


def get_faculty(fid: str = "", role: str = "") -> dict | None:
    with connect() as c:
        if fid:
            row = c.execute("SELECT * FROM faculty WHERE id=?", (fid,)).fetchone()
        else:
            row = c.execute("SELECT * FROM faculty WHERE role=?", (role,)).fetchone()
        return _faculty_dict(row) if row else None


def _faculty_dict(row) -> dict:
    d = dict(row)
    d["methodology"] = json.loads(d.get("methodology") or "{}") or dict(DEFAULT_METHODOLOGY)
    d["history"] = json.loads(d.get("history") or "[78]")
    return d


def resolve_professor(professor_id: str = "", subject: str = "", name: str = "") -> dict | None:
    with connect() as c:
        rows = [_faculty_dict(r) for r in
                c.execute("SELECT * FROM faculty WHERE role='professor'").fetchall()]
    if not rows:
        return None
    if professor_id:
        for p in rows:
            if p["id"] == professor_id:
                return p
    for p in rows:
        if name and p["name"].lower() == name.lower():
            return p
        if subject and p["subject"].lower() == subject.lower():
            return p
    return rows[0]


def reward_professor(prof_id: str, delta: int, reason: str) -> dict | None:
    with connect() as c:
        row = c.execute("SELECT * FROM faculty WHERE id=?", (prof_id,)).fetchone()
        if not row:
            return None
        prof = _faculty_dict(row)
        prof["score"] = max(0, min(100, prof["score"] + delta))
        prof["history"] = (prof["history"] + [prof["score"]])[-10:]
        c.execute("UPDATE faculty SET score=?, history=? WHERE id=?",
                  (prof["score"], json.dumps(prof["history"]), prof_id))
    sign = f"+{delta}" if delta >= 0 else str(delta)
    log_feed(prof["name"], f"{reason} · {sign} to {prof['name']}",
             "pos" if delta >= 0 else "neg")
    return professor_snapshot(prof_id)


def set_methodology(prof_id: str, methodology: dict, note: str) -> dict | None:
    with connect() as c:
        row = c.execute("SELECT * FROM faculty WHERE id=?", (prof_id,)).fetchone()
        if not row:
            return None
        version = row["version"] + 1
        c.execute("UPDATE faculty SET version=?, methodology=?, note=? WHERE id=?",
                  (version, json.dumps(methodology), note, prof_id))
        name = row["name"]
    log_feed(_name("provost"),
             f"Rewrote {name}'s methodology · v{version-1} → v{version}", "update")
    return professor_snapshot(prof_id)


def professor_snapshot(prof_id: str) -> dict | None:
    prof = get_faculty(fid=prof_id)
    if not prof:
        return None
    score, hist = prof["score"], prof["history"]
    letter = "A−" if score >= 86 else "B+" if score >= 76 else "C" if score >= 60 else "D"
    trend = ("up" if len(hist) > 1 and hist[-1] > hist[0]
             else "down" if len(hist) > 1 and hist[-1] < hist[0] else "flat")
    return {"id": prof["id"], "name": prof["name"], "subject": prof["subject"],
            "score": score, "letter": letter, "trend": trend, "hue": prof["hue"],
            "version": prof["version"], "history": hist,
            "methodology": prof["methodology"], "note": prof["note"]}


# --- student / registrar --------------------------------------------------

def award_xp(amount: int) -> None:
    with connect() as c:
        c.execute("UPDATE student SET xp = xp + ? WHERE id=1", (amount,))


def check_in() -> dict | None:
    """Registrar: daily attendance + streak. Returns info on a NEW day, else None."""
    today = date.today().isoformat()
    with connect() as c:
        row = c.execute("SELECT * FROM student WHERE id=1").fetchone()
        if not row or row["last_active"] == today:
            return None
        yesterday = (datetime.now().toordinal() - 1)
        was_yesterday = False
        if row["last_active"]:
            try:
                was_yesterday = date.fromisoformat(row["last_active"]).toordinal() == yesterday
            except ValueError:
                pass
        streak = row["streak"] + 1 if was_yesterday else 1
        c.execute("UPDATE student SET last_active=?, streak=?, days_active=days_active+1, xp=xp+? WHERE id=1",
                  (today, streak, XP["checkin"]))
    log_feed(_name("registrar"), f"Attendance logged · {streak}-day streak", "neutral")
    return {"streak": streak}


# --- mastery ---------------------------------------------------------------

def bump_mastery(subject_id: str, module_id: str = "", amount: float = 0.1,
                 floor: float = 0.0) -> None:
    """Raise mastery for a module's concept (or the subject's active module)."""
    now = time.time()
    with connect() as c:
        if not module_id:
            row = c.execute("SELECT id FROM modules WHERE subject_id=? AND status='active' "
                            "ORDER BY position LIMIT 1", (subject_id,)).fetchone()
            if not row:
                return
            module_id = row["id"]
        c.execute("UPDATE mastery SET level = MIN(0.97, MAX(?, level + ?)), seen_at=? "
                  "WHERE module_id=?", (floor, amount, now, module_id))


# --- lessons / board --------------------------------------------------------

def add_lesson(lesson: dict, subject_id: str = "", board_card: bool = True,
               feed: bool = True) -> int:
    now = time.time()
    tag = (lesson.get("title") or "lesson").split()[0].strip(",.:").lower()
    with connect() as c:
        if not subject_id:
            row = c.execute("SELECT id FROM subjects WHERE title=?",
                            (lesson.get("subject", ""),)).fetchone()
            subject_id = row["id"] if row else ""
        cur = c.execute(
            "INSERT INTO lessons(subject_id,subject,title,author,read_time,intro,sections,probe,"
            "sandbox,code_language,code_starter,tag,state,created_at,refs,objectives,takeaways) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (subject_id, lesson.get("subject", ""), lesson.get("title", "Lesson"),
             lesson.get("author", "Professor"), lesson.get("read", "6 min"),
             lesson.get("intro", ""), json.dumps(lesson.get("sections", [])),
             json.dumps(lesson.get("probe", {})), lesson.get("sandbox", "python"),
             lesson.get("code_language", "python"), lesson.get("code_starter", ""),
             tag, "new", now, json.dumps(lesson.get("refs", [])),
             json.dumps(lesson.get("objectives", [])),
             json.dumps(lesson.get("takeaways", []))))
        lesson_id = cur.lastrowid
        if board_card:
            c.execute("INSERT INTO board(col,type,title,subject,meta,tool,lesson_id,created_at) "
                      "VALUES('lessons','lesson',?,?,?,0,?,?)",
                      (f"Read: {lesson.get('title','Lesson')}", lesson.get("subject", ""),
                       f"{lesson.get('read','6 min')} · {lesson.get('author','Professor')}",
                       lesson_id, now))
    if feed:
        log_feed(lesson.get("author", "Professor"),
                 f"Published lesson · “{lesson.get('title','Lesson')}”", "neutral")
    return lesson_id


def get_lesson(lesson_id: int) -> dict | None:
    with connect() as c:
        row = c.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone()
        if not row:
            return None
        c.execute("UPDATE lessons SET state='read' WHERE id=?", (lesson_id,))
    return _lesson_dict(row)


def _lesson_dict(row) -> dict:
    keys = row.keys()

    def col(name, default):
        return (row[name] if name in keys else None) or default

    return {
        "id": row["id"], "title": row["title"], "author": row["author"],
        "authorRole": "professor", "subject": row["subject"], "read": row["read_time"],
        "intro": row["intro"], "sections": json.loads(row["sections"] or "[]"),
        "probe": json.loads(row["probe"] or "{}"), "sandbox": row["sandbox"],
        "code_language": row["code_language"], "code_starter": row["code_starter"],
        "refs": json.loads(col("refs", "[]")),
        "objectives": json.loads(col("objectives", "[]")),
        "takeaways": json.loads(col("takeaways", "[]")),
        "next": "Build on this",
    }


def latest_lesson() -> dict | None:
    with connect() as c:
        row = c.execute("SELECT * FROM lessons ORDER BY id DESC LIMIT 1").fetchone()
    return _lesson_dict(row) if row else None


def add_board_card(col: str, type_: str, title: str, subject: str, meta: str,
                   good: bool | None = None, lesson_id: int | None = None) -> None:
    with connect() as c:
        c.execute("INSERT INTO board(col,type,title,subject,meta,tool,good,lesson_id,created_at) "
                  "VALUES(?,?,?,?,?,0,?,?,?)",
                  (col, type_, title, subject, meta,
                   None if good is None else int(good), lesson_id, time.time()))


# --- the catalog: every syllabus topic is a future class -----------------------

def seed_catalog(subject_id: str, module_id: str, topics: list[str]) -> None:
    """One catalog row per (module, topic). Idempotent."""
    now = time.time()
    with connect() as c:
        for i, t in enumerate(topics):
            exists = c.execute("SELECT 1 FROM catalog WHERE module_id=? AND topic=?",
                               (module_id, t)).fetchone()
            if not exists:
                c.execute("INSERT INTO catalog(subject_id,module_id,topic,position,status,created_at) "
                          "VALUES(?,?,?,?,'planned',?)", (subject_id, module_id, t, i, now))


def next_planned_catalog() -> dict | None:
    """The next class to write, in curriculum order."""
    with connect() as c:
        row = c.execute(
            "SELECT cat.*, s.title AS subject_title, m.title AS module_title, "
            "m.status AS module_status "
            "FROM catalog cat JOIN subjects s ON s.id = cat.subject_id "
            "JOIN modules m ON m.id = cat.module_id "
            "WHERE cat.status = 'planned' "
            "ORDER BY s.position, m.position, cat.position LIMIT 1").fetchone()
    return dict(row) if row else None


def first_planned_for_subject(subject_id: str) -> dict | None:
    with connect() as c:
        row = c.execute(
            "SELECT cat.*, s.title AS subject_title, m.title AS module_title, "
            "m.status AS module_status "
            "FROM catalog cat JOIN subjects s ON s.id = cat.subject_id "
            "JOIN modules m ON m.id = cat.module_id "
            "WHERE cat.status = 'planned' AND cat.subject_id = ? "
            "ORDER BY m.position, cat.position LIMIT 1", (subject_id,)).fetchone()
    return dict(row) if row else None


def get_catalog_entry(catalog_id: int) -> dict | None:
    with connect() as c:
        row = c.execute(
            "SELECT cat.*, s.title AS subject_title, m.title AS module_title, "
            "m.status AS module_status "
            "FROM catalog cat JOIN subjects s ON s.id = cat.subject_id "
            "JOIN modules m ON m.id = cat.module_id WHERE cat.id = ?",
            (catalog_id,)).fetchone()
    return dict(row) if row else None


def set_catalog_status(catalog_id: int, status: str, lesson_id: int | None = None) -> None:
    with connect() as c:
        if lesson_id is None:
            c.execute("UPDATE catalog SET status=? WHERE id=?", (status, catalog_id))
        else:
            c.execute("UPDATE catalog SET status=?, lesson_id=? WHERE id=?",
                      (status, lesson_id, catalog_id))


def catalog_counts() -> tuple[int, int]:
    with connect() as c:
        row = c.execute("SELECT SUM(CASE WHEN status='ready' THEN 1 ELSE 0 END) AS ready, "
                        "COUNT(*) AS total FROM catalog").fetchone()
    return (row["ready"] or 0, row["total"] or 0)


def module_status(module_id: str) -> str:
    with connect() as c:
        row = c.execute("SELECT status FROM modules WHERE id=?", (module_id,)).fetchone()
        return row["status"] if row else ""


def module_topics(module_id: str) -> list[str]:
    with connect() as c:
        row = c.execute("SELECT topics FROM modules WHERE id=?", (module_id,)).fetchone()
    try:
        return json.loads(row["topics"] or "[]") if row else []
    except (json.JSONDecodeError, KeyError, IndexError):
        return []


# --- exams -------------------------------------------------------------------

def next_exam_module() -> dict | None:
    """The active module that should be examined next."""
    with connect() as c:
        row = c.execute(
            "SELECT m.id AS module_id, m.title, s.title AS subject, s.id AS subject_id "
            "FROM modules m JOIN subjects s ON s.id = m.subject_id "
            "WHERE m.status='active' AND m.exam_status IN ('pending','failed') "
            "ORDER BY s.position, m.position LIMIT 1").fetchone()
    return dict(row) if row else None


def get_or_create_exam(module_id: str, questions_factory) -> dict | None:
    """Return the open exam for a module, creating it (via the Examiner) if needed."""
    with connect() as c:
        mod = c.execute("SELECT m.*, s.title AS subject_title FROM modules m "
                        "JOIN subjects s ON s.id=m.subject_id WHERE m.id=?",
                        (module_id,)).fetchone()
        if not mod:
            return None
        row = c.execute("SELECT * FROM exams WHERE module_id=? AND status='upcoming' "
                        "ORDER BY id DESC LIMIT 1", (module_id,)).fetchone()
        if row:
            return _exam_dict(row)
    questions = questions_factory(mod["subject_title"], mod["title"])
    week = current_week()
    with connect() as c:
        cur = c.execute(
            "INSERT INTO exams(module_id,subject,title,type,week,bar,questions,status,created_at) "
            "VALUES(?,?,?,?,?,70,?,'upcoming',?)",
            (module_id, mod["subject_title"], mod["title"], "Unit exam", week,
             json.dumps(questions), time.time()))
        row = c.execute("SELECT * FROM exams WHERE id=?", (cur.lastrowid,)).fetchone()
    log_feed(_name("examiner"), f"Set the “{mod['title']}” exam · bar 70", "update")
    return _exam_dict(row)


def get_exam(exam_id: int) -> dict | None:
    with connect() as c:
        row = c.execute("SELECT * FROM exams WHERE id=?", (exam_id,)).fetchone()
    return _exam_dict(row) if row else None


def _exam_dict(row) -> dict:
    return {"id": row["id"], "module_id": row["module_id"], "subject": row["subject"],
            "title": row["title"], "type": row["type"], "week": row["week"],
            "bar": row["bar"], "questions": json.loads(row["questions"] or "[]"),
            "score": row["score"], "status": row["status"], "feedback": row["feedback"]}


def finish_exam(exam_id: int, score: int, passed: bool, feedback: str) -> None:
    """Record the result and advance the curriculum on a pass."""
    with connect() as c:
        exam = c.execute("SELECT * FROM exams WHERE id=?", (exam_id,)).fetchone()
        if not exam:
            return
        c.execute("UPDATE exams SET score=?, status=?, feedback=?, taken_at=? WHERE id=?",
                  (score, "passed" if passed else "failed", feedback, time.time(), exam_id))
        mod = c.execute("SELECT * FROM modules WHERE id=?", (exam["module_id"],)).fetchone()
        if mod:
            c.execute("UPDATE modules SET exam_status=? WHERE id=?",
                      ("passed" if passed else "failed", mod["id"]))
            if passed:
                c.execute("UPDATE modules SET status='done' WHERE id=?", (mod["id"],))
                nxt = c.execute("SELECT id FROM modules WHERE subject_id=? AND status='locked' "
                                "ORDER BY position LIMIT 1", (mod["subject_id"],)).fetchone()
                if nxt:
                    c.execute("UPDATE modules SET status='active' WHERE id=?", (nxt["id"],))


def current_week() -> int:
    with connect() as c:
        row = c.execute("SELECT started_at, weeks FROM college WHERE id=1").fetchone()
    if not row:
        return 1
    days = max(0, (time.time() - (row["started_at"] or time.time())) / 86400)
    return min(row["weeks"] or 12, int(days // 7) + 1)


# --- channels ----------------------------------------------------------------

def add_message(channel_id: str, who: str, role: str, hue: str, text: str) -> dict:
    now = time.time()
    with connect() as c:
        c.execute("INSERT INTO messages(channel_id,who,role,hue,text,created_at) "
                  "VALUES(?,?,?,?,?,?)", (channel_id, who, role, hue, text, now))
        if role != "me":
            c.execute("UPDATE channels SET unread = unread + 1 WHERE id=?", (channel_id,))
    return {"who": who, "role": role, "hue": hue, "text": text, "t": _rel(now)}


def get_channel(channel_id: str) -> dict | None:
    with connect() as c:
        row = c.execute("SELECT * FROM channels WHERE id=?", (channel_id,)).fetchone()
    return dict(row) if row else None


def mark_channel_read(channel_id: str) -> None:
    with connect() as c:
        c.execute("UPDATE channels SET unread=0 WHERE id=?", (channel_id,))


# --- the big UI-shaped snapshot ------------------------------------------------

def enrolled() -> bool:
    with connect() as c:
        return c.execute("SELECT 1 FROM college WHERE id=1").fetchone() is not None


def ui_state() -> dict:
    """Everything the frontend renders, in the exact shapes the screens read."""
    if not enrolled():
        return {"enrolled": False}

    with connect() as c:
        college = dict(c.execute("SELECT * FROM college WHERE id=1").fetchone())
        student = dict(c.execute("SELECT * FROM student WHERE id=1").fetchone())
        faculty_rows = [_faculty_dict(r) for r in
                        c.execute("SELECT * FROM faculty ORDER BY rowid").fetchall()]
        subject_rows = [dict(r) for r in
                        c.execute("SELECT * FROM subjects ORDER BY position").fetchall()]
        module_rows = [dict(r) for r in
                       c.execute("SELECT * FROM modules ORDER BY subject_id, position").fetchall()]
        mastery_rows = [dict(r) for r in c.execute("SELECT * FROM mastery").fetchall()]
        lesson_rows = c.execute("SELECT * FROM lessons ORDER BY id DESC").fetchall()
        board_rows = [dict(r) for r in c.execute("SELECT * FROM board ORDER BY id DESC").fetchall()]
        exam_rows = [dict(r) for r in c.execute("SELECT * FROM exams ORDER BY id").fetchall()]
        feed_rows = [dict(r) for r in
                     c.execute("SELECT * FROM feed ORDER BY id DESC LIMIT 30").fetchall()]
        channel_rows = [dict(r) for r in
                        c.execute("SELECT * FROM channels ORDER BY position").fetchall()]
        message_rows = [dict(r) for r in
                        c.execute("SELECT * FROM messages ORDER BY id").fetchall()]
        material_rows = [dict(r) for r in
                         c.execute("SELECT * FROM materials ORDER BY id DESC").fetchall()]
        catalog_rows = [dict(r) for r in c.execute(
            "SELECT cat.id AS catalog_id, cat.topic, cat.status, cat.lesson_id, "
            "s.title AS subject_title, s.prof_name, m.title AS module_title "
            "FROM catalog cat JOIN subjects s ON s.id = cat.subject_id "
            "JOIN modules m ON m.id = cat.module_id "
            "ORDER BY s.position, m.position, cat.position").fetchall()]

    # student stats
    days_since_start = max(1, int((time.time() - (college["started_at"] or time.time())) / 86400) + 1)
    attendance = min(100, round(student["days_active"] / days_since_start * 100))
    xp = student["xp"]
    tier = max(i for i, t in enumerate(RANK_THRESHOLDS) if xp >= t)
    next_xp = RANK_THRESHOLDS[tier + 1] if tier + 1 < len(RANK_THRESHOLDS) else RANK_THRESHOLDS[-1] + 1400
    momentum = min(100, 30 + student["streak"] * 10)
    week = current_week()

    STUDENT = {
        "name": student["name"], "handle": student["handle"], "mission": college["mission"],
        "level": college["level"], "audience": "learner", "careerMode": True,
        "xp": xp, "rankTier": min(3, tier), "nextTierXp": next_xp,
        "streak": student["streak"], "momentum": momentum, "attendance": attendance,
        "week": week, "weeks": college["weeks"],
    }

    mods_by_subject: dict[str, list] = {}
    for m in module_rows:
        mods_by_subject.setdefault(m["subject_id"], []).append(m)

    SUBJECTS = []
    for s in subject_rows:
        mods = mods_by_subject.get(s["id"], [])
        # Progress = modules actually completed. Day one reads 0%, honestly.
        done = sum(1 for m in mods if m["status"] == "done")
        progress = round(done / max(1, len(mods)) * 100)
        SUBJECTS.append({
            "id": s["id"], "title": s["title"], "prof": s["professor_id"],
            "profName": s["prof_name"], "progress": progress, "hue": s["hue"],
            "sandboxes": json.loads(s["sandboxes"] or "[]"),
            "modules": [{"id": m["id"], "title": m["title"], "status": m["status"],
                         "exam": m["exam_status"],
                         "topics": json.loads(m.get("topics") or "[]")} for m in mods],
        })

    # budget split: every agent shares the global credit cap equally
    usage = usage_summary()
    spend_by_agent = {a["agent"]: a["cost"] or 0 for a in usage["by_agent"]}
    per_agent_cap = round(usage["cap"] / max(1, len(faculty_rows)), 2)

    FACULTY = []
    GRADES = []
    for f in faculty_rows:
        snap = professor_snapshot(f["id"]) if f["role"] == "professor" else None
        FACULTY.append({
            "id": f["id"], "role": f["role"], "name": f["name"], "hue": f["hue"],
            "subject": f["subject"] or None, "model": f["model"] or "—",
            "status": f["status"],
            "grade": ({"letter": snap["letter"], "score": snap["score"],
                       "trend": snap["trend"]} if snap else None),
            "budget": {"used": round(spend_by_agent.get(f["id"], 0), 3), "cap": per_agent_cap},
        })
        if snap:
            GRADES.append(snap)

    KANBAN = {"lessons": [], "doing": [], "submitted": [], "graded": []}
    for b in board_rows:
        col = b["col"] if b["col"] in KANBAN else "doing"
        KANBAN[col].append({
            "id": f"b{b['id']}", "title": b["title"], "subject": b["subject"],
            "type": b["type"], "meta": b["meta"], "tool": bool(b["tool"]),
            "good": None if b["good"] is None else bool(b["good"]),
            "lesson_id": b["lesson_id"],
        })

    EXAMS = [{
        "id": e["id"], "module_id": e["module_id"], "title": e["title"],
        "subject": e["subject"], "type": e["type"], "score": e["score"],
        "bar": e["bar"], "status": e["status"], "when": f"Wk {e['week']}",
    } for e in exam_rows]

    FEED = [{"t": _rel(f["created_at"]), "who": f["who"], "text": f["text"],
             "kind": f["kind"]} for f in feed_rows]

    msgs_by_channel: dict[str, list] = {}
    for m in message_rows:
        msgs_by_channel.setdefault(m["channel_id"], []).append(
            {"who": m["who"], "role": m["role"], "hue": m["hue"],
             "text": m["text"], "t": _rel(m["created_at"])})
    CHANNELS = [{"id": ch["id"], "kind": ch["kind"], "name": ch["name"],
                 "sub": ch["sub"], "hue": ch["hue"], "unread": ch["unread"],
                 "messages": msgs_by_channel.get(ch["id"], [])} for ch in channel_rows]

    # The Library is the full course catalog: every class, ready or planned.
    lessons_by_id = {r["id"]: r for r in lesson_rows}
    LIBRARY = []
    in_catalog: set[int] = set()
    for ce in catalog_rows:
        lrow = lessons_by_id.get(ce["lesson_id"]) if ce["lesson_id"] else None
        if lrow is not None:
            in_catalog.add(lrow["id"])
        LIBRARY.append({
            "id": lrow["id"] if lrow else f"c{ce['catalog_id']}",
            "catalog_id": ce["catalog_id"],
            "lesson_id": ce["lesson_id"] if lrow else None,
            "title": lrow["title"] if lrow else ce["topic"],
            "author": ce["prof_name"],
            "subject": ce["subject_title"],
            "module": ce["module_title"],
            "read": lrow["read_time"] if lrow else "—",
            "tag": lrow["tag"] if lrow else "class",
            "state": "ready" if lrow is not None else ce["status"],
        })
    # Lessons authored outside the catalog (Guide questions, direct requests).
    for r in lesson_rows:
        if r["id"] not in in_catalog:
            LIBRARY.append({"id": r["id"], "catalog_id": None, "lesson_id": r["id"],
                            "title": r["title"], "author": r["author"],
                            "subject": r["subject"], "module": "on request",
                            "read": r["read_time"], "tag": r["tag"], "state": "ready"})

    module_status = {m["id"]: m["status"] for m in module_rows}
    mastery_by_subject: dict[str, list] = {}
    for m in mastery_rows:
        rel = _rel(m["seen_at"])
        seen = ("locked" if module_status.get(m["module_id"]) == "locked"
                else "not yet" if not m["seen_at"]
                else "today" if rel == "now" else rel + " ago")
        mastery_by_subject.setdefault(m["subject_id"], []).append(
            {"name": m["concept"], "level": round(m["level"], 2), "seen": seen})
    MASTERY = [{"subject": s["title"], "hue": s["hue"],
                "concepts": mastery_by_subject.get(s["id"], [])} for s in subject_rows]

    MATERIALS = [{
        "id": m["id"], "subject": m["subject"], "kind": m["kind"],
        "title": m["title"], "authors": m["authors"], "url": m["url"],
        "summary": m["summary"], "tools": json.loads(m["tools"] or "[]"),
        "addedBy": m["added_by"],
    } for m in material_rows]

    return {
        "enrolled": True,
        "STUDENT": STUDENT, "SUBJECTS": SUBJECTS, "FACULTY": FACULTY,
        "KANBAN": KANBAN, "EXAMS": EXAMS, "GRADES": GRADES, "FEED": FEED,
        "CHANNELS": CHANNELS, "LIBRARY": LIBRARY, "MASTERY": MASTERY,
        "MATERIALS": MATERIALS,
        "LESSON": latest_lesson(),
        "NEXT_EXAM": next_exam_module(),
        "BUILD": build_status(),
        "USAGE": {"used": usage["used"], "cap": usage["cap"], "remaining": usage["remaining"]},
    }


# --- misc -----------------------------------------------------------------

def _rel(ts: float | None) -> str:
    if not ts:
        return "—"
    s = max(0, int(time.time() - ts))
    if s < 60:
        return "now"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h"
    return f"{s // 86400}d"
