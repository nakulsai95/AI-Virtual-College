"""The live college: full UI state, Guide routing, channels, exams, budget.

GET /api/state is the single snapshot the frontend hydrates from — every
screen's data, in the exact shapes the React components read. Reading it also
runs the Registrar's daily check-in (attendance/streak) and, on a new day,
the Counselor's nudge.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from .. import db, store
from ..agents import counselor, examiner, guide, professor, provost
from ..llm import build_provider, metered
from ..schemas import (
    BudgetIn,
    ChannelMessageIn,
    ExamGenerateIn,
    ExamSubmitIn,
    GuideIn,
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
    try:
        lesson = professor.design_lesson(
            p_provider, subject=subject["title"], topic=route["topic"],
            professor=prof_name, methodology=methodology, sandbox=sandbox)
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
        "professor": f"You teach {fac['subject']}.",
        "guide": "You are the learner's personal guide — route doubts, encourage.",
        "principal": "You run the college and report to the learner.",
    }.get(fac["role"], f"You are the college's {fac['role']}.")
    system = (
        f"You are {fac['name']}, the {fac['role']} at AULA, an AI-run college. "
        f"{role_line} You are chatting with your learner. "
        "Reply in 2-4 warm, concrete sentences. No markdown, no lists.")
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
        return examiner.generate_exam(provider, subject=subject, module=module)

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


# --- credits / budget ------------------------------------------------------------

@router.get("/usage")
def usage():
    return db.usage_summary()


@router.put("/budget")
def set_budget(body: BudgetIn):
    db.set_budget_cap(body.cap)
    return db.usage_summary()


# --- lifecycle --------------------------------------------------------------------

@router.post("/reset")
def reset():
    """Wipe the college so the learner can re-onboard with a new goal."""
    db.reset_college()
    return {"ok": True}
