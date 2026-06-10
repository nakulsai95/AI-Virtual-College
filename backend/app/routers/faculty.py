"""Professor lessons, Examiner grading + reward loop, and live faculty state.

The loop, end to end: the Examiner grades the learner's probe answer → the
reward lands on the professor (never the learner) → a failure that drags the
professor down has the Provost (a real agent) rewrite their methodology →
the learner's mastery, XP, and board update either way.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from .. import db, store
from ..agents import examiner, professor, provost
from ..llm import build_provider, metered
from ..llm.providers.mock_provider import MockProvider
from ..schemas import GradeIn, GradeOut, LessonIn, LessonOut

log = logging.getLogger("aula.faculty")
router = APIRouter(prefix="/api", tags=["faculty"])

# Reward magnitudes for the loop.
PASS_REWARD = 5
FAIL_REWARD = -10
PROVOST_TRIGGER = 75  # a fail below this professor score brings the Provost in


@router.post("/lesson", response_model=LessonOut)
def author_lesson(body: LessonIn):
    prof = db.resolve_professor(subject=body.subject, name=body.professor)
    name = body.professor or (prof["name"] if prof else "Professor")
    agent_id = prof["id"] if prof else "professor"
    methodology = (prof or {}).get("methodology") or dict(db.DEFAULT_METHODOLOGY)

    provider = metered(build_provider(store.get_connector()), agent_id, "author lesson")
    connected = provider.id != "mock"
    # What to teach is extracted from the materials this professor gathered.
    context, refs = db.materials_context(_subject_id(body.subject), body.topic)
    try:
        lesson = professor.design_lesson(
            provider, subject=body.subject, topic=body.topic, professor=name,
            methodology=methodology, sandbox=body.sandbox, materials=context,
        )
        using_mock = provider.id == "mock"
    except Exception as e:  # noqa: BLE001
        if connected:
            # A real model is configured — fail loudly, never silently demo.
            log.warning("Professor failed on %s: %s", provider.id, e)
            raise HTTPException(
                502, f"Your connected model ({provider.name} · {provider.model}) "
                     f"failed while writing the lesson: {e}") from e
        log.warning("Professor failed (%s); using demo lesson", e)
        mock = MockProvider()
        lesson = professor.design_lesson(
            mock, subject=body.subject, topic=body.topic, professor=name,
            methodology=methodology, sandbox=body.sandbox,
        )
        provider, using_mock = mock, True
    lesson["refs"] = refs

    lesson_id = db.add_lesson(lesson, subject_id=(prof or {}).get("subject_id", ""))
    lesson["id"] = lesson_id
    db.check_in()
    return LessonOut(lesson=lesson, provider=provider.id, model=provider.model,
                     using_mock=using_mock)


@router.post("/grade", response_model=GradeOut)
def grade_answer(body: GradeIn):
    provider = metered(build_provider(store.get_connector()), "examiner", "grade probe")
    result = examiner.grade(provider, question=body.question, answer=body.answer, bar=body.bar)
    using_mock = provider.id == "mock"

    # Apply the reward to the responsible professor (never to the learner).
    reward = None
    prof = db.resolve_professor(
        professor_id=body.professor_id, subject=body.subject, name=body.professor)
    if prof:
        delta = PASS_REWARD if result["passed"] else FAIL_REWARD
        what = "Probe" if body.kind == "probe" else "Exam"
        reason = f"{what} passed · {result['score']}%" if result["passed"] \
            else f"{what} failed · {result['score']}%"
        snap = db.reward_professor(prof["id"], delta, reason)
        methodology_changed = False
        if not result["passed"] and snap and snap["score"] < PROVOST_TRIGGER:
            snap, methodology_changed = _provost_rewrite(snap, body, result)
        reward = {"delta": delta, "professor": snap, "methodology_changed": methodology_changed}

    # The learner's own loop: XP + mastery move with every attempt.
    subject_id = _subject_id(body.subject)
    db.award_xp(db.XP["probe_pass"] if result["passed"] else db.XP["probe_fail"])
    if subject_id:
        db.bump_mastery(subject_id, amount=0.15 if result["passed"] else 0.05)
    db.add_board_card(
        "graded", "task", f"Probe: {body.question[:48]}", body.subject,
        f"{result['score']}% · {'passed' if result['passed'] else 'retry'}",
        good=result["passed"])
    db.check_in()

    return GradeOut(
        score=result["score"], passed=result["passed"], feedback=result["feedback"],
        reward=reward, provider=provider.id, using_mock=using_mock,
    )


def _provost_rewrite(snap: dict, body: GradeIn, result: dict) -> tuple[dict, bool]:
    """The Provost reasons about the failure and rewrites the methodology."""
    provider = metered(build_provider(store.get_connector()), "provost", "rewrite methodology")
    context = (f"The learner failed a {body.kind} on “{body.question[:120]}” "
               f"scoring {result['score']}% (bar {body.bar}). "
               f"Examiner's feedback: {result['feedback'][:200]}")
    methodology, note = provost.rewrite(provider, professor=snap, context=context)
    new_snap = db.set_methodology(snap["id"], methodology, note)
    return (new_snap or snap), True


def _subject_id(subject_title: str) -> str:
    with db.connect() as c:
        row = c.execute("SELECT id FROM subjects WHERE title=?", (subject_title,)).fetchone()
        return row["id"] if row else ""


@router.get("/faculty")
def faculty_state():
    """Live faculty grades + the reward feed (drives Command Center / Grades)."""
    state = db.ui_state()
    if not state.get("enrolled"):
        return {"professors": [], "feed": [], "has_curriculum": False}
    return {"professors": state["GRADES"], "feed": state["FEED"], "has_curriculum": True}
