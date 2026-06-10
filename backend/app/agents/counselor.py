"""The Counselor agent — daily pacing nudges, never punitive.

Looks at the learner's weakest active concept and streak, and writes one warm,
specific nudge. Falls back to a template offline.
"""
from __future__ import annotations

import json
import re

from ..llm.base import LLMProvider

_SYSTEM = """You are the Counselor at AULA, an AI-run college. You look after the
learner's pacing and wellbeing. Write ONE short nudge (a single sentence,
warm and specific — never guilt-trippy) that helps them move forward today.

Return a single JSON object, no markdown:
{"nudge": "<one sentence>"}
Output ONLY the JSON object."""


def nudge(provider: LLMProvider, *, streak: int, weakest_concept: str) -> str:
    user = (f"Learner's day streak: {streak}\n"
            f"Weakest concept: {weakest_concept or 'their current module'}")
    try:
        raw = provider.complete(_SYSTEM, [{"role": "user", "content": user}],
                                max_tokens=200, json=True)
        data = _parse(raw)
        text = str(data.get("nudge", "")).strip()
        if text:
            return text[:160]
    except Exception:  # noqa: BLE001 - a nudge is never worth an error
        pass
    target = weakest_concept or "your current module"
    return f"One more rep on {target} and it sticks — try it today."


def _parse(raw: str) -> dict:
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    raise ValueError("counselor returned non-JSON")
