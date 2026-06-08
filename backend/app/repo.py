"""Per-user state + content-KB access (SQLAlchemy Core)."""
from __future__ import annotations

import json

from sqlalchemy import delete, insert, select, update

from .db import engine, library, materials, user_state


# -- per-user JSON state (connector, enrollment, faculty, student, ...) ----

def _get(kind: str, uid: int) -> dict | None:
    with engine.begin() as conn:
        row = conn.execute(
            select(user_state.c.data).where(
                user_state.c.user_id == uid, user_state.c.kind == kind)
        ).first()
    if not row or not row[0]:
        return None
    try:
        return json.loads(row[0])
    except json.JSONDecodeError:
        return None


def _set(kind: str, uid: int, value: dict | None):
    with engine.begin() as conn:
        if value is None:
            conn.execute(delete(user_state).where(
                user_state.c.user_id == uid, user_state.c.kind == kind))
            return
        payload = json.dumps(value)
        exists = conn.execute(
            select(user_state.c.user_id).where(
                user_state.c.user_id == uid, user_state.c.kind == kind)
        ).first()
        if exists:
            conn.execute(update(user_state).where(
                user_state.c.user_id == uid, user_state.c.kind == kind).values(data=payload))
        else:
            conn.execute(insert(user_state).values(user_id=uid, kind=kind, data=payload))


def get_connector(uid: int):   return _get("connector", uid)
def set_connector(uid: int, v): _set("connector", uid, v)

def get_search(uid: int):      return _get("search", uid)
def set_search(uid: int, v):   _set("search", uid, v)

def get_enrollment(uid: int):  return _get("enrollment", uid)
def set_enrollment(uid: int, v): _set("enrollment", uid, v)

def get_faculty(uid: int):     return _get("faculty", uid)
def set_faculty(uid: int, v):  _set("faculty", uid, v)

def get_student(uid: int):     return _get("student", uid)
def set_student(uid: int, v):  _set("student", uid, v)

def get_exams(uid: int):       return _get("exams", uid) or {"results": []}
def set_exams(uid: int, v):    _set("exams", uid, v)

def get_channel(uid: int):     return _get("channel", uid) or {"messages": []}
def set_channel(uid: int, v):  _set("channel", uid, v)

def get_notif(uid: int):       return _get("notif", uid) or {}
def set_notif(uid: int, v):    _set("notif", uid, v)


# -- content knowledge base ------------------------------------------------

def add_materials(uid: int, topic: str, sources: list[dict]):
    if not sources:
        return
    with engine.begin() as conn:
        conn.execute(insert(materials), [
            {"owner_id": uid, "topic": topic, "title": s.get("title", ""),
             "url": s.get("url", ""), "snippet": s.get("snippet", ""),
             "kind": s.get("kind", "web"), "source": s.get("source", "")}
            for s in sources
        ])


def list_materials(uid: int, limit: int = 200) -> list[dict]:
    with engine.begin() as conn:
        rows = conn.execute(
            select(materials).where(materials.c.owner_id == uid)
            .order_by(materials.c.id.desc()).limit(limit)
        ).mappings().all()
    return [dict(r) | {"created_at": str(r["created_at"])} for r in rows]


def add_library_lesson(uid: int, subject: str, title: str, data: dict):
    with engine.begin() as conn:
        conn.execute(insert(library).values(
            owner_id=uid, subject=subject, title=title, data=json.dumps(data)))


def list_library(uid: int, limit: int = 200) -> list[dict]:
    with engine.begin() as conn:
        rows = conn.execute(
            select(library).where(library.c.owner_id == uid)
            .order_by(library.c.id.desc()).limit(limit)
        ).mappings().all()
    out = []
    for r in rows:
        try:
            data = json.loads(r["data"]) if r["data"] else {}
        except json.JSONDecodeError:
            data = {}
        out.append({"id": r["id"], "subject": r["subject"], "title": r["title"],
                    "author": data.get("author", ""), "read": data.get("read", ""),
                    "created_at": str(r["created_at"])})
    return out
