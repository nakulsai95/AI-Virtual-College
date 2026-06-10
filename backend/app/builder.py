"""The College Build — the faculty builds a full university, progressively.

Staged build (runs in the background after onboarding):
  0. The Principal details each subject's syllabus — every module broken into
     5-8 topics. Each topic becomes a CLASS in the catalog (a future lesson).
  1. Each Professor researches their subject and stocks the library —
     textbooks (Wikibooks, full text), articles, books, papers, course pages.
  2. Each Professor authors their subject's FIRST class in full 101 depth.
  3. The Examiner prepares the first exam for every subject.
  4. The Head lays out the learner's kanban for the whole path.
  5. THE CONTENT FACTORY: works through the rest of the catalog class by
     class — hundreds of full lessons — on the provider's cheap tier, until
     the university is complete or the credit budget runs low (then it
     pauses; raising the cap resumes it).

Every stage is idempotent: artifacts that already exist are skipped, so the
build can be resumed after a restart, a pause, or a crash.
"""
from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from . import db, research, store
from .agents import examiner, principal, professor
from .llm import build_provider, metered

log = logging.getLogger("aula.builder")

_BUDGET_RESERVE = 0.40  # pause the factory when fewer credits than this remain


def build_college() -> None:
    """The whole semester-prep pipeline. Safe to run (and re-run) in the background."""
    if not db.enrolled():
        return
    with db.connect() as c:
        subjects = [dict(r) for r in
                    c.execute("SELECT * FROM subjects ORDER BY position").fetchall()]
        modules = [dict(r) for r in
                   c.execute("SELECT * FROM modules ORDER BY subject_id, position").fetchall()]
    mods_by_subject: dict[str, list[dict]] = {}
    for m in modules:
        mods_by_subject.setdefault(m["subject_id"], []).append(m)

    # 4 staged steps per subject + the kanban plan; the factory tracks itself.
    total = len(subjects) * 4 + 1
    done = 0
    principal_name = (db.get_faculty(role="principal") or {}).get("name", "Principal")
    examiner_name = (db.get_faculty(role="examiner") or {}).get("name", "Examiner")

    try:
        for s in subjects:
            prof = db.resolve_professor(professor_id=s["professor_id"],
                                        subject=s["title"])
            prof_name = s["prof_name"] or (prof["name"] if prof else "Professor")
            mods = mods_by_subject.get(s["id"], [])
            first = mods[0] if mods else None
            sandboxes = json.loads(s["sandboxes"] or "[]") or ["python"]

            # -- 0. detailed syllabus, batch-wise: one subject per call ----------
            db.set_build_status("syllabus",
                                f"{principal_name} is detailing the {s['title']} syllabus…",
                                done, total)
            _detail_syllabus(s, mods)
            done += 1

            # -- 1. materials: scrape as much as the sources will give ----------
            if not _has_materials(s["id"]):
                db.set_build_status("materials",
                                    f"{prof_name} is gathering materials for {s['title']}…",
                                    done, total)
                n = _gather_materials(s, prof_name, sandboxes, mods)
                if n:
                    db.log_feed(prof_name,
                                f"Stocked the library · {n} materials for {s['title']}",
                                "neutral")
            done += 1

            # -- 2. the subject's first class, in full 101 depth -----------------
            entry = db.first_planned_for_subject(s["id"])
            if entry and not _subject_has_lessons(s["id"]):
                db.set_build_status("lessons",
                                    f"{prof_name} is teaching the first class — “{entry['topic']}”…",
                                    done, total)
                _author_class(entry, prof, prof_name, sandboxes[0])
            done += 1

            # -- 3. the first exam, prepared in advance --------------------------
            if first:
                db.set_build_status("exams",
                                    f"{examiner_name} is preparing the {s['title']} exam…",
                                    done, total)
                _prepare_exam(first["id"])
            done += 1

        # -- 4. the Head lays out the board -----------------------------------
        if not _board_planned():
            db.set_build_status("kanban", f"{principal_name} is planning your board…",
                                done, total)
            _plan_kanban(subjects, mods_by_subject)
            db.log_feed(principal_name,
                        "Planned your board — the whole path, week by week.", "update")
        done += 1

        # -- 5. the content factory: write the whole university ----------------
        _content_factory(principal_name)
    except Exception:  # noqa: BLE001 - never leave the build spinning forever
        log.exception("college build failed")
        ready, cat_total = db.catalog_counts()
        db.set_build_status("paused",
                            f"Build hit an error at {ready}/{cat_total} classes — "
                            "it will resume on restart or POST /api/build/continue.",
                            ready, max(cat_total, 1))


# --- the content factory -------------------------------------------------------

def _content_factory(principal_name: str) -> None:
    """Author every remaining class in the catalog, in curriculum order.

    Runs on the provider's CHEAP tier. Pauses (not fails) when credits run
    low or the model errors — raising the budget or /api/build/continue
    resumes exactly where it left off.
    """
    ready, total = db.catalog_counts()
    if total == 0:
        db.set_build_status("done", "College ready.", 1, 1, finished=True)
        return
    if ready >= total:
        db.set_build_status("done", f"University complete — {total} classes authored.",
                            total, total, finished=True)
        return

    authored_by: dict[str, int] = {}
    while True:
        entry = db.next_planned_catalog()
        if entry is None:
            break

        base = build_provider(store.get_connector())
        paid = base.id not in ("mock", "ollama")
        if paid:
            usage = db.usage_summary()
            if usage["cap"] > 0 and usage["remaining"] < _BUDGET_RESERVE:
                db.set_build_status(
                    "paused",
                    f"Paused at {ready}/{total} classes — credits low. "
                    "Raise the cap in Connections to keep building.",
                    ready, total)
                db.log_feed("system",
                            f"Content factory paused at {ready}/{total} classes — "
                            "credits low. Raise the cap to continue.", "neg")
                return

        db.set_catalog_status(entry["id"], "writing")
        db.set_build_status("factory",
                            f"Writing class {ready + 1}/{total} — “{entry['topic']}” "
                            f"({entry['subject_title']})…", ready, total)
        prof = db.resolve_professor(subject=entry["subject_title"])
        prof_name = prof["name"] if prof else "Professor"
        try:
            _author_class(entry, prof, prof_name, _subject_sandbox(entry["subject_id"]),
                          feed=False)
        except Exception as e:  # noqa: BLE001
            db.set_catalog_status(entry["id"], "planned")
            log.warning("factory: class “%s” failed: %s", entry["topic"], e)
            db.set_build_status(
                "paused",
                f"Paused at {ready}/{total} classes — the model errored "
                f"({str(e)[:80]}). It resumes on restart or when you continue the build.",
                ready, total)
            return

        ready += 1
        authored_by[prof_name] = authored_by.get(prof_name, 0) + 1
        if authored_by[prof_name] % 10 == 0:
            db.log_feed(prof_name,
                        f"Authored {authored_by[prof_name]} classes in "
                        f"{entry['subject_title']} · {ready}/{total} total", "neutral")
        if paid:
            time.sleep(0.3)

    ready, total = db.catalog_counts()
    db.set_build_status("done", f"University complete — {total} classes authored.",
                        total, max(total, 1), finished=True)
    db.log_feed(principal_name,
                f"University build complete — {total} classes across the catalog.",
                "pos")


def _author_class(entry: dict, prof: dict | None, prof_name: str,
                  sandbox: str, feed: bool = True) -> int:
    """Write one catalog class in full 101 depth, grounded in materials +
    syllabus, on the bulk (cheap) tier. Board card only for active modules."""
    methodology = (prof or {}).get("methodology") or dict(db.DEFAULT_METHODOLOGY)
    provider = metered(build_provider(store.get_connector()),
                       (prof or {}).get("id", "professor"), "author class",
                       tier="bulk")
    context, refs = db.materials_context(entry["subject_id"], entry["topic"])
    topics = db.module_topics(entry["module_id"])
    lesson = professor.design_lesson(
        provider, subject=entry["subject_title"], topic=entry["topic"],
        professor=prof_name, methodology=methodology, sandbox=sandbox,
        materials=context, syllabus_topics=topics, depth="full")
    lesson["refs"] = refs
    lesson_id = db.add_lesson(lesson, subject_id=entry["subject_id"],
                              board_card=(entry.get("module_status") == "active"),
                              feed=feed)
    db.set_catalog_status(entry["id"], "ready", lesson_id)
    return lesson_id


# --- staged-build helpers --------------------------------------------------------

def _detail_syllabus(subject: dict, mods: list[dict]) -> None:
    """The Principal expands this subject's modules into detailed topics and
    seeds the class catalog. Idempotent; mutates mods in place."""
    missing = [m for m in mods if not json.loads(m.get("topics") or "[]")]
    if missing:
        provider = metered(build_provider(store.get_connector()), "principal",
                           "detail syllabus")
        topic_map = principal.detail_subject_syllabus(
            provider, subject_title=subject["title"], modules=missing)
        if topic_map:
            with db.connect() as c:
                for mid, topics in topic_map.items():
                    c.execute("UPDATE modules SET topics=? WHERE id=?",
                              (json.dumps(topics), mid))
            for m in mods:
                if m["id"] in topic_map:
                    m["topics"] = json.dumps(topic_map[m["id"]])
    # Every topic becomes a class in the catalog (idempotent).
    for m in mods:
        topics = json.loads(m.get("topics") or "[]")
        if topics:
            db.seed_catalog(subject["id"], m["id"], topics)


def _has_materials(subject_id: str) -> bool:
    with db.connect() as c:
        row = c.execute("SELECT COUNT(*) AS n FROM materials WHERE subject_id=?",
                        (subject_id,)).fetchone()
        return (row["n"] or 0) > 3


def _subject_has_lessons(subject_id: str) -> bool:
    with db.connect() as c:
        row = c.execute("SELECT COUNT(*) AS n FROM lessons WHERE subject_id=?",
                        (subject_id,)).fetchone()
        return (row["n"] or 0) > 0


def _subject_sandbox(subject_id: str) -> str:
    with db.connect() as c:
        row = c.execute("SELECT sandboxes FROM subjects WHERE id=?",
                        (subject_id,)).fetchone()
    boxes = json.loads(row["sandboxes"] or "[]") if row else []
    return boxes[0] if boxes else "python"


def _board_planned() -> bool:
    with db.connect() as c:
        row = c.execute("SELECT COUNT(*) AS n FROM board WHERE type IN ('plan','project')").fetchone()
        return (row["n"] or 0) > 0


def _gather_materials(subject: dict, prof_name: str, sandboxes: list[str],
                      modules: list[dict]) -> int:
    """Professor research — collect as much as the sources will give.

    Per subject: open TEXTBOOKS (Wikibooks, full text scraped), the full topic
    article, books, papers, course pages. Then per module: its own article +
    tutorials, so every class has source material to teach from. All fetched
    in parallel; failures just mean fewer entries.
    """
    topic = subject["title"]
    mod_titles = [m["title"] for m in modules][:6]

    jobs: list[tuple[str, object]] = [
        ("textbook", lambda: research.wikibooks(topic, n=2)),
        ("textbook", lambda: research.wikipedia_full(topic)),
        ("book", lambda: research.openlibrary_books(topic, n=4)),
        ("paper", lambda: research.arxiv_papers(topic, n=4)),
        ("article", lambda: _wiki_list(topic)),
        ("link", lambda: research.search_web(
            f"{topic} university course lecture notes tutorial", n=4)),
    ]
    for mt in mod_titles:
        jobs.append(("article", lambda mt=mt: _wiki_list(f"{mt}")))
        jobs.append(("link", lambda mt=mt: _module_links_with_content(mt, topic)))
        jobs.append(("paper", lambda mt=mt: research.arxiv_papers(mt, n=1)))

    results: list[tuple[str, dict]] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = [(kind, ex.submit(fn)) for kind, fn in jobs]
        for kind, fut in futures:
            try:
                for item in (fut.result() or []):
                    results.append((kind, item))
            except Exception:  # noqa: BLE001 - research is best-effort
                continue

    count = 0
    for kind, item in results:
        tools = (["web-search"] if kind == "paper"
                 else sandboxes[:1] if kind == "link" else [])
        db.add_material(subject["id"], topic, kind, item["title"],
                        item.get("authors", "Wikipedia" if kind == "article" else "web"),
                        item.get("url", ""), item.get("summary", ""),
                        tools=tools, added_by=prof_name,
                        content=item.get("content", ""))
        count += 1
    return count


def _wiki_list(topic: str) -> list[dict]:
    w = research.wikipedia_summary(topic)
    return [w] if w else []


def _module_links_with_content(module_title: str, topic: str) -> list[dict]:
    """Per-subtopic content: find tutorials AND read the top page, so the
    professor has real text to teach the module from."""
    hits = research.search_web(f"{module_title} {topic} tutorial explained", n=2)
    if hits:
        hits[0] = dict(hits[0])
        hits[0]["summary"] = research.fetch_page_text(hits[0]["url"], cap=600)
    return hits


def _prepare_exam(module_id: str) -> None:
    provider = metered(build_provider(store.get_connector()), "examiner",
                       "design exam (build)")

    def factory(subject: str, module: str) -> list[dict]:
        return examiner.generate_exam(provider, subject=subject, module=module,
                                      topics=db.module_topics(module_id))

    try:
        db.get_or_create_exam(module_id, factory)
    except Exception as e:  # noqa: BLE001
        log.warning("build: exam for module %s failed: %s", module_id, e)


def _plan_kanban(subjects: list[dict], mods_by_subject: dict) -> None:
    """The Head breaks the WHOLE learning path into the board: a hands-on
    card per current module, and a planned card for every later module —
    so the board mirrors the curriculum, not a sample of it.

    The Principal (LLM) writes the plan; a deterministic fallback guarantees
    full coverage either way. Lesson cards land automatically when authored.
    """
    with db.connect() as c:
        row = c.execute("SELECT weeks FROM college WHERE id=1").fetchone()
    weeks = (row["weeks"] if row else 12) or 12

    payload = [{
        "title": s["title"],
        "sandboxes": json.loads(s["sandboxes"] or "[]") or ["python"],
        "modules": [m["title"] for m in mods_by_subject.get(s["id"], [])],
    } for s in subjects]

    provider = metered(build_provider(store.get_connector()), "principal", "plan board")
    cards = principal.plan_board(provider, subjects=payload, weeks=weeks)
    if not cards:
        cards = _fallback_plan(payload, weeks)

    now = time.time()
    with db.connect() as c:
        for i, card in enumerate(cards):
            c.execute(
                "INSERT INTO board(col,type,title,subject,meta,tool,created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (card["col"], card["type"], card["title"], card["subject"],
                 card["meta"], int(card["tool"]), now - i * 0.001))


def _fallback_plan(payload: list[dict], weeks: int) -> list[dict]:
    """Deterministic full-path plan: every module is represented."""
    cards = []
    for s in payload:
        mods = s["modules"]
        if not mods:
            continue
        env = s["sandboxes"][0]
        cards.append({"col": "doing", "type": "project",
                      "title": f"Practice: {mods[0]}", "subject": s["title"],
                      "meta": f"{env} sandbox", "tool": True})
        for i, mt in enumerate(mods[1:], start=2):
            wk = max(1, min(weeks, round(i * weeks / max(1, len(mods)))))
            cards.append({"col": "lessons", "type": "plan",
                          "title": f"Module {i}: {mt}", "subject": s["title"],
                          "meta": f"planned · Wk {wk}", "tool": False})
    return cards
