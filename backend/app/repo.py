"""Per-user state access — JSON blobs keyed by user id."""
from __future__ import annotations

import json

from .db import connect

_TABLES = {"connector": "connectors", "enrollment": "enrollments",
           "faculty": "faculty_state", "student": "student_model",
           "exams": "exam_results"}


def _get(kind: str, user_id: int) -> dict | None:
    table = _TABLES[kind]
    with connect() as conn:
        row = conn.execute(f"SELECT json FROM {table} WHERE user_id = ?", (user_id,)).fetchone()
    if not row or not row["json"]:
        return None
    try:
        return json.loads(row["json"])
    except json.JSONDecodeError:
        return None


def _set(kind: str, user_id: int, value: dict | None):
    table = _TABLES[kind]
    with connect() as conn:
        if value is None:
            conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
            return
        ts = ", updated_at = datetime('now')" if kind == "enrollment" else ""
        cols = "(user_id, json, updated_at)" if kind == "enrollment" else "(user_id, json)"
        vals = "(?, ?, datetime('now'))" if kind == "enrollment" else "(?, ?)"
        conn.execute(
            f"INSERT INTO {table} {cols} VALUES {vals} "
            f"ON CONFLICT(user_id) DO UPDATE SET json = excluded.json{ts}",
            (user_id, json.dumps(value)),
        )


# Typed convenience wrappers ------------------------------------------------

def get_connector(uid: int):   return _get("connector", uid)
def set_connector(uid: int, v): _set("connector", uid, v)

def get_enrollment(uid: int):  return _get("enrollment", uid)
def set_enrollment(uid: int, v): _set("enrollment", uid, v)

def get_faculty(uid: int):     return _get("faculty", uid)
def set_faculty(uid: int, v):  _set("faculty", uid, v)

def get_student(uid: int):     return _get("student", uid)
def set_student(uid: int, v):  _set("student", uid, v)

def get_exams(uid: int):       return _get("exams", uid) or {"results": []}
def set_exams(uid: int, v):    _set("exams", uid, v)
