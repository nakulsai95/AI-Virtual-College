"""The Principal (Orchestrator) agent.

Given a learner's goal, it designs the college: a faculty of agents, a set of
subjects, and per-subject modules — and chooses the right sandbox(es) to mount
for each subject (Python, SQL, Git, web search, Jupyter, shell), so the
environment matches what's being studied rather than defaulting to Python.
"""
from __future__ import annotations

import json
import re

from ..llm.base import LLMProvider
from ..schemas import Curriculum

# Allowed sandbox ids the Principal may mount per subject. This is the
# topic/semester-driven sandbox catalogue the user asked for.
SANDBOXES = ["python", "sql", "git", "web-search", "jupyter", "shell", "notebook"]

SYSTEM = f"""You are the Principal of AULA, an AI-run virtual college. A learner
tells you what they want to learn. You design the whole institution for them.

Design a focused curriculum and return it as a single JSON object with EXACTLY
this shape (no markdown, no commentary):

{{
  "mission": "<one-line restatement of their goal>",
  "level": "beginner|intermediate|advanced",
  "weeks": <integer 8-16>,
  "summary": "<2-3 sentence overview of the plan>",
  "subjects": [
    {{
      "id": "s1",
      "title": "<subject name>",
      "professor": "<a short first name>",
      "sandboxes": [<1-3 ids from: {SANDBOXES}>],
      "modules": [
        {{"id": "s1m1", "title": "<module title>"}}
      ]
    }}
  ],
  "faculty": [
    {{"id": "principal", "role": "principal", "name": "<name>", "model": ""}},
    {{"id": "provost", "role": "provost", "name": "<name>", "model": ""}},
    {{"id": "prof1", "role": "professor", "name": "<name>", "subject": "<subject title>", "model": ""}},
    {{"id": "examiner", "role": "examiner", "name": "<name>", "model": ""}},
    {{"id": "guide", "role": "guide", "name": "<name>", "model": ""}}
  ]
}}

Rules:
- 2 to 4 subjects, each with 4 to 6 modules ordered from foundations to mastery.
- Choose sandboxes that fit the SUBJECT's topic — e.g. SQL/databases -> "sql",
  data science -> "jupyter", coding -> "python" or "git", theory -> "web-search".
  Do NOT default everything to "python".
- One professor per subject; include their name in faculty with role "professor".
- Keep names short and human. Output ONLY the JSON object."""


def design_curriculum(provider: LLMProvider, goal: str, level: str) -> Curriculum:
    user = f"My goal: {goal.strip() or 'become job-ready in backend Python'}\nMy level: {level}"
    raw = provider.complete(SYSTEM, [{"role": "user", "content": user}], max_tokens=4000, json=True)
    data = _parse_json(raw)
    # Stamp the connected model onto every faculty member for the Command Center.
    for f in data.get("faculty", []):
        if not f.get("model"):
            f["model"] = provider.model
    return Curriculum.model_validate(data)


def _parse_json(raw: str) -> dict:
    """Tolerant JSON extraction — providers sometimes wrap output in prose/fences."""
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # strip ```json fences
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    # grab the first balanced-looking object
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            pass
    raise ValueError("Principal did not return valid JSON curriculum")
