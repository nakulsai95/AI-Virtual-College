"""Mock connector — runs with no key so the app works before one is added.

It returns a deterministic, plausible curriculum derived from the goal text so
the onboarding flow is fully functional offline. Real providers replace it the
moment the user connects one in the UI.
"""
from __future__ import annotations

import json

from ..base import LLMProvider


class MockProvider(LLMProvider):
    id = "mock"
    name = "Demo (no key)"

    @property
    def default_model(self) -> str:
        return "aula-demo"

    def complete(self, system, messages, *, max_tokens=4000, json=False):
        if not json:
            return "pong"
        user = " ".join(m["content"] for m in messages if m["role"] == "user")
        return _demo_curriculum_json(_clean_goal(user))


def _clean_goal(text: str) -> str:
    """Pull just the goal out of the agent's 'My goal: ...\\nMy level: ...' prompt."""
    import re
    m = re.search(r"my goal:\s*(.+)", text, re.IGNORECASE)
    goal = m.group(1) if m else text
    return re.split(r"\bmy level:", goal, flags=re.IGNORECASE)[0].strip()


# --- naive topic inference, just enough to feel responsive ----------------
_TOPIC_MAP = [
    (("python", "backend", "api", "django", "flask", "fastapi"),
     [("APIs & Services", "py"), ("Databases", "sql")]),
    (("react", "frontend", "javascript", "typescript", "web"),
     [("React & Components", "git"), ("State & Data Fetching", "git")]),
    (("sql", "database", "data engineering", "data engineer"),
     [("Relational Modelling", "sql"), ("Querying & Performance", "sql")]),
    (("machine learning", "ml", "data science", "ai", "neural", "pandas"),
     [("Foundations of ML", "jupyter"), ("Models & Evaluation", "jupyter")]),
]


def _subjects_for(goal: str):
    for keys, subs in _TOPIC_MAP:
        if any(k in goal for k in keys):
            return subs
    return [("Core Concepts", "shell"), ("Applied Practice", "git")]


def _demo_curriculum_json(goal: str) -> str:
    subjects_seed = _subjects_for(goal)
    subjects = []
    for i, (title, sandbox) in enumerate(subjects_seed):
        subjects.append({
            "id": f"s{i+1}",
            "title": title,
            "professor": ["Mei", "Kenji", "Aria", "Ravi"][i % 4],
            "sandboxes": [sandbox, "web-search"],
            "modules": [
                {"id": f"s{i+1}m1", "title": f"{title}: foundations"},
                {"id": f"s{i+1}m2", "title": f"{title}: core techniques"},
                {"id": f"s{i+1}m3", "title": f"{title}: building real things"},
                {"id": f"s{i+1}m4", "title": f"{title}: testing & mastery"},
            ],
        })
    data = {
        "mission": goal.strip()[:120] or "Reach your learning goal",
        "level": "intermediate",
        "weeks": 12,
        "summary": "A demo curriculum (no LLM key connected). Connect a provider "
                   "in Connections to have a real Principal design this for you.",
        "subjects": subjects,
        "faculty": [
            {"id": "principal", "role": "principal", "name": "Iroha", "model": "demo"},
            {"id": "provost", "role": "provost", "name": "Daichi", "model": "demo"},
        ] + [
            {"id": f"prof{i+1}", "role": "professor", "name": s["professor"],
             "subject": s["title"], "model": "demo"}
            for i, s in enumerate(subjects)
        ] + [
            {"id": "examiner", "role": "examiner", "name": "Rei", "model": "demo"},
            {"id": "guide", "role": "guide", "name": "Yuki", "model": "demo"},
        ],
    }
    return json.dumps(data)
