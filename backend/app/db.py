"""Persistence — SQLAlchemy Core, Postgres-ready.

The whole app talks to one engine driven by DATABASE_URL. It defaults to a
local SQLite file, so nothing extra is needed for dev; point DATABASE_URL at
Postgres (e.g. postgresql+psycopg://user:pass@host/db) for production — the same
code runs unchanged because SQLAlchemy abstracts the dialect.

Layout:
  users / tokens       — accounts + bearer tokens
  user_state           — one JSON blob per (user, kind): connector, enrollment,
                         faculty, student, exams, channel, notif
  materials            — the content knowledge base (retrieved sources)
  library              — authored lessons, reusable per user
"""
from __future__ import annotations

import datetime
import os
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    insert,
    select,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'aula.db'}"

# SQLite needs check_same_thread off for FastAPI's threadpool; Postgres ignores it.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True, connect_args=_connect_args)

metadata = MetaData()
GUEST_ID = 0


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String(320), unique=True),
    Column("name", String(200)),
    Column("pw_hash", Text),
    Column("pw_salt", Text),
    Column("created_at", DateTime, default=_now),
)

tokens = Table(
    "tokens", metadata,
    Column("token", String(80), primary_key=True),
    Column("user_id", Integer, nullable=False),
    Column("created_at", DateTime, default=_now),
)

# One JSON blob per (user_id, kind). Avoids a table per state type.
user_state = Table(
    "user_state", metadata,
    Column("user_id", Integer, primary_key=True),
    Column("kind", String(40), primary_key=True),
    Column("data", Text),
    Column("updated_at", DateTime, default=_now, onupdate=_now),
)

# Content knowledge base: retrieved sources grounding the curriculum.
materials = Table(
    "materials", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("owner_id", Integer, nullable=False),
    Column("topic", String(300)),
    Column("title", Text),
    Column("url", Text),
    Column("snippet", Text),
    Column("kind", String(40)),     # paper | course | book | docs | web
    Column("source", String(40)),   # arxiv | open-index | tavily | ...
    Column("created_at", DateTime, default=_now),
)

# Authored lessons, reusable.
library = Table(
    "library", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("owner_id", Integer, nullable=False),
    Column("subject", Text),
    Column("title", Text),
    Column("data", Text),           # full lesson JSON
    Column("created_at", DateTime, default=_now),
)


def init_db():
    metadata.create_all(engine)
    with engine.begin() as conn:
        exists = conn.execute(select(users.c.id).where(users.c.id == GUEST_ID)).first()
        if not exists:
            conn.execute(insert(users).values(id=GUEST_ID, name="Guest"))
