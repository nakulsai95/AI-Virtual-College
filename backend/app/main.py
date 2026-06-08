"""AULA backend — FastAPI app.

Exposes the LLM connector system (user picks a provider + supplies a key) and
the Principal onboarding agent that designs a real curriculum.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import cors_origins
from .routers import connectors, faculty, onboard, sandbox

app = FastAPI(title="AULA — Virtual AI College", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connectors.router)
app.include_router(onboard.router)
app.include_router(faculty.router)
app.include_router(sandbox.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "aula", "version": __version__}
