"""Pydantic models for API requests/responses and the curriculum the
Principal agent produces."""
from __future__ import annotations

from pydantic import BaseModel, Field

# ---- Connectors --------------------------------------------------------

class ConnectorIn(BaseModel):
    provider: str
    api_key: str = ""
    model: str = ""
    base_url: str = ""


class ConnectorStatus(BaseModel):
    provider: str
    name: str
    model: str
    connected: bool
    has_key: bool
    using_mock: bool


# ---- Curriculum (Principal output) -------------------------------------

class Module(BaseModel):
    id: str
    title: str


class Subject(BaseModel):
    id: str
    title: str
    professor: str
    # Topic/semester-driven sandboxes mounted for this subject.
    sandboxes: list[str] = Field(default_factory=list)
    modules: list[Module] = Field(default_factory=list)


class FacultyMember(BaseModel):
    id: str
    role: str
    name: str
    subject: str | None = None
    model: str = ""


class Curriculum(BaseModel):
    mission: str
    level: str = "intermediate"
    weeks: int = 12
    summary: str = ""
    subjects: list[Subject] = Field(default_factory=list)
    faculty: list[FacultyMember] = Field(default_factory=list)


class OnboardIn(BaseModel):
    goal: str
    level: str = "intermediate"


class OnboardOut(BaseModel):
    curriculum: Curriculum
    provider: str
    model: str
    using_mock: bool


# ---- Professor / lessons ----------------------------------------------

class LessonIn(BaseModel):
    subject: str
    topic: str
    professor: str = ""
    sandbox: str = "python"


class LessonOut(BaseModel):
    lesson: dict
    provider: str
    model: str
    using_mock: bool


# ---- Examiner / reward loop -------------------------------------------

class GradeIn(BaseModel):
    kind: str = "probe"  # "probe" | "exam"
    question: str
    answer: str
    bar: int = 70
    subject: str = ""
    professor_id: str = ""
    professor: str = ""


class GradeOut(BaseModel):
    score: int
    passed: bool
    feedback: str
    reward: dict | None = None  # {delta, professor, methodology_changed}
    provider: str
    using_mock: bool


# ---- Guide / channels / exams / budget ---------------------------------

class GuideIn(BaseModel):
    message: str


class ChannelMessageIn(BaseModel):
    text: str


class ExamGenerateIn(BaseModel):
    module_id: str


class ExamSubmitIn(BaseModel):
    answers: list[str] = Field(default_factory=list)


class BudgetIn(BaseModel):
    cap: float


class LabGenerateIn(BaseModel):
    subject: str
    topic: str
    mode: str = ""  # "" structured lab | "game" playable arcade


class LabCompleteIn(BaseModel):
    subject: str = ""
    score: int = 0
    topic: str = ""


class ReviewIn(BaseModel):
    card_id: int
    grade: str = "good"  # again | good | easy


class ProfileIn(BaseModel):
    name: str = ""
    email: str = ""


# ---- Sandbox ----------------------------------------------------------

class SandboxIn(BaseModel):
    sandbox: str = "python"
    code: str


class SandboxOut(BaseModel):
    ok: bool
    stdout: str
    stderr: str
    duration_ms: int
    sandbox: str
