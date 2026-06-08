"""Onboarding — the Principal designs a real curriculum from the goal."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from .. import store
from ..agents import principal
from ..agents.principal import SANDBOXES
from ..llm import build_provider
from ..llm.providers.mock_provider import MockProvider
from ..schemas import OnboardIn, OnboardOut

log = logging.getLogger("aula.onboard")
router = APIRouter(prefix="/api", tags=["onboard"])


@router.get("/sandboxes")
def list_sandboxes():
    """Topic/semester sandbox catalogue the Principal mounts per subject."""
    return {"sandboxes": SANDBOXES}


@router.post("/onboard", response_model=OnboardOut)
def onboard(body: OnboardIn):
    if not body.goal.strip():
        raise HTTPException(400, "Tell the Principal what you want to learn.")

    provider = build_provider(store.get_connector())
    try:
        curriculum = principal.design_curriculum(provider, body.goal, body.level)
        using_mock = provider.id == "mock"
    except Exception as e:  # noqa: BLE001 - never fail onboarding; degrade to demo
        log.warning("Principal failed on %s (%s); falling back to demo curriculum", provider.id, e)
        mock = MockProvider()
        curriculum = principal.design_curriculum(mock, body.goal, body.level)
        provider, using_mock = mock, True

    return OnboardOut(
        curriculum=curriculum,
        provider=provider.id,
        model=provider.model,
        using_mock=using_mock,
    )
