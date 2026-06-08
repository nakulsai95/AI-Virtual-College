"""The Professor agent — authors a lesson on demand.

Given a subject + topic (and the professor's current methodology), it writes a
short, structured lesson with a runnable code starter and a probe question that
checks understanding. The probe is what gets graded — and grading the answer
rewards the *professor*, not the student.
"""
from __future__ import annotations

import json
import re

from ..llm.base import LLMProvider

# Default sandbox + starter per subject domain, so "Run it" has something real.
_STARTERS = {
    "python": ("python", "# Try it — edit and run\nprint(sum(range(1, 11)))\n"),
    "sql": ("sql", "-- Try it — a table 'users(id, name, age)' is seeded for you\nSELECT name, age FROM users ORDER BY age DESC;\n"),
    "git": ("python", "# Sketch your solution here\nprint('hello from the sandbox')\n"),
    "jupyter": ("python", "import statistics\ndata = [4, 8, 15, 16, 23, 42]\nprint('mean', statistics.mean(data))\n"),
    "shell": ("python", "print('hello from the sandbox')\n"),
}


def _system(methodology: dict) -> str:
    return f"""You are a Professor at AULA, an AI college. Write ONE short lesson
for a learner on the given topic. Teach in this style:
- pacing: {methodology.get('pacing')}
- sequence: {methodology.get('sequence')}
- modality: {methodology.get('modality')}
- examples: {methodology.get('examples')}

Return a single JSON object, no markdown:
{{
  "title": "<lesson title>",
  "read": "<e.g. 6 min>",
  "intro": "<2-3 sentence hook explaining why this matters>",
  "sections": [{{"h": "<heading>", "p": "<one tight paragraph>"}}],
  "probe": {{"q": "<one question that checks real understanding>", "hint": "<short hint>"}}
}}
Rules: 3 sections. Keep paragraphs concrete. Output ONLY the JSON object."""


def design_lesson(provider: LLMProvider, *, subject: str, topic: str, professor: str,
                  methodology: dict, sandbox: str = "python") -> dict:
    user = f"Subject: {subject}\nTopic the learner asked about: {topic}"
    raw = provider.complete(_system(methodology), [{"role": "user", "content": user}],
                            max_tokens=2500, json=True)
    data = _parse(raw, subject, topic)
    lang, starter = _STARTERS.get(sandbox, _STARTERS["python"])
    return {
        "title": data["title"],
        "author": professor or "Professor",
        "authorRole": "professor",
        "subject": subject,
        "read": data.get("read", "6 min"),
        "intro": data["intro"],
        "sections": data["sections"][:4],
        "probe": data["probe"],
        "sandbox": sandbox,
        "code_language": lang,
        "code_starter": starter,
        "next": "Build on this",
    }


def _parse(raw: str, subject: str, topic: str) -> dict:
    raw = (raw or "").strip()
    for candidate in (raw, _fenced(raw), _braced(raw)):
        if not candidate:
            continue
        try:
            d = json.loads(candidate)
            if "title" in d and "sections" in d and "probe" in d:
                return d
        except json.JSONDecodeError:
            continue
    # tolerant fallback so a lesson always renders
    return {
        "title": topic.strip().title() or subject,
        "read": "5 min",
        "intro": f"A quick lesson on {topic} within {subject}.",
        "sections": [
            {"h": "The idea", "p": f"{topic} is a core part of {subject}. Here's the essence."},
            {"h": "How it works", "p": "We break it down into the moving parts and how they fit."},
            {"h": "Why it matters", "p": "Knowing this unlocks the next step in your plan."},
        ],
        "probe": {"q": f"In your own words, what problem does {topic} solve?",
                  "hint": "Think about what would break without it."},
    }


def _fenced(raw: str) -> str:
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    return m.group(1) if m else ""


def _braced(raw: str) -> str:
    s, e = raw.find("{"), raw.rfind("}")
    return raw[s : e + 1] if s != -1 and e > s else ""
