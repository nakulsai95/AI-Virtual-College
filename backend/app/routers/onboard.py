"""Onboarding — the Principal designs a real curriculum and it's persisted."""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from .. import builder, db, research, store
from ..agents import principal
from ..agents.principal import SANDBOXES
from ..llm import build_provider, metered
from ..llm.providers.mock_provider import MockProvider
from ..schemas import Curriculum, FacultyMember, OnboardIn, OnboardOut

log = logging.getLogger("aula.onboard")
router = APIRouter(prefix="/api", tags=["onboard"])

# Every college gets the full staff, even if the Principal forgot to hire some.
_REQUIRED_ROLES = [
    ("provost", "Daichi"), ("examiner", "Rei"), ("registrar", "Sora"),
    ("guide", "Yuki"), ("counselor", "Haru"),
]


@router.get("/sandboxes")
def list_sandboxes():
    """Topic/semester sandbox catalogue the Principal mounts per subject."""
    return {"sandboxes": SANDBOXES}


@router.get("/onboard/status")
def onboard_status():
    """Which stage the Principal is in right now (drives the hiring screen)."""
    return {"stage": db.get_config("onboard_status", "idle")}


@router.post("/onboard", response_model=OnboardOut)
def onboard(body: OnboardIn, background: BackgroundTasks):
    if not body.goal.strip():
        raise HTTPException(400, "Tell the Principal what you want to learn.")

    # The Principal first studies how real universities teach this.
    db.set_config("onboard_status", "research")
    digest, sources = research.curriculum_digest(body.goal)

    db.set_config("onboard_status", "design")
    provider = metered(build_provider(store.get_connector()), "principal", "design curriculum")
    connected = provider.id != "mock"
    try:
        curriculum = principal.design_curriculum(provider, body.goal, body.level,
                                                 research=digest)
        using_mock = provider.id == "mock"
    except Exception as e:  # noqa: BLE001
        if connected:
            # A real model is configured — fail loudly, never silently demo.
            log.warning("Principal failed on %s: %s", provider.id, e)
            raise HTTPException(
                502, f"Your connected model ({provider.name} · {provider.model}) "
                     f"failed while designing the curriculum: {e}") from e
        mock = MockProvider()
        curriculum = principal.design_curriculum(mock, body.goal, body.level)
        provider, using_mock = mock, True

    # Quality pass: validate the draft against what universities actually
    # teach, and fill important gaps before anything is persisted.
    validation_note, topics_added = "", 0
    if digest and not using_mock:
        db.set_config("onboard_status", "validate")
        v_provider = metered(build_provider(store.get_connector()), "principal",
                             "validate curriculum")
        curriculum, validation_note, topics_added = principal.validate_curriculum(
            v_provider, curriculum, digest)

    curriculum = _ensure_full_faculty(curriculum, provider.model)

    # Persist the whole college — it now survives restarts.
    db.seed_from_curriculum(curriculum.model_dump(), body.goal, body.level)
    db.check_in()

    if digest and not using_mock:
        db.log_feed(
            next((f.name for f in curriculum.faculty if f.role == "principal"), "Principal"),
            "Validated the plan against university syllabi · "
            + (f"added {topics_added} missing topics" if topics_added else "coverage aligned")
            + (f" — {validation_note}" if validation_note else ""),
            "update")

    # The Principal's research lands in the library as curriculum sources.
    principal_name = next((f.name for f in curriculum.faculty if f.role == "principal"),
                          "Principal")
    for src in sources:
        db.add_material("", "Curriculum research", src["kind"], src["title"],
                        src["authors"], src["url"], src.get("summary", ""),
                        added_by=principal_name)
    if sources:
        db.log_feed(principal_name,
                    f"Researched {len(sources)} curricula & sources before designing the plan",
                    "update")

    # Kick off the real college build: materials, first lessons, exams, kanban.
    db.set_config("onboard_status", "done")
    db.set_build_status("starting", "Faculty is preparing your semester…", 0,
                        len(curriculum.subjects) * 4 + 1)
    background.add_task(builder.build_college)

    return OnboardOut(
        curriculum=curriculum,
        provider=provider.id,
        model=provider.model,
        using_mock=using_mock,
    )


def _ensure_full_faculty(curriculum: Curriculum, model: str) -> Curriculum:
    have = {f.role for f in curriculum.faculty}
    if "principal" not in have:
        curriculum.faculty.insert(0, FacultyMember(
            id="principal", role="principal", name="Iroha", model=model))
    for role, default_name in _REQUIRED_ROLES:
        if role not in have:
            curriculum.faculty.append(
                FacultyMember(id=role, role=role, name=default_name, model=model))
    return curriculum
