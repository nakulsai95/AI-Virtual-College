"""The Personal Guide agent — routes any learner question to the right professor.

The Guide reads the question, picks the subject (and so the professor) it
belongs to, and replies warmly. The router endpoint then has that professor
actually author a lesson. Falls back to keyword routing offline.
"""
from __future__ import annotations

import json
import re

from ..llm.base import LLMProvider

_SYSTEM = """You are the Personal Guide at AULA, an AI-run college. The learner
asks you anything; you route it to the right professor and reassure the learner.

You will be given the learner's question and the list of subjects (with ids).
Return a single JSON object, no markdown:
{
  "reply": "<1-2 warm sentences: acknowledge the question, say who you're bringing in>",
  "subject": "<the id of the best-matching subject>",
  "topic": "<a short lesson topic distilled from the question>"
}
Pick the subject whose professor should teach this. Output ONLY the JSON object."""


def route(provider: LLMProvider, *, question: str, subjects: list[dict]) -> dict:
    """Returns {reply, subject (id), topic}. Never raises — degrades to keyword routing."""
    listing = "\n".join(
        f"- {s['id']}: {s['title']} (modules: {', '.join(m['title'] for m in s.get('modules', [])[:6])})"
        for s in subjects)
    user = f"Question: {question}\n\nSubjects:\n{listing}"
    try:
        raw = provider.complete(_SYSTEM, [{"role": "user", "content": user}],
                                max_tokens=400, json=True)
        data = _parse(raw)
        sid = str(data.get("subject", "")).strip()
        if not any(s["id"] == sid for s in subjects):
            sid = _keyword_route(question, subjects)
        return {
            "reply": str(data.get("reply", "")).strip() or _default_reply(),
            "subject": sid,
            "topic": str(data.get("topic", "")).strip() or question[:80],
        }
    except Exception:  # noqa: BLE001 - routing must always succeed
        return {"reply": _default_reply(), "subject": _keyword_route(question, subjects),
                "topic": question[:80]}


def _default_reply() -> str:
    return ("Good question — that lives with one of your professors. "
            "Bringing them in; they'll write you a short lesson on it.")


def _keyword_route(question: str, subjects: list[dict]) -> str:
    q = question.lower()
    best, best_hits = "", -1
    for s in subjects:
        words = (s["title"] + " " + " ".join(m["title"] for m in s.get("modules", []))).lower()
        hits = sum(1 for w in set(re.findall(r"[a-z]{3,}", q)) if w in words)
        if hits > best_hits:
            best, best_hits = s["id"], hits
    return best or (subjects[0]["id"] if subjects else "")


def _parse(raw: str) -> dict:
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    raise ValueError("guide returned non-JSON")
