"""Onboarding — the Principal designs a real curriculum and it's persisted."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from .. import db, store
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


@router.post("/onboard", response_model=OnboardOut)
def onboard(body: OnboardIn):
    if not body.goal.strip():
        raise HTTPException(400, "Tell the Principal what you want to learn.")

    provider = metered(build_provider(store.get_connector()), "principal", "design curriculum")
    connected = provider.id != "mock"
    try:
        curriculum = principal.design_curriculum(provider, body.goal, body.level)
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

    curriculum = _ensure_full_faculty(curriculum, provider.model)

    # Persist the whole college — it now survives restarts.
    db.seed_from_curriculum(curriculum.model_dump(), body.goal, body.level)
    db.check_in()

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
