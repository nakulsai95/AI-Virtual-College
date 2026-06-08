"""SQLite persistence — multi-user storage with zero extra dependencies.

One file (backend/aula.db, git-ignored). Connections are opened per call and
closed promptly; FastAPI runs sync endpoints in a threadpool, so this stays
simple and safe without a global connection.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "aula.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  email      TEXT UNIQUE,
  name       TEXT,
  pw_hash    TEXT,
  pw_salt    TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS tokens (
  token      TEXT PRIMARY KEY,
  user_id    INTEGER NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);
-- One row per user holding a JSON blob, for each kind of state.
CREATE TABLE IF NOT EXISTS connectors    (user_id INTEGER PRIMARY KEY, json TEXT);
CREATE TABLE IF NOT EXISTS enrollments   (user_id INTEGER PRIMARY KEY, json TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS faculty_state (user_id INTEGER PRIMARY KEY, json TEXT);
CREATE TABLE IF NOT EXISTS student_model (user_id INTEGER PRIMARY KEY, json TEXT);
"""

# Reserved id for the anonymous / "continue as guest" user.
GUEST_ID = 0


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with connect() as conn:
        conn.executescript(_SCHEMA)
        # Ensure the guest user exists (id 0) for anonymous sessions.
        conn.execute(
            "INSERT OR IGNORE INTO users (id, email, name) VALUES (?, ?, ?)",
            (GUEST_ID, None, "Guest"),
        )
