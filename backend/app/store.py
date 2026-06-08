"""Tiny persisted store for the active LLM connector.

This keeps the user's provider choice + key between restarts during local dev.
The file lives outside git (see .gitignore). It is NOT a secrets manager —
fine for a single-user prototype, not for production.
"""
from __future__ import annotations

import json
import threading

from .config import CONNECTOR_STORE, seed_connector

_lock = threading.Lock()
_cache: dict | None = None


def _load() -> dict | None:
    global _cache
    if _cache is not None:
        return _cache
    if CONNECTOR_STORE.exists():
        try:
            _cache = json.loads(CONNECTOR_STORE.read_text())
            return _cache
        except (json.JSONDecodeError, OSError):
            pass
    _cache = seed_connector()
    return _cache


def get_connector() -> dict | None:
    with _lock:
        return _load()


def set_connector(config: dict) -> dict:
    global _cache
    with _lock:
        _cache = config
        try:
            CONNECTOR_STORE.write_text(json.dumps(config, indent=2))
        except OSError:
            pass  # in-memory still works even if disk write fails
        return _cache


def clear_connector() -> None:
    global _cache
    with _lock:
        _cache = None
        try:
            CONNECTOR_STORE.unlink(missing_ok=True)
        except OSError:
            pass
