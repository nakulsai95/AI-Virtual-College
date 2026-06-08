"""Authentication — email/password with PBKDF2 hashing and bearer tokens.

Stdlib only (hashlib, secrets). An unauthenticated request resolves to the
GUEST user so the demo keeps working without an account.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import Depends, Header, HTTPException

from .db import GUEST_ID, connect

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
    with connect() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if exists:
            raise HTTPException(409, "An account with that email already exists.")
        cur = conn.execute(
            "INSERT INTO users (email, name, pw_hash, pw_salt) VALUES (?, ?, ?, ?)",
            (email, name or email.split("@")[0], pw_hash, salt),
        )
        uid = cur.lastrowid
    return {"id": uid, "email": email, "name": name or email.split("@")[0], "token": _issue(uid)}


def login(email: str, password: str) -> dict:
    email = email.strip().lower()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, name, pw_hash, pw_salt FROM users WHERE email = ?", (email,)
        ).fetchone()
    if not row or not row["pw_salt"] or not hmac.compare_digest(_hash(password, row["pw_salt"]), row["pw_hash"]):
        raise HTTPException(401, "Wrong email or password.")
    return {"id": row["id"], "email": email, "name": row["name"], "token": _issue(row["id"])}


def _issue(uid: int) -> str:
    token = secrets.token_urlsafe(32)
    with connect() as conn:
        conn.execute("INSERT INTO tokens (token, user_id) VALUES (?, ?)", (token, uid))
    return token


def logout(token: str):
    with connect() as conn:
        conn.execute("DELETE FROM tokens WHERE token = ?", (token,))


def _user_from_token(token: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT u.id, u.email, u.name FROM tokens t JOIN users u ON u.id = t.user_id "
            "WHERE t.token = ?",
            (token,),
        ).fetchone()
    return dict(row) if row else None


def current_user(authorization: str | None = Header(default=None)) -> dict:
    """FastAPI dependency. Returns the authed user, or the GUEST user."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        user = _user_from_token(token)
        if user:
            return {**user, "guest": False}
    return {"id": GUEST_ID, "email": None, "name": "Guest", "guest": True}


CurrentUser = Depends(current_user)
