"""End-to-end smoke test against the real app (mock LLM provider, temp DB).

Run: .venv\\Scripts\\python.exe smoke_test.py
"""
from __future__ import annotations

import os
import sys
import tempfile

# Use a throwaway database so the test never touches the real college, and
# pin the mock provider so the test NEVER spends real API credits — even if
# a key is present in .env. (load_dotenv does not override existing env vars.)
_tmp = tempfile.mkdtemp()
os.environ["AULA_TEST"] = "1"
os.environ["AULA_PROVIDER"] = "mock"
os.environ["AULA_API_KEY"] = ""
os.environ["AULA_NO_NET"] = "1"  # research is skipped — deterministic + offline

from app import db  # noqa: E402
from pathlib import Path  # noqa: E402

db.DB_PATH = Path(_tmp) / "aula-test.db"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
FAILED = []


def check(name: str, cond: bool, detail: str = ""):
    status = "ok " if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


db.init_db()

# 1. health + providers
r = client.get("/api/health")
check("health", r.status_code == 200 and r.json()["status"] == "ok")

r = client.get("/api/connectors/providers")
ids = [p["id"] for p in r.json()["providers"]]
check("providers include mistral+gemini", "mistral" in ids and "gemini" in ids, str(ids))

# 2. state before enrolment
r = client.get("/api/state")
check("state pre-enrol", r.status_code == 200 and r.json()["enrolled"] is False)

# 3. onboard (mock principal)
r = client.post("/api/onboard", json={"goal": "Become job-ready in backend Python", "level": "intermediate"})
check("onboard", r.status_code == 200, r.text[:300])
cur = r.json()["curriculum"]
roles = {f["role"] for f in cur["faculty"]}
check("all 7 roles hired", {"principal", "provost", "professor", "examiner",
                            "registrar", "guide", "counselor"} <= roles, str(roles))

# 4. full state after enrolment (TestClient runs the background build synchronously)
r = client.get("/api/state")
s = r.json()
check("state enrolled", s["enrolled"] is True)
check("state has subjects", len(s["SUBJECTS"]) >= 2)
check("state has faculty", len(s["FACULTY"]) >= 7)
check("state has channels", len(s["CHANNELS"]) >= 2)
check("state has mastery", len(s["MASTERY"]) >= 1 and len(s["MASTERY"][0]["concepts"]) >= 1)
check("state has next exam", s["NEXT_EXAM"] is not None, str(s.get("NEXT_EXAM")))
check("usage shape", "cap" in s["USAGE"] and "used" in s["USAGE"])
check("subjects start at 0%", all(x["progress"] == 0 for x in s["SUBJECTS"]),
      str([x["progress"] for x in s["SUBJECTS"]]))
first_subject = s["SUBJECTS"][0]

# 4b. the college build: catalog, factory, exams, kanban
check("build finished", s["BUILD"] is not None and s["BUILD"]["finished"], str(s.get("BUILD")))
check("syllabus detailed with topics",
      any(m.get("topics") for x in s["SUBJECTS"] for m in x["modules"]),
      str([m.get("topics") for x in s["SUBJECTS"] for m in x["modules"]][:3]))
check("catalog is university-sized (every topic = a class)",
      len(s["LIBRARY"]) >= sum(len(x["modules"]) for x in s["SUBJECTS"]),
      f"library={len(s['LIBRARY'])}")
check("content factory completed the catalog",
      all(l["state"] == "ready" for l in s["LIBRARY"]),
      str([(l['title'], l['state']) for l in s["LIBRARY"] if l['state'] != 'ready'][:3]))
_lesson_cards = [t for t in s["KANBAN"]["lessons"] if t["type"] == "lesson"]
check("board not flooded by the factory",
      0 < len(_lesson_cards) < len(s["LIBRARY"]),
      f"lesson cards={len(_lesson_cards)} catalog={len(s['LIBRARY'])}")

# 4c. 101 depth: objectives, multi-paragraph sections, takeaways
_ready = next(l for l in s["LIBRARY"] if l["state"] == "ready" and l["lesson_id"])
r = client.get(f"/api/lessons/{_ready['lesson_id']}")
_lj = r.json()["lesson"]
check("101 lesson shape (objectives/paras/takeaways)",
      bool(_lj["objectives"]) and bool(_lj["takeaways"])
      and bool(_lj["sections"] and _lj["sections"][0].get("paras")),
      str(_lj)[:200])

# 4e. flashcards + spaced repetition (Track C)
check("review summary in state", "due" in s.get("REVIEW", {}) and "total" in s.get("REVIEW", {}))
check("flashcards seeded from lessons", s["REVIEW"]["total"] > 0, str(s["REVIEW"]))
r = client.get("/api/review")
_cards = r.json()["cards"]
check("cards are due for review", len(_cards) > 0)
_before = client.get("/api/review").json()["counts"]["due"]
r = client.post("/api/review", json={"card_id": _cards[0]["id"], "grade": "good"})
check("review reschedules a card", r.status_code == 200
      and r.json()["counts"]["due"] == _before - 1, r.text[:200])

# 4f. interactive labs (Track A)
r = client.post("/api/lab/generate", json={"subject": first_subject["title"], "topic": "warm-up"})
check("lab generated", r.status_code == 200 and r.json()["lab"]["kind"] in
      ("sort", "steps", "scenario", "quiz", "match", "order", "bugfix"), r.text[:200])
check("lab teaches (steps have reveals)",
      r.json()["lab"]["kind"] != "steps" or
      all(st.get("reveal") for st in r.json()["lab"]["steps"]),
      str(r.json()["lab"])[:200])
_lab_id = r.json()["lab"]["id"]
r2 = client.post("/api/lab/generate", json={"subject": first_subject["title"], "topic": "warm-up"})
check("lab is cached on second call", r2.json().get("cached") is True and
      r2.json()["lab"]["id"] == _lab_id)
_xp_before = client.get("/api/state").json()["STUDENT"]["xp"]
r = client.post("/api/lab/complete", json={"subject": first_subject["title"], "score": 80,
                                           "topic": "warm-up"})
check("lab completion awards xp", r.status_code == 200
      and client.get("/api/state").json()["STUDENT"]["xp"] > _xp_before)

# playable game (arcade) — real canvas + score reporting, cached
r = client.post("/api/game/generate", json={"subject": first_subject["title"], "topic": "level one"})
_g = r.json()["lab"]
check("playable game generated", r.status_code == 200 and _g["kind"] == "arcade"
      and "<canvas" in _g["html"].lower() and "postmessage" in _g["html"].lower(),
      str(_g)[:160])
r2 = client.post("/api/game/generate", json={"subject": first_subject["title"], "topic": "level one"})
check("game cached on second call", r2.json().get("cached") is True)

# 4d. JIT: un-write one class, generate it on demand
with db.connect() as _c:
    _row = _c.execute("SELECT id FROM catalog ORDER BY id DESC LIMIT 1").fetchone()
    _c.execute("UPDATE catalog SET status='planned', lesson_id=NULL WHERE id=?", (_row["id"],))
r = client.post(f"/api/catalog/{_row['id']}/generate")
check("JIT class generation", r.status_code == 200 and r.json()["lesson"]["id"] > 0,
      r.text[:200])
check("exams prepared in advance",
      sum(1 for e in s["EXAMS"] if e["status"] == "upcoming") >= 1, str(s["EXAMS"]))
check("kanban practice cards", len(s["KANBAN"]["doing"]) >= 1, str(s["KANBAN"]["doing"]))
check("practice cards tagged with tools", any(t.get("tool") for t in s["KANBAN"]["doing"]))
_total_modules = sum(len(x["modules"]) for x in s["SUBJECTS"])
_board_cards = sum(len(v) for v in s["KANBAN"].values())
check("board covers the whole learning path", _board_cards >= _total_modules,
      f"cards={_board_cards} modules={_total_modules}")
check("materials list present", isinstance(s.get("MATERIALS"), list))
check("lesson exists up-front", s["LESSON"] is not None)

# 5. guide -> routed lesson
r = client.post("/api/guide", json={"message": "I don't get how JWT auth works"})
check("guide ask", r.status_code == 200, r.text[:300])
g = r.json()
check("guide routed", bool(g["route"]["subject"]) and bool(g["route"]["professor"]))
check("guide lesson authored", bool(g["lesson"]["title"]) and g["lesson"]["id"] > 0)
lesson_id = g["lesson"]["id"]

# 6. lesson library + detail
r = client.get("/api/state")
check("library has lesson", len(r.json()["LIBRARY"]) >= 1)
check("kanban has lesson card", len(r.json()["KANBAN"]["lessons"]) >= 1)
r = client.get(f"/api/lessons/{lesson_id}")
check("lesson detail", r.status_code == 200 and r.json()["lesson"]["id"] == lesson_id)

# 7. direct lesson endpoint
r = client.post("/api/lesson", json={"subject": first_subject["title"], "topic": "indexes",
                                     "professor": first_subject["profName"], "sandbox": "python"})
check("author lesson", r.status_code == 200 and bool(r.json()["lesson"]["title"]))

# 8. probe grading + reward loop
probe_q = g["lesson"]["probe"]["q"]
r = client.post("/api/grade", json={"kind": "probe", "question": probe_q,
                                    "answer": "It carries signed claims so the server can verify identity without storing sessions.",
                                    "bar": 70, "subject": first_subject["title"],
                                    "professor": first_subject["profName"]})
check("grade probe", r.status_code == 200, r.text[:300])
gr = r.json()
check("probe reward applied", gr["reward"] is not None and "professor" in gr["reward"])

# failing answers until the provost rewrites
changed = False
for _ in range(6):
    r = client.post("/api/grade", json={"kind": "probe", "question": probe_q, "answer": "no",
                                        "bar": 70, "subject": first_subject["title"],
                                        "professor": first_subject["profName"]})
    if r.json().get("reward", {}).get("methodology_changed"):
        changed = True
        break
check("provost rewrite triggers on repeated failure", changed)

r = client.get("/api/state")
grades = r.json()["GRADES"]
check("methodology version bumped", any(p["version"] > 1 for p in grades),
      str([(p["name"], p["version"]) for p in grades]))
check("xp awarded", r.json()["STUDENT"]["xp"] > 0, str(r.json()["STUDENT"]["xp"]))

# 9. exams: generate -> submit -> module advances
mod = r.json()["NEXT_EXAM"]
r = client.post("/api/exams/generate", json={"module_id": mod["module_id"]})
check("exam generated", r.status_code == 200, r.text[:300])
exam = r.json()["exam"]
check("exam has questions", len(exam["questions"]) >= 3)

answers = ["A thorough, reasoned answer explaining the concept with an example and tradeoffs."] * len(exam["questions"])
r = client.post(f"/api/exams/{exam['id']}/submit", json={"answers": answers})
check("exam submitted", r.status_code == 200, r.text[:300])
res = r.json()
check("exam graded", isinstance(res["score"], int) and len(res["per_question"]) == len(exam["questions"]))

r = client.get("/api/state")
s = r.json()
exam_row = next(e for e in s["EXAMS"] if e["id"] == exam["id"])
check("exam recorded", exam_row["status"] in ("passed", "failed"), exam_row["status"])
if res["passed"]:
    subj = next(x for x in s["SUBJECTS"] if x["title"] == exam["subject"])
    statuses = [m["status"] for m in subj["modules"]]
    check("module advanced", "done" in statuses, str(statuses))

# 10. channels: send a DM, get a persona reply
ch = next(c for c in s["CHANNELS"] if c["kind"] == "dm")
r = client.post(f"/api/channel/{ch['id']}/messages", json={"text": "Can you give me a hint?"})
check("channel send", r.status_code == 200 and len(r.json()["messages"]) == 2, r.text[:300])

# 11. sandbox runs real code on Windows
r = client.post("/api/sandbox/run", json={"sandbox": "python", "code": "print(sum(range(10)))"})
check("python sandbox", r.status_code == 200 and "45" in r.json()["stdout"], r.text[:300])
r = client.post("/api/sandbox/run", json={"sandbox": "sql", "code": "SELECT name FROM users ORDER BY age LIMIT 1;"})
check("sql sandbox", r.status_code == 200 and "Yuki" in r.json()["stdout"], r.text[:300])

# 12. budget endpoints
r = client.get("/api/usage")
check("usage endpoint", r.status_code == 200 and "cap" in r.json())
r = client.put("/api/budget", json={"cap": 12.5})
check("budget set", r.status_code == 200 and r.json()["cap"] == 12.5)

# account (local Gmail profile) reflects onto the live student
r = client.put("/api/profile", json={"name": "Alex Rivera", "email": "alex.rivera@gmail.com"})
check("profile set", r.status_code == 200 and r.json()["account"]["email"] == "alex.rivera@gmail.com")
_st = client.get("/api/state").json()["STUDENT"]
check("account reflected on student", _st["name"] == "Alex Rivera" and _st["handle"] == "@alex.rivera",
      str(_st.get("name")) + " / " + str(_st.get("handle")))

# 13. feed shows the whole story
r = client.get("/api/state")
feed_text = " | ".join(f["text"] for f in r.json()["FEED"])
check("feed has reward events", "to " in feed_text or "passed" in feed_text, feed_text[:200])

print()
if FAILED:
    print(f"{len(FAILED)} FAILED: {FAILED}")
    sys.exit(1)
print("ALL CHECKS PASSED")
