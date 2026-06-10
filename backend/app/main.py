"""AULA backend — FastAPI app.

One server runs the whole college: the API (LLM connectors, agents, sandbox,
persistent state) AND the frontend, served statically at http://localhost:8000.
"""
from __future__ import annotations

import logging
import os
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__, builder, db
from .config import BASE_DIR, cors_origins
from .routers import college, connectors, faculty, onboard, sandbox

REPO_ROOT = BASE_DIR.parent
log = logging.getLogger("aula.main")

app = FastAPI(title="AULA — Virtual AI College", version=__version__)

db.init_db()


@app.on_event("startup")
def _resume_university_build():
    """A restart never loses the university: if the catalog is incomplete,
    the content factory resumes in the background."""
    if os.getenv("AULA_TEST"):
        return  # tests drive the build explicitly

    def _resume():
        try:
            if db.enrolled():
                ready, total = db.catalog_counts()
                if total and ready < total:
                    log.info("resuming university build: %s/%s classes", ready, total)
                    builder.build_college()
        except Exception:  # noqa: BLE001
            log.exception("build resume failed")

    threading.Thread(target=_resume, daemon=True).start()

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
app.include_router(college.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "aula", "version": __version__}


# --- the frontend, same origin (only the UI dirs — never backend/ secrets) ---

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(REPO_ROOT / "index.html")


app.mount("/app", StaticFiles(directory=REPO_ROOT / "app"), name="app")
if (REPO_ROOT / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=REPO_ROOT / "assets"), name="assets")
