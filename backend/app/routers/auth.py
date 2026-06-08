"""Auth — register, login, logout, and whoami."""
from __future__ import annotations

from fastapi import APIRouter, Header

from .. import auth
from ..auth import CurrentUser
from ..schemas import AuthIn, AuthOut, RegisterIn

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthOut)
def register(body: RegisterIn):
    u = auth.register(body.email, body.password, body.name)
    return AuthOut(**u)


@router.post("/login", response_model=AuthOut)
def login(body: AuthIn):
    u = auth.login(body.email, body.password)
    return AuthOut(**u)


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    if authorization and authorization.lower().startswith("bearer "):
        auth.logout(authorization.split(" ", 1)[1].strip())
    return {"ok": True}


@router.get("/me")
def me(user=CurrentUser):
    return {"id": user["id"], "email": user["email"], "name": user["name"], "guest": user["guest"]}
