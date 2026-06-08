"""The Examiner agent — grades a learner's answer against a bar.

The asymmetry that defines AULA: grading affects the *teacher's* reward, never
the learner's standing. A pass is positive reward to the professor; a fail is
negative reward and triggers the Provost to rewrite their methodology.
"""
from __future__ import annotations

import json
import re

from ..llm.base import LLMProvider

_SYSTEM = """You are the Examiner at AULA. Grade the learner's answer to the
question on a 0-100 scale for correctness and understanding. Be fair but
honest. Return a single JSON object, no markdown:
{"score": <0-100 integer>, "feedback": "<2-3 sentences: what was right, what to improve>"}
Output ONLY the JSON object."""

_EXAM_SYSTEM = """You are the Examiner at AULA. Write {n} short exam questions
that test real understanding of the subject's concepts (not trivia). Return a
single JSON object, no markdown:
{{"questions": [{{"q": "<question>"}}]}}
Output ONLY the JSON object."""


def build_exam(provider, *, subject: str, concepts: list[str], n: int = 3) -> list[dict]:
    """The Examiner sets an exam from the subject's concepts."""
    concepts = [c for c in (concepts or []) if c] or [subject]
    if getattr(provider, "id", "") == "mock":
        return _exam_fallback(concepts, n)
    try:
        user = f"Subject: {subject}\nConcepts: {', '.join(concepts)}"
        raw = provider.complete(_EXAM_SYSTEM.format(n=n), [{"role": "user", "content": user}],
                                max_tokens=1200, json=True)
        data = _parse(raw)
        out = []
        for i, q in enumerate(data.get("questions", [])[:n]):
            text = q.get("q") or q.get("question") if isinstance(q, dict) else str(q)
            if text:
                out.append({"id": f"q{i+1}", "q": text})
        if out:
            return out
    except Exception:  # noqa: BLE001
        pass
    return _exam_fallback(concepts, n)


def _exam_fallback(concepts: list[str], n: int) -> list[dict]:
    return [{"id": f"q{i+1}", "q": f"Explain “{c}” in your own words, with a concrete example."}
            for i, c in enumerate(concepts[:n])]


def grade(provider: LLMProvider, *, question: str, answer: str, bar: int = 70) -> dict:
    answer = (answer or "").strip()
    if not answer:
        return {"score": 0, "passed": False,
                "feedback": "No answer submitted — give it a try and resubmit."}

    user = f"Question: {question}\n\nLearner's answer: {answer}\n\nPass bar: {bar}"
    try:
        raw = provider.complete(_SYSTEM, [{"role": "user", "content": user}],
                                max_tokens=600, json=True)
        data = _parse(raw)
        score = int(max(0, min(100, data.get("score", 0))))
        feedback = str(data.get("feedback", "")).strip() or "Graded."
    except Exception:  # noqa: BLE001 - degrade to a heuristic so grading never hard-fails
        score, feedback = _heuristic(answer, bar)

    return {"score": score, "passed": score >= bar, "feedback": feedback}


def _heuristic(answer: str, bar: int) -> tuple[int, str]:
    """Length/effort-based fallback when no LLM is connected (demo mode)."""
    words = len(answer.split())
    score = min(95, 45 + words * 4)
    fb = ("Solid attempt — demo grading rewards a clear, reasoned answer. "
          "Connect a model in Connections for real feedback.")
    return score, fb


def _parse(raw: str) -> dict:
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    raise ValueError("examiner returned non-JSON")
