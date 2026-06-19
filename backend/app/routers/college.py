"""The live college: full UI state, Guide routing, channels, exams, budget.

GET /api/state is the single snapshot the frontend hydrates from — every
screen's data, in the exact shapes the React components read. Reading it also
runs the Registrar's daily check-in (attendance/streak) and, on a new day,
the Counselor's nudge.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from .. import builder, db, store
from ..agents import counselor, examiner, guide, lab, professor, provost
from ..llm import build_provider, metered
from ..schemas import (
    BudgetIn,
    ChannelMessageIn,
    ExamGenerateIn,
    ExamSubmitIn,
    GuideIn,
    LabCompleteIn,
    LabGenerateIn,
    ProfileIn,
    ReviewIn,
)

log = logging.getLogger("aula.college")
router = APIRouter(prefix="/api", tags=["college"])

EXAM_PASS_REWARD = 8
EXAM_FAIL_REWARD = -10
PROVOST_TRIGGER = 75


# --- the snapshot -----------------------------------------------------------

@router.get("/state")
def state():
    if db.enrolled() and db.check_in():
        _daily_nudge()
    return db.ui_state()


def _daily_nudge():
    """New day → the Counselor looks at the weakest concept and nudges."""
    try:
        weakest = _weakest_concept()
        student = _student()
        provider = metered(build_provider(store.get_connector()), "counselor", "daily nudge")
        text = counselor.nudge(provider, streak=student.get("streak", 1),
                               weakest_concept=weakest)
        db.log_feed(db.get_faculty(role="counselor")["name"] if db.get_faculty(role="counselor") else "Counselor",
                    f"Nudge sent · “{text}”", "neutral")
    except Exception:  # noqa: BLE001 - a nudge is never worth a 500
        log.exception("counselor nudge failed")


def _weakest_concept() -> str:
    with db.connect() as c:
        row = c.execute(
            "SELECT ma.concept FROM mastery ma JOIN modules m ON m.id = ma.module_id "
            "WHERE m.status != 'locked' ORDER BY ma.level LIMIT 1").fetchone()
        return row["concept"] if row else ""


def _student() -> dict:
    with db.connect() as c:
        row = c.execute("SELECT * FROM student WHERE id=1").fetchone()
        return dict(row) if row else {}


# --- lessons / library -------------------------------------------------------

@router.get("/lessons/{lesson_id}")
def lesson_detail(lesson_id: int):
    lesson = db.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(404, "No such lesson.")
    return {"lesson": lesson}


@router.post("/catalog/{catalog_id}/generate")
def generate_class(catalog_id: int):
    """JIT: write this catalog class right now (bulk tier), return the lesson."""
    entry = db.get_catalog_entry(catalog_id)
    if not entry:
        raise HTTPException(404, "No such class in the catalog.")
    if entry["status"] == "ready" and entry["lesson_id"]:
        return {"lesson": db.get_lesson(entry["lesson_id"])}

    prof = db.resolve_professor(subject=entry["subject_title"])
    prof_name = prof["name"] if prof else "Professor"
    db.set_catalog_status(catalog_id, "writing")
    try:
        lesson_id = builder._author_class(  # noqa: SLF001 - same package, same flow
            entry, prof, prof_name, builder._subject_sandbox(entry["subject_id"]))
    except Exception as e:  # noqa: BLE001
        db.set_catalog_status(catalog_id, "planned")
        provider = build_provider(store.get_connector())
        if provider.id != "mock":
            raise HTTPException(
                502, f"Your connected model failed while writing this class: {e}") from e
        raise HTTPException(500, f"Could not write the class: {e}") from e
    return {"lesson": db.get_lesson(lesson_id)}


@router.post("/build/continue")
def build_continue(background: BackgroundTasks):
    """Resume the college build / content factory (idempotent)."""
    if not db.enrolled():
        raise HTTPException(400, "No college yet — onboard first.")
    background.add_task(builder.build_college)
    ready, total = db.catalog_counts()
    return {"ok": True, "ready": ready, "total": total}


# --- the Personal Guide ------------------------------------------------------

@router.post("/guide")
def ask_guide(body: GuideIn):
    if not body.message.strip():
        raise HTTPException(400, "Ask me anything.")
    ui = db.ui_state()
    if not ui.get("enrolled"):
        raise HTTPException(400, "Enrol first — the Principal needs to design your curriculum.")
    subjects = ui["SUBJECTS"]

    g_provider = metered(build_provider(store.get_connector()), "guide", "route question")
    route = guide.route(g_provider, question=body.message, subjects=subjects)
    subject = next((s for s in subjects if s["id"] == route["subject"]), subjects[0])

    prof = db.resolve_professor(professor_id=subject.get("prof", ""),
                                subject=subject["title"])
    prof_name = subject.get("profName") or (prof["name"] if prof else "Professor")
    sandbox = (subject.get("sandboxes") or ["python"])[0]
    methodology = (prof or {}).get("methodology") or dict(db.DEFAULT_METHODOLOGY)

    p_provider = metered(build_provider(store.get_connector()),
                         (prof or {}).get("id", "professor"), "author lesson")
    # The professor teaches from the materials they gathered for this subject.
    context, refs = db.materials_context(subject["id"], route["topic"])
    try:
        lesson = professor.design_lesson(
            p_provider, subject=subject["title"], topic=route["topic"],
            professor=prof_name, methodology=methodology, sandbox=sandbox,
            materials=context, refine=True)
    except Exception as e:  # noqa: BLE001
        if p_provider.id != "mock":
            # A real model is configured — fail loudly, never silently demo.
            raise HTTPException(
                502, f"Your connected model ({p_provider.name} · {p_provider.model}) "
                     f"failed while writing the lesson: {e}") from e
        from ..llm.providers.mock_provider import MockProvider
        lesson = professor.design_lesson(
            MockProvider(), subject=subject["title"], topic=route["topic"],
            professor=prof_name, methodology=methodology, sandbox=sandbox)
    lesson["refs"] = refs
    lesson["id"] = db.add_lesson(lesson)

    # The conversation also lands in the Guide's DM channel.
    guide_fac = db.get_faculty(role="guide")
    if guide_fac:
        ch_id = f"dm-{guide_fac['id']}"
        if db.get_channel(ch_id):
            student = _student()
            db.add_message(ch_id, student.get("name", "You"), "me", "", body.message)
            db.add_message(ch_id, guide_fac["name"], "guide", guide_fac["hue"], route["reply"])
            db.mark_channel_read(ch_id)

    db.check_in()
    return {
        "reply": route["reply"],
        "route": {"subject": subject["title"], "professor": prof_name},
        "lesson": lesson,
        "provider": g_provider.id,
        "using_mock": g_provider.id == "mock",
    }


# --- channels ----------------------------------------------------------------

@router.post("/channel/{channel_id}/messages")
def send_message(channel_id: str, body: ChannelMessageIn):
    if not body.text.strip():
        raise HTTPException(400, "Say something.")
    ch = db.get_channel(channel_id)
    if not ch:
        raise HTTPException(404, "No such channel.")

    student = _student()
    sent = db.add_message(channel_id, student.get("name", "You"), "me", "", body.text)

    # Who answers? DMs -> the channel's owner; the faculty room -> the principal.
    responder = None
    if channel_id.startswith("dm-"):
        responder = db.get_faculty(fid=channel_id[3:])
    if responder is None:
        responder = db.get_faculty(role="principal")
    if responder is None:
        return {"messages": [sent]}

    reply_text = _persona_reply(responder, body.text, channel_id)
    reply = db.add_message(channel_id, responder["name"], responder["role"],
                           responder["hue"], reply_text)
    db.mark_channel_read(channel_id)
    db.check_in()
    return {"messages": [sent, reply]}


def _persona_reply(fac: dict, text: str, channel_id: str) -> str:
    provider = metered(build_provider(store.get_connector()), fac["id"], "channel reply")
    if provider.id == "mock":
        return _template_reply(fac)
    role_line = {
        "professor": (f"You teach {fac['subject']} and you are personally graded on "
                      "whether this learner succeeds. Answer their question concretely; "
                      "if it deserves a full lesson, say you'll write one if they ask "
                      "the Guide."),
        "guide": "You are the learner's personal guide — route doubts to the right teacher, encourage, never lecture.",
        "principal": "You run the college; you report progress plainly and own problems without excuses.",
        "examiner": "You set and grade exams blind; you can explain how grading works, never leak questions.",
        "counselor": "You look after pacing and wellbeing; you never judge.",
        "registrar": "You keep attendance, streaks and records.",
    }.get(fac["role"], f"You are the college's {fac['role']}.")
    system = (
        f"You are {fac['name']}, the {fac['role']} at AULA, an AI-run college, "
        f"chatting with your learner in a DM. {role_line} "
        "Stay in character and remember the relationship: their success is your job. "
        "Reply in 2-4 warm, concrete sentences — specifics over platitudes. "
        "No markdown, no lists, no sign-offs.")
    history = _recent_messages(channel_id, limit=8)
    try:
        return provider.complete(system, history + [{"role": "user", "content": text}],
                                 max_tokens=400).strip() or _template_reply(fac)
    except Exception:  # noqa: BLE001 - chat must never 500
        return _template_reply(fac)


def _template_reply(fac: dict) -> str:
    if fac["role"] == "professor":
        return (f"Good question — let's dig into it. Ask the Guide to have me write a full "
                f"lesson on it, or try the sandbox and show me what you get.")
    if fac["role"] == "guide":
        return "On it — ask me in the Personal Guide tab and I'll bring the right teacher in."
    return "Noted — I'll keep the faculty on it. Anything else you need, just say."


def _recent_messages(channel_id: str, limit: int = 8) -> list[dict]:
    with db.connect() as c:
        rows = c.execute("SELECT who, role, text FROM messages WHERE channel_id=? "
                         "ORDER BY id DESC LIMIT ?", (channel_id, limit)).fetchall()
    out = []
    for r in reversed(rows):
        out.append({"role": "user" if r["role"] == "me" else "assistant", "content": r["text"]})
    # The API requires the list to start with a user turn.
    while out and out[0]["role"] == "assistant":
        out.pop(0)
    return out


@router.post("/channel/{channel_id}/read")
def read_channel(channel_id: str):
    db.mark_channel_read(channel_id)
    return {"ok": True}


# --- exams ---------------------------------------------------------------------

@router.post("/exams/generate")
def generate_exam(body: ExamGenerateIn):
    provider = metered(build_provider(store.get_connector()), "examiner", "design exam")

    def factory(subject: str, module: str) -> list[dict]:
        return examiner.generate_exam(provider, subject=subject, module=module,
                                      topics=db.module_topics(body.module_id))

    exam = db.get_or_create_exam(body.module_id, factory)
    if not exam:
        raise HTTPException(404, "No such module.")
    return {"exam": exam, "provider": provider.id, "using_mock": provider.id == "mock"}


@router.post("/exams/{exam_id}/submit")
def submit_exam(exam_id: int, body: ExamSubmitIn):
    exam = db.get_exam(exam_id)
    if not exam:
        raise HTTPException(404, "No such exam.")
    if exam["status"] != "upcoming":
        raise HTTPException(400, "This exam was already taken — re-enrol the unit to retake it.")

    provider = metered(build_provider(store.get_connector()), "examiner", "grade exam")
    result = examiner.grade_exam(provider, questions=exam["questions"],
                                 answers=body.answers, bar=exam["bar"])
    db.finish_exam(exam_id, result["score"], result["passed"], result["feedback"])

    examiner_name = (db.get_faculty(role="examiner") or {}).get("name", "Examiner")
    db.log_feed(examiner_name,
                f"{'Exam passed' if result['passed'] else 'Exam failed'} · "
                f"“{exam['title']}” · {result['score']}% (bar {exam['bar']})",
                "pos" if result["passed"] else "neg")

    # Reward loop → professor of the exam's subject.
    reward = None
    methodology_changed = False
    prof = db.resolve_professor(subject=exam["subject"])
    if prof:
        delta = EXAM_PASS_REWARD if result["passed"] else EXAM_FAIL_REWARD
        snap = db.reward_professor(
            prof["id"], delta,
            f"Exam {'passed' if result['passed'] else 'failed'} · “{exam['title']}”")
        if not result["passed"] and snap and snap["score"] < PROVOST_TRIGGER:
            p_provider = metered(build_provider(store.get_connector()), "provost",
                                 "rewrite methodology")
            context = (f"The learner failed the “{exam['title']}” exam at "
                       f"{result['score']}% (bar {exam['bar']}). "
                       f"Weakest answer feedback: {result['feedback'][:200]}")
            methodology, note = provost.rewrite(p_provider, professor=snap, context=context)
            snap = db.set_methodology(snap["id"], methodology, note) or snap
            methodology_changed = True
        reward = {"delta": delta, "professor": snap,
                  "methodology_changed": methodology_changed}

    # Learner's side: XP, mastery, board.
    db.award_xp(db.XP["exam_pass"] if result["passed"] else db.XP["exam_fail"])
    subject_id = _subject_id_for(exam["subject"])
    if subject_id:
        if result["passed"]:
            db.bump_mastery(subject_id, module_id=exam["module_id"], amount=0.3, floor=0.85)
        else:
            db.bump_mastery(subject_id, module_id=exam["module_id"], amount=0.1)
    db.add_board_card("graded", "task", f"{exam['type']}: {exam['title']}", exam["subject"],
                      f"{result['score']}% · {'passed' if result['passed'] else 'retry'}",
                      good=result["passed"])
    db.check_in()

    return {
        "score": result["score"], "passed": result["passed"],
        "feedback": result["feedback"], "per_question": result["per_question"],
        "reward": reward, "methodology_changed": methodology_changed,
        "provider": provider.id, "using_mock": provider.id == "mock",
    }


def _subject_id_for(subject_title: str) -> str:
    with db.connect() as c:
        row = c.execute("SELECT id FROM subjects WHERE title=?", (subject_title,)).fetchone()
        return row["id"] if row else ""


# --- labs / games ----------------------------------------------------------------

@router.post("/lab/generate")
def lab_generate(body: LabGenerateIn):
    """Design (or return the cached) interactive lab for a class — JIT, bulk tier."""
    subject_id = _subject_id_for(body.subject)
    cached = db.get_lab(subject_id, body.topic)
    if cached:
        return {"lab": cached, "cached": True}

    sandbox = builder._subject_sandbox(subject_id) if subject_id else "python"
    context, _ = db.materials_context(subject_id, body.topic) if subject_id else ("", [])
    provider = metered(build_provider(store.get_connector()), "professor",
                       "design lab", tier="bulk")
    spec = lab.design_lab(provider, subject=body.subject, topic=body.topic,
                          materials=context, sandbox=sandbox)
    spec["id"] = db.save_lab(subject_id, body.topic, spec)
    return {"lab": spec, "cached": False, "using_mock": provider.id == "mock"}


@router.post("/game/generate")
def game_generate(body: LabGenerateIn):
    """Author (or return the cached) PLAYABLE game for a class — a chapter in the
    continuing adventure. Falls back to a structured lab if no runnable game."""
    subject_id = _subject_id_for(body.subject)
    cache_key = body.topic + " ::game"
    cached = db.get_lab(subject_id, cache_key)
    if cached:
        return {"lab": cached, "cached": True}

    context, _ = db.materials_context(subject_id, body.topic) if subject_id else ("", [])
    sandbox = builder._subject_sandbox(subject_id) if subject_id else "python"
    provider = metered(build_provider(store.get_connector()), "professor",
                       "design game", tier="bulk")
    spec = lab.design_arcade(provider, subject=body.subject, topic=body.topic,
                             materials=context,
                             next_topic=db.next_topic_after(subject_id, body.topic),
                             story=db.story_recap())
    if not spec:  # no runnable game — fall back to a structured learning lab
        spec = lab.design_lab(provider, subject=body.subject, topic=body.topic,
                              materials=context, sandbox=sandbox)
    spec["id"] = db.save_lab(subject_id, cache_key, spec)
    return {"lab": spec, "cached": False, "using_mock": provider.id == "mock"}


@router.post("/lab/complete")
def lab_complete(body: LabCompleteIn):
    """Finishing a lab/game rewards the learner (XP + mastery) and advances the
    story so the next chapter can build on it."""
    score = max(0, min(100, body.score))
    db.award_xp(20 + score // 5)
    subject_id = _subject_id_for(body.subject)
    if subject_id:
        db.bump_mastery(subject_id, amount=0.05 + score / 1000)
    if body.topic and score >= 50:
        db.advance_story(body.topic)
    prof = db.resolve_professor(subject=body.subject)
    db.log_feed(prof["name"] if prof else "Lab",
                f"Cleared “{body.topic or body.subject or 'practice'}” · {score}%",
                "pos" if score >= 60 else "neutral")
    db.check_in()
    return {"ok": True, "score": score}


# --- spaced repetition -------------------------------------------------------------

@router.get("/review")
def review_due():
    return {"cards": db.due_flashcards(limit=30), "counts": dict(
        zip(("due", "total"), db.flashcard_counts()))}


@router.post("/review")
def review_grade(body: ReviewIn):
    if body.grade not in ("again", "good", "easy"):
        raise HTTPException(400, "grade must be again | good | easy")
    ok = db.review_flashcard(body.card_id, body.grade)
    if not ok:
        raise HTTPException(404, "No such card.")
    if body.grade != "again":
        db.award_xp(2)
    return {"ok": True, "counts": dict(zip(("due", "total"), db.flashcard_counts()))}


# --- credits / budget ------------------------------------------------------------

@router.get("/usage")
def usage():
    return db.usage_summary()


@router.put("/budget")
def set_budget(body: BudgetIn, background: BackgroundTasks):
    old_cap = db.budget_cap()
    db.set_budget_cap(body.cap)
    # More credits → the content factory picks up where it paused.
    if body.cap > old_cap and db.enrolled():
        ready, total = db.catalog_counts()
        if total and ready < total:
            background.add_task(builder.build_college)
    return db.usage_summary()


# --- account --------------------------------------------------------------------

@router.get("/profile")
def get_profile():
    return {"account": db.get_account()}


@router.put("/profile")
def set_profile(body: ProfileIn):
    if not body.email.strip():
        raise HTTPException(400, "An email is required.")
    db.set_account(body.name or body.email.split("@")[0], body.email)
    return {"account": db.get_account()}


# --- lifecycle --------------------------------------------------------------------

@router.post("/reset")
def reset():
    """Wipe the college so the learner can re-onboard with a new goal."""
    db.reset_college()
    return {"ok": True}
