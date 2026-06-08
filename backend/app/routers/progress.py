"""The learner's own progress diagnostic (per-concept mastery, XP, streak)."""
from __future__ import annotations

from fastapi import APIRouter

from .. import repo
from ..auth import CurrentUser

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/progress")
def get_progress(user=CurrentUser):
    student = repo.get_student(user["id"])
    return {"student": student, "has_progress": student is not None}
