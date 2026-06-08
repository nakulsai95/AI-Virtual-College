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
