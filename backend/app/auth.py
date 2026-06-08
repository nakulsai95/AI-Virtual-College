"""Authentication — email/password (PBKDF2) + bearer tokens, on SQLAlchemy."""
from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import Depends, Header, HTTPException
from sqlalchemy import delete, insert, select

from .db import GUEST_ID, engine, tokens, users

_ITER = 200_000


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITER).hex()


def register(email: str, password: str, name: str = "") -> dict:
    email = email.strip().lower()
    if not email or not password:
        raise HTTPException(400, "Email and password are required.")
    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")
    salt = secrets.token_hex(16)
    pw_hash = _hash(password, salt)
    display = name or email.split("@")[0]
    with engine.begin() as conn:
        exists = conn.execute(select(users.c.id).where(users.c.email == email)).first()
        if exists:
            raise HTTPException(409, "An account with that email already exists.")
        result = conn.execute(insert(users).values(
            email=email, name=display, pw_hash=pw_hash, pw_salt=salt))
        uid = result.inserted_primary_key[0]
    return {"id": uid, "email": email, "name": display, "token": _issue(uid)}


def login(email: str, password: str) -> dict:
    email = email.strip().lower()
    with engine.begin() as conn:
        row = conn.execute(
            select(users.c.id, users.c.name, users.c.pw_hash, users.c.pw_salt)
            .where(users.c.email == email)
        ).first()
    if not row or not row.pw_salt or not hmac.compare_digest(_hash(password, row.pw_salt), row.pw_hash):
        raise HTTPException(401, "Wrong email or password.")
    return {"id": row.id, "email": email, "name": row.name, "token": _issue(row.id)}


def _issue(uid: int) -> str:
    token = secrets.token_urlsafe(32)
    with engine.begin() as conn:
        conn.execute(insert(tokens).values(token=token, user_id=uid))
    return token


def logout(token: str):
    with engine.begin() as conn:
        conn.execute(delete(tokens).where(tokens.c.token == token))


def _user_from_token(token: str) -> dict | None:
    with engine.begin() as conn:
        row = conn.execute(
            select(users.c.id, users.c.email, users.c.name)
            .select_from(tokens.join(users, users.c.id == tokens.c.user_id))
            .where(tokens.c.token == token)
        ).first()
    return {"id": row.id, "email": row.email, "name": row.name} if row else None


def current_user(authorization: str | None = Header(default=None)) -> dict:
    """FastAPI dependency. Returns the authed user, or the GUEST user."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        user = _user_from_token(token)
        if user:
            return {**user, "guest": False}
    return {"id": GUEST_ID, "email": None, "name": "Guest", "guest": True}


CurrentUser = Depends(current_user)
