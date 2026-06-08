"""Connector management — the LLM-provider picker, now per-user."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import repo
from ..auth import CurrentUser
from ..llm import PROVIDER_SPECS, build_provider, provider_spec
from ..schemas import ConnectorIn, ConnectorStatus, SearchConnectorIn

router = APIRouter(prefix="/api/connectors", tags=["connectors"])

SEARCH_PROVIDERS = [
    {"id": "tavily", "name": "Tavily", "key_url": "https://app.tavily.com/", "key_label": "TAVILY_API_KEY"},
]


def _status(uid: int) -> ConnectorStatus:
    cfg = repo.get_connector(uid)
    provider = build_provider(cfg)
    using_mock = provider.id == "mock"
    pid = (cfg or {}).get("provider", "") if cfg else ""
    spec = provider_spec(pid)
    return ConnectorStatus(
        provider=pid or "",
        name=spec["name"] if spec else "",
        model=(cfg or {}).get("model", "") or (provider.model if not using_mock else ""),
        connected=not using_mock,
        has_key=bool((cfg or {}).get("api_key")),
        using_mock=using_mock,
    )


@router.get("/providers")
def list_providers():
    return {"providers": PROVIDER_SPECS}


@router.get("/active", response_model=ConnectorStatus)
def get_active(user=CurrentUser):
    return _status(user["id"])


@router.put("/active", response_model=ConnectorStatus)
def set_active(body: ConnectorIn, user=CurrentUser):
    spec = provider_spec(body.provider)
    if spec is None:
        raise HTTPException(400, f"Unknown provider '{body.provider}'")
    if spec["requires_key"] and not body.api_key:
        raise HTTPException(400, f"{spec['name']} requires an API key.")
    repo.set_connector(user["id"], {
        "provider": body.provider, "api_key": body.api_key,
        "model": body.model or spec["default_model"], "base_url": body.base_url,
    })
    return _status(user["id"])


@router.post("/test")
def test_connector(body: ConnectorIn):
    spec = provider_spec(body.provider)
    if spec is None:
        raise HTTPException(400, f"Unknown provider '{body.provider}'")
    provider = build_provider({
        "provider": body.provider, "api_key": body.api_key,
        "model": body.model or spec["default_model"], "base_url": body.base_url,
    })
    if provider.id == "mock":
        return {"ok": False, "detail": "No key provided — would run in demo mode.", "model": ""}
    return provider.test()


@router.delete("/active", response_model=ConnectorStatus)
def clear_active(user=CurrentUser):
    repo.set_connector(user["id"], None)
    return _status(user["id"])


# --- Search connector (grounds the curriculum in real web results) ------

@router.get("/search/providers")
def search_providers():
    return {"providers": SEARCH_PROVIDERS}


@router.get("/search")
def get_search(user=CurrentUser):
    cfg = repo.get_search(user["id"]) or {}
    return {"provider": cfg.get("provider", ""), "connected": bool(cfg.get("api_key"))}


@router.put("/search")
def set_search(body: SearchConnectorIn, user=CurrentUser):
    if not body.api_key:
        raise HTTPException(400, "A search API key is required.")
    repo.set_search(user["id"], {"provider": body.provider, "api_key": body.api_key})
    return {"provider": body.provider, "connected": True}


@router.delete("/search")
def clear_search(user=CurrentUser):
    repo.set_search(user["id"], None)
    return {"provider": "", "connected": False}
