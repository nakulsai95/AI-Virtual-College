"""Professor lessons, Examiner grading + reward loop, and live faculty state."""
from __future__ import annotations

import logging

from fastapi import APIRouter

from .. import store
from ..agents import examiner, professor
from ..llm import build_provider
from ..llm.providers.mock_provider import MockProvider
from ..schemas import GradeIn, GradeOut, LessonIn, LessonOut
from ..state import STATE

log = logging.getLogger("aula.faculty")
router = APIRouter(prefix="/api", tags=["faculty"])

# Reward magnitudes for the loop.
PASS_REWARD = 5
FAIL_REWARD = -10


@router.post("/lesson", response_model=LessonOut)
def author_lesson(body: LessonIn):
    provider = build_provider(store.get_connector())
    prof = STATE.resolve_professor(subject=body.subject, name=body.professor)
    methodology = prof["methodology"] if prof else None
    name = body.professor or (prof["name"] if prof else "Professor")

    from ..state import DEFAULT_METHODOLOGY
    try:
        lesson = professor.design_lesson(
            provider, subject=body.subject, topic=body.topic, professor=name,
            methodology=methodology or DEFAULT_METHODOLOGY, sandbox=body.sandbox,
        )
        using_mock = provider.id == "mock"
    except Exception as e:  # noqa: BLE001
        log.warning("Professor failed (%s); using demo lesson", e)
        mock = MockProvider()
        lesson = professor.design_lesson(
            mock, subject=body.subject, topic=body.topic, professor=name,
            methodology=methodology or DEFAULT_METHODOLOGY, sandbox=body.sandbox,
        )
        provider, using_mock = mock, True

    STATE.log_lesson(name, lesson["title"])
    return LessonOut(lesson=lesson, provider=provider.id, model=provider.model, using_mock=using_mock)


@router.post("/grade", response_model=GradeOut)
def grade_answer(body: GradeIn):
    provider = build_provider(store.get_connector())
    result = examiner.grade(provider, question=body.question, answer=body.answer, bar=body.bar)
    using_mock = provider.id == "mock"

    # Apply the reward to the responsible professor (never to the learner).
    reward = None
    prof = STATE.resolve_professor(
        professor_id=body.professor_id, subject=body.subject, name=body.professor)
    if prof:
        delta = PASS_REWARD if result["passed"] else FAIL_REWARD
        reason = ("Probe passed" if body.kind == "probe" else "Exam passed") if result["passed"] \
            else ("Probe failed" if body.kind == "probe" else "Exam failed")
        snap = STATE.reward(prof, delta, reason, kind="probe")
        methodology_changed = False
        # A failure that drags the professor down triggers a Provost rewrite.
        if not result["passed"] and prof["score"] < 75:
            snap = STATE.rewrite_methodology(prof)
            methodology_changed = True
        reward = {"delta": delta, "professor": snap, "methodology_changed": methodology_changed}

    return GradeOut(
        score=result["score"], passed=result["passed"], feedback=result["feedback"],
        reward=reward, provider=provider.id, using_mock=using_mock,
    )


@router.get("/faculty")
def faculty_state():
    """Live faculty grades + the reward feed (drives Command Center / Grades)."""
    return STATE.snapshot()
