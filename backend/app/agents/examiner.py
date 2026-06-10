"""The Examiner agent — grades a learner's answer against a bar.

The asymmetry that defines AULA: grading affects the *teacher's* reward, never
the learner's standing. A pass is positive reward to the professor; a fail is
negative reward and triggers the Provost to rewrite their methodology.
"""
from __future__ import annotations

import json
import re

from ..llm.base import LLMProvider

_SYSTEM = """You are the Examiner at AULA, an AI-run college. Grade the
learner's free-text answer against the question, in any domain, using this
rubric (total 0-100):
- Correctness (50): factually right; no key misconception.
- Understanding (30): explains WHY in their own words, not just what.
- Application (20): connects the idea to a use, consequence, or example.

Calibration: 90+ exceptional · 70-89 solid · 50-69 partial grasp · below 50
missed the core idea. Grade the content, never the grammar. Be honest — a
generous score for a wrong answer hurts the learner.

Feedback: 2-3 sentences, addressed to the learner. First name what they got
right, then the single most important thing to improve. Fair, never cruel.

Return a single JSON object, no markdown:
{"score": <0-100 integer>, "feedback": "<2-3 sentences>"}
Output ONLY the JSON object."""

_GEN_SYSTEM = """You are the Examiner at AULA, an AI-run college. Design an exam
for the module the learner just studied — in any domain. Follow this blueprint,
one question each:
1. Core concept — "what problem does this solve / why does it exist?"
2. Application — a small realistic scenario they must reason through.
3. Misconception or edge case — where people typically go wrong.
4. Explain it simply — teach the idea to a beginner in two sentences.

Each question must be answerable in 2-4 sentences of free text by someone who
truly learned the module — and hard to bluff by someone who skimmed. Hints
point at the angle of attack, never the answer.

Return a single JSON object, no markdown:
{"questions": [{"q": "<the question>", "hint": "<short hint>"}]}
Rules: exactly 4 questions. Output ONLY the JSON object."""


def generate_exam(provider: LLMProvider, *, subject: str, module: str,
                  topics: list[str] | None = None) -> list[dict]:
    """Returns [{q, hint}, ...]. Never raises — degrades to template questions."""
    user = f"Subject: {subject}\nModule: {module}"
    if topics:
        user += "\nSyllabus topics this module covered (test across them):\n- " + "\n- ".join(topics[:6])
    try:
        raw = provider.complete(_GEN_SYSTEM, [{"role": "user", "content": user}],
                                max_tokens=1200, json=True)
        data = _parse(raw)
        questions = [
            {"q": str(q.get("q", "")).strip(), "hint": str(q.get("hint", "")).strip()}
            for q in data.get("questions", []) if str(q.get("q", "")).strip()
        ]
        if questions:
            return questions[:6]
    except Exception:  # noqa: BLE001 - an exam must always exist
        pass
    return [
        {"q": f"In your own words, what problem does “{module}” solve?",
         "hint": "Think about what would break without it."},
        {"q": f"Walk through how you would apply {module} in a small real project.",
         "hint": "Name the steps in order."},
        {"q": f"What is the most common mistake people make with {module}, and how do you avoid it?",
         "hint": "Think about edge cases."},
        {"q": f"Explain {module} to a beginner in two sentences.",
         "hint": "Plain words beat jargon."},
    ]


def grade_exam(provider: LLMProvider, *, questions: list[dict], answers: list[str],
               bar: int = 70) -> dict:
    """Grade a whole exam: per-question grading, averaged overall score."""
    per_question = []
    for i, q in enumerate(questions):
        answer = answers[i] if i < len(answers) else ""
        per_question.append(grade(provider, question=q.get("q", ""), answer=answer, bar=bar))
    if not per_question:
        return {"score": 0, "passed": False, "feedback": "Empty exam.", "per_question": []}
    score = round(sum(r["score"] for r in per_question) / len(per_question))
    weakest = min(per_question, key=lambda r: r["score"])
    feedback = weakest["feedback"]
    return {"score": score, "passed": score >= bar, "feedback": feedback,
            "per_question": per_question}


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
