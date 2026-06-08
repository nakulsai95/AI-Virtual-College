"""Connector management — the LLM-provider picker the user drives in the UI."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import store
from ..llm import PROVIDER_SPECS, build_provider, provider_spec
from ..schemas import ConnectorIn, ConnectorStatus

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


def _status() -> ConnectorStatus:
    cfg = store.get_connector()
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
    """The catalogue the Connections screen renders."""
    return {"providers": PROVIDER_SPECS}


@router.get("/active", response_model=ConnectorStatus)
def get_active():
    return _status()


@router.put("/active", response_model=ConnectorStatus)
def set_active(body: ConnectorIn):
    spec = provider_spec(body.provider)
    if spec is None:
        raise HTTPException(400, f"Unknown provider '{body.provider}'")
    if spec["requires_key"] and not body.api_key:
        raise HTTPException(400, f"{spec['name']} requires an API key.")
    cfg = {
        "provider": body.provider,
        "api_key": body.api_key,
        "model": body.model or spec["default_model"],
        "base_url": body.base_url,
    }
    store.set_connector(cfg)
    return _status()


@router.post("/test")
def test_connector(body: ConnectorIn):
    """Verify a candidate connector WITHOUT saving it (live round-trip)."""
    spec = provider_spec(body.provider)
    if spec is None:
        raise HTTPException(400, f"Unknown provider '{body.provider}'")
    provider = build_provider({
        "provider": body.provider,
        "api_key": body.api_key,
        "model": body.model or spec["default_model"],
        "base_url": body.base_url,
    })
    if provider.id == "mock":
        return {"ok": False, "detail": "No key provided — would run in demo mode.", "model": ""}
    return provider.test()


@router.delete("/active", response_model=ConnectorStatus)
def clear_active():
    store.clear_connector()
    return _status()
