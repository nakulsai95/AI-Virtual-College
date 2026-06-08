"""Faculty Room (live agent conversation) + notifications."""
from __future__ import annotations

import time

from fastapi import APIRouter

from .. import repo
from ..agents import faculty_room
from ..auth import CurrentUser
from ..llm import build_provider
from ..state import CollegeState

router = APIRouter(prefix="/api", tags=["channel"])


@router.get("/channel")
def get_channel(user=CurrentUser):
    """Persisted faculty-room messages for this user."""
    return repo.get_channel(user["id"])


@router.post("/channel/advance")
def advance_channel(user=CurrentUser):
    """The faculty discuss the student's current progress; append + return new messages."""
    uid = user["id"]
    provider = build_provider(repo.get_connector(uid))
    enr = repo.get_enrollment(uid) or {}
    state = CollegeState.load(uid)
    snap = state.snapshot()

    new = faculty_room.discuss(
        provider,
        faculty=enr.get("faculty", []),
        professors=snap["professors"],
        feed=snap["feed"],
        mission=enr.get("mission", ""),
    )
    t = time.strftime("%H:%M")
    for m in new:
        m["t"] = t

    log = repo.get_channel(uid)
    log["messages"] = (log["messages"] + new)[-40:]
    repo.set_channel(uid, log)
    return {"messages": new, "provider": provider.id, "using_mock": provider.id == "mock"}


# --- Notifications (driven by the reward feed) --------------------------

@router.get("/notifications")
def notifications(user=CurrentUser):
    uid = user["id"]
    feed = CollegeState.load(uid).feed
    marker = repo.get_notif(uid).get("marker")
    unread = 0
    for ev in feed:
        if marker and ev.get("t") == marker.get("t") and ev.get("text") == marker.get("text"):
            break
        unread += 1
    return {"events": feed[:15], "unread": unread}


@router.post("/notifications/seen")
def mark_seen(user=CurrentUser):
    uid = user["id"]
    feed = CollegeState.load(uid).feed
    repo.set_notif(uid, {"marker": ({"t": feed[0]["t"], "text": feed[0]["text"]} if feed else None)})
    return {"unread": 0}
