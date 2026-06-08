"""Exams — the Examiner sets a multi-question exam, grades it, and the result
feeds the reward loop (professor) and the student model (learner)."""
from __future__ import annotations

import time

from fastapi import APIRouter

from .. import progress, repo
from ..agents import examiner
from ..auth import CurrentUser
from ..llm import build_provider
from ..schemas import (
    ExamPerQ,
    ExamResultOut,
    ExamStartIn,
    ExamStartOut,
    ExamSubmitIn,
)
from ..state import CollegeState

router = APIRouter(prefix="/api/exam", tags=["exams"])

PASS_REWARD = 8
FAIL_REWARD = -12


def _subject_meta(uid: int, subject: str) -> tuple[list[str], str]:
    """Concepts (module titles) + professor name for a subject, from enrollment."""
    enr = repo.get_enrollment(uid) or {}
    for s in enr.get("subjects", []):
        if s.get("title", "").lower() == subject.lower():
            return [m["title"] for m in s.get("modules", [])], s.get("professor", "")
    return [subject], ""


@router.post("/start", response_model=ExamStartOut)
def start_exam(body: ExamStartIn, user=CurrentUser):
    uid = user["id"]
    provider = build_provider(repo.get_connector(uid))
    concepts, prof = _subject_meta(uid, body.subject)
    questions = examiner.build_exam(provider, subject=body.subject, concepts=concepts, n=3)
    return ExamStartOut(
        subject=body.subject, professor=prof, bar=body.bar,
        questions=questions, provider=provider.id, using_mock=provider.id == "mock",
    )


@router.post("/submit", response_model=ExamResultOut)
def submit_exam(body: ExamSubmitIn, user=CurrentUser):
    uid = user["id"]
    provider = build_provider(repo.get_connector(uid))

    per_q: list[ExamPerQ] = []
    for a in body.answers:
        r = examiner.grade(provider, question=a.question, answer=a.answer, bar=body.bar)
        per_q.append(ExamPerQ(id=a.id, score=r["score"], passed=r["passed"], feedback=r["feedback"]))

    overall = round(sum(p.score for p in per_q) / len(per_q)) if per_q else 0
    passed = overall >= body.bar

    # Reward the professor (never the learner) — same loop as probes.
    reward = None
    state = CollegeState.load(uid)
    prof = state.resolve_professor(subject=body.subject, name=body.professor)
    if prof:
        delta = PASS_REWARD if passed else FAIL_REWARD
        snap = state.reward(prof, delta, "Exam passed" if passed else "Exam failed")
        methodology_changed = False
        if not passed and prof["score"] < 75:
            snap = state.rewrite_methodology(prof)
            methodology_changed = True
        reward = {"delta": delta, "professor": snap, "methodology_changed": methodology_changed}
        state.save(uid)

    # Learner progress (non-punitive) + persist the result.
    student = repo.get_student(uid)
    if student:
        repo.set_student(uid, progress.on_grade(student, body.subject, passed, overall))

    store = repo.get_exams(uid)
    store["results"].insert(0, {
        "id": f"e{int(time.time())}", "subject": body.subject, "professor": body.professor,
        "overall": overall, "bar": body.bar, "passed": passed,
        "when": time.strftime("%Y-%m-%d %H:%M"),
    })
    store["results"] = store["results"][:50]
    repo.set_exams(uid, store)

    return ExamResultOut(
        overall=overall, passed=passed, bar=body.bar, per_question=per_q,
        reward=reward, provider=provider.id, using_mock=provider.id == "mock",
    )


@router.get("/results")
def exam_results(user=CurrentUser):
    return repo.get_exams(user["id"])
