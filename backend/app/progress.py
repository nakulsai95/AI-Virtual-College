"""The student model — the learner's own diagnostic.

Tracks XP, streak, and per-concept mastery, updated when the learner reads a
lesson or answers a probe. This is the data behind the "My Progress" screen.
Unlike faculty grades, nothing here is punitive — it's a map of what's landed.
"""
from __future__ import annotations

import datetime

_HUES = ["#f5a623", "#3b82f6", "#9b6cff", "#2dd4bf", "#f0846b", "#46d6ad"]


def init_student(curriculum: dict) -> dict:
    mastery = []
    for i, s in enumerate(curriculum.get("subjects", [])):
        concepts = [
            {"name": m["title"], "level": 0.05, "seen": "not yet"}
            for m in s.get("modules", [])
        ]
        mastery.append({"subject": s.get("title", ""), "hue": _HUES[i % len(_HUES)], "concepts": concepts})
    return {
        "mission": curriculum.get("mission", ""),
        "level": curriculum.get("level", "intermediate"),
        "weeks": curriculum.get("weeks", 12),
        "week": 1,
        "xp": 0, "rankTier": 0, "nextTierXp": 300,
        "streak": 0, "momentum": 20, "attendance": 100,
        "lessons_read": 0, "probes_passed": 0, "probes_failed": 0,
        "mastery": mastery,
        "last_active": _today(),
    }


def on_lesson(student: dict, subject: str, topic: str) -> dict:
    _touch(student)
    student["lessons_read"] = student.get("lessons_read", 0) + 1
    block = _subject(student, subject)
    if block:
        concept = _match_concept(block, topic) or _first_unseen(block) or _lowest(block)
        if concept:
            concept["seen"] = "today"
            concept["level"] = max(concept["level"], 0.25)
    student["xp"] = student.get("xp", 0) + 10
    _retier(student)
    return student


def on_grade(student: dict, subject: str, passed: bool, score: int, topic: str = "") -> dict:
    _touch(student)
    block = _subject(student, subject)
    if block:
        concept = _match_concept(block, topic) or _lowest_engaged(block) or _lowest(block)
        if concept:
            concept["seen"] = "today"
            if passed:
                concept["level"] = min(1.0, concept["level"] + 0.25)
            else:
                concept["level"] = min(0.55, concept["level"] + 0.05)
    if passed:
        student["probes_passed"] = student.get("probes_passed", 0) + 1
        student["xp"] = student.get("xp", 0) + 60
        student["momentum"] = min(100, student.get("momentum", 20) + 8)
    else:
        student["probes_failed"] = student.get("probes_failed", 0) + 1
        student["xp"] = student.get("xp", 0) + 15
        student["momentum"] = max(0, student.get("momentum", 20) - 4)
    _retier(student)
    return student


# -- helpers ---------------------------------------------------------------

def _subject(student, subject):
    subject = (subject or "").lower()
    for b in student.get("mastery", []):
        if b["subject"].lower() == subject:
            return b
    return student["mastery"][0] if student.get("mastery") else None


def _match_concept(block, topic):
    topic = (topic or "").lower().strip()
    if not topic:
        return None
    for c in block["concepts"]:
        name = c["name"].lower()
        if topic in name or name in topic or _overlap(name, topic):
            return c
    return None


def _overlap(a, b):
    aw, bw = set(a.split()), set(b.split())
    return len(aw & bw) >= 2


def _first_unseen(block):
    return next((c for c in block["concepts"] if c["seen"] == "not yet"), None)


def _lowest(block):
    return min(block["concepts"], key=lambda c: c["level"]) if block["concepts"] else None


def _lowest_engaged(block):
    seen = [c for c in block["concepts"] if c["seen"] != "not yet"]
    return min(seen, key=lambda c: c["level"]) if seen else None


def _retier(student):
    xp = student["xp"]
    student["rankTier"] = min(3, xp // 300)
    student["nextTierXp"] = (student["rankTier"] + 1) * 300


def _touch(student):
    today = _today()
    last = student.get("last_active")
    if last != today:
        # consecutive-day check
        try:
            d_last = datetime.date.fromisoformat(last)
            gap = (datetime.date.fromisoformat(today) - d_last).days
        except (TypeError, ValueError):
            gap = 1
        student["streak"] = student.get("streak", 0) + 1 if gap == 1 else 1
        student["last_active"] = today


def _today() -> str:
    return datetime.date.today().isoformat()
