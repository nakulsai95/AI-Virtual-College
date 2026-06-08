"""AULA backend — FastAPI app.

Multi-user: accounts + per-user persistence (SQLite). Exposes the LLM connector
system, the Principal/Professor/Examiner agents, the reward loop, real
sandboxes, and the learner's progress diagnostic.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__, repo
from .config import cors_origins, seed_connector
from .db import GUEST_ID, init_db
from .routers import auth, connectors, faculty, onboard, progress, sandbox

app = FastAPI(title="AULA — Virtual AI College", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(connectors.router)
app.include_router(onboard.router)
app.include_router(faculty.router)
app.include_router(sandbox.router)
app.include_router(progress.router)


@app.on_event("startup")
def _startup():
    init_db()
    # Optional: seed the guest user's connector from env so the app can run
    # against a real model without anyone signing in or touching the UI.
    seed = seed_connector()
    if seed and not repo.get_connector(GUEST_ID):
        repo.set_connector(GUEST_ID, seed)
    logging.getLogger("aula").info("AULA backend ready (v%s)", __version__)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "aula", "version": __version__}
