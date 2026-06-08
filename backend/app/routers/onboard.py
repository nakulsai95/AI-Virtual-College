"""Onboarding — the Principal designs a curriculum, persisted per user."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from .. import progress, repo, retrieval
from ..agents import principal
from ..agents.principal import SANDBOXES
from ..auth import CurrentUser
from ..llm import build_provider
from ..llm.providers.mock_provider import MockProvider
from ..schemas import OnboardIn, OnboardOut
from ..state import CollegeState

log = logging.getLogger("aula.onboard")
router = APIRouter(prefix="/api", tags=["onboard"])


@router.get("/sandboxes")
def list_sandboxes():
    return {"sandboxes": SANDBOXES}


@router.get("/enrollment")
def get_enrollment(user=CurrentUser):
    """Lets the frontend skip onboarding and restore a returning student."""
    cur = repo.get_enrollment(user["id"])
    return {"enrolled": cur is not None, "curriculum": cur}


@router.post("/onboard", response_model=OnboardOut)
def onboard(body: OnboardIn, user=CurrentUser):
    if not body.goal.strip():
        raise HTTPException(400, "Tell the Principal what you want to learn.")
    uid = user["id"]

    # Ground the plan in real materials (open sources + arXiv + optional web search).
    materials = retrieval.gather(body.goal, search_config=repo.get_search(uid), n=10)
    if materials:
        repo.add_materials(uid, body.goal, materials)

    provider = build_provider(repo.get_connector(uid))
    try:
        curriculum = principal.design_curriculum(provider, body.goal, body.level, materials)
        using_mock = provider.id == "mock"
    except Exception as e:  # noqa: BLE001 - never fail onboarding; degrade to demo
        log.warning("Principal failed on %s (%s); falling back to demo", provider.id, e)
        mock = MockProvider()
        curriculum = principal.design_curriculum(mock, body.goal, body.level, materials)
        provider, using_mock = mock, True

    cur_dict = curriculum.model_dump()
    # Persist the enrollment, seed faculty state + the student model.
    repo.set_enrollment(uid, cur_dict)
    state = CollegeState()
    state.init_from_curriculum(cur_dict)
    state.save(uid)
    repo.set_student(uid, progress.init_student(cur_dict))

    return OnboardOut(curriculum=curriculum, provider=provider.id,
                      model=provider.model, using_mock=using_mock)
