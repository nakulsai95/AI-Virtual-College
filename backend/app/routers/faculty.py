"""Professor lessons, Examiner grading + reward loop, live faculty state."""
from __future__ import annotations

import logging

from fastapi import APIRouter

from .. import progress, repo
from ..agents import examiner, professor
from ..auth import CurrentUser
from ..llm import build_provider
from ..llm.providers.mock_provider import MockProvider
from ..schemas import GradeIn, GradeOut, LessonIn, LessonOut
from ..state import DEFAULT_METHODOLOGY, CollegeState

log = logging.getLogger("aula.faculty")
router = APIRouter(prefix="/api", tags=["faculty"])

PASS_REWARD = 5
FAIL_REWARD = -10


@router.post("/lesson", response_model=LessonOut)
def author_lesson(body: LessonIn, user=CurrentUser):
    uid = user["id"]
    provider = build_provider(repo.get_connector(uid))
    state = CollegeState.load(uid)
    prof = state.resolve_professor(subject=body.subject, name=body.professor)
    methodology = prof["methodology"] if prof else DEFAULT_METHODOLOGY
    name = body.professor or (prof["name"] if prof else "Professor")

    try:
        lesson = professor.design_lesson(provider, subject=body.subject, topic=body.topic,
                                         professor=name, methodology=methodology, sandbox=body.sandbox)
        using_mock = provider.id == "mock"
    except Exception as e:  # noqa: BLE001
        log.warning("Professor failed (%s); using demo lesson", e)
        mock = MockProvider()
        lesson = professor.design_lesson(mock, subject=body.subject, topic=body.topic,
                                         professor=name, methodology=methodology, sandbox=body.sandbox)
        provider, using_mock = mock, True

    state.log_lesson(name, lesson["title"])
    state.save(uid)
    repo.add_library_lesson(uid, body.subject, lesson["title"], lesson)  # to the library KB

    # The learner read/received a lesson — nudge their own progress.
    student = repo.get_student(uid)
    if student:
        repo.set_student(uid, progress.on_lesson(student, body.subject, body.topic))

    return LessonOut(lesson=lesson, provider=provider.id, model=provider.model, using_mock=using_mock)


@router.post("/grade", response_model=GradeOut)
def grade_answer(body: GradeIn, user=CurrentUser):
    uid = user["id"]
    provider = build_provider(repo.get_connector(uid))
    result = examiner.grade(provider, question=body.question, answer=body.answer, bar=body.bar)
    using_mock = provider.id == "mock"

    reward = None
    state = CollegeState.load(uid)
    prof = state.resolve_professor(professor_id=body.professor_id, subject=body.subject, name=body.professor)
    if prof:
        delta = PASS_REWARD if result["passed"] else FAIL_REWARD
        reason = (("Probe" if body.kind == "probe" else "Exam") +
                  (" passed" if result["passed"] else " failed"))
        snap = state.reward(prof, delta, reason)
        methodology_changed = False
        if not result["passed"] and prof["score"] < 75:
            snap = state.rewrite_methodology(prof)
            methodology_changed = True
        reward = {"delta": delta, "professor": snap, "methodology_changed": methodology_changed}
        state.save(uid)

    # Update the learner's own diagnostic (never punitive).
    student = repo.get_student(uid)
    if student:
        repo.set_student(uid, progress.on_grade(
            student, body.subject, result["passed"], result["score"], topic=body.question))

    return GradeOut(score=result["score"], passed=result["passed"], feedback=result["feedback"],
                    reward=reward, provider=provider.id, using_mock=using_mock)


@router.get("/faculty")
def faculty_state(user=CurrentUser):
    return CollegeState.load(user["id"]).snapshot()
