"""The Principal (Orchestrator) agent.

Given a learner's goal — and a set of real, retrieved materials to ground it —
the Principal designs the whole college: a faculty of agents, subjects with
modules, per-module learning objectives + an assignment, a per-subject sandbox,
a milestone timeline, and reading lists drawn from the retrieved sources.

The design is always synthesised by the LLM the user connected.
"""
from __future__ import annotations

import json
import re

from ..llm.base import LLMProvider
from ..schemas import Curriculum

SANDBOXES = ["python", "sql", "git", "web-search", "jupyter", "shell", "notebook"]

SYSTEM = f"""You are the Principal of AULA, an AI-run virtual college. A learner
tells you what they want to learn. You design the whole institution, grounding
it in the real learning MATERIALS provided. Return ONE JSON object, no markdown:

{{
  "mission": "<one-line restatement of the goal>",
  "level": "beginner|intermediate|advanced",
  "weeks": <integer 8-16>,
  "summary": "<2-3 sentence overview>",
  "subjects": [
    {{
      "id": "s1",
      "title": "<subject>",
      "professor": "<short first name>",
      "sandboxes": [<1-3 ids from: {SANDBOXES}>],
      "modules": [
        {{
          "id": "s1m1",
          "title": "<module>",
          "objectives": ["<specific, checkable learning objective>", "..."],
          "assignment": {{"title": "<assignment>", "prompt": "<what to build/do>", "sandbox": "<one sandbox id>"}}
        }}
      ]
    }}
  ],
  "faculty": [
    {{"id": "principal", "role": "principal", "name": "<name>", "model": ""}},
    {{"id": "provost", "role": "provost", "name": "<name>", "model": ""}},
    {{"id": "prof1", "role": "professor", "name": "<name>", "subject": "<subject title>", "model": ""}},
    {{"id": "examiner", "role": "examiner", "name": "<name>", "model": ""}},
    {{"id": "guide", "role": "guide", "name": "<name>", "model": ""}}
  ],
  "milestones": [
    {{"week": <int>, "title": "<checkpoint>", "detail": "<what the learner can do by here>"}}
  ]
}}

Rules:
- 2-4 subjects, each 4-6 modules from foundations to mastery.
- Every module: 2-3 concrete objectives and one hands-on assignment whose
  sandbox fits the topic (SQL->"sql", coding->"python"/"git", data->"jupyter").
- Choose subject sandboxes by topic — do NOT default everything to "python".
- 3-5 milestones spread across the weeks.
- Ground objectives in the provided materials where relevant.
- Keep names short and human. Output ONLY the JSON object."""


def design_curriculum(provider: LLMProvider, goal: str, level: str,
                      materials: list[dict] | None = None) -> Curriculum:
    materials = materials or []
    user = (f"My goal: {goal.strip() or 'become job-ready in backend Python'}\n"
            f"My level: {level}\n\n" + _materials_block(materials))
    raw = provider.complete(SYSTEM, [{"role": "user", "content": user}], max_tokens=6000, json=True)
    data = _parse_json(raw)
    for f in data.get("faculty", []):
        if not f.get("model"):
            f["model"] = provider.model
    curriculum = Curriculum.model_validate(data)
    _attach_reading(curriculum, materials)
    curriculum.grounded = bool(materials)
    return curriculum


def _materials_block(materials: list[dict]) -> str:
    if not materials:
        return "No external materials were available — design from your own knowledge."
    lines = ["Real materials to ground the plan (cite these in reading lists):"]
    for m in materials[:12]:
        lines.append(f"- [{m.get('kind','web')}] {m.get('title','')} — {m.get('url','')}")
    return "\n".join(lines)


def _attach_reading(curriculum: Curriculum, materials: list[dict]):
    """Fill any empty module reading lists from the retrieved materials."""
    if not materials:
        return
    pool = [{"title": m.get("title", ""), "url": m.get("url", ""), "kind": m.get("kind", "web")}
            for m in materials if m.get("title")]
    if not pool:
        return
    i = 0
    for s in curriculum.subjects:
        for m in s.modules:
            if not m.reading:
                pick = pool[i % len(pool)]
                nxt = pool[(i + 1) % len(pool)]
                from ..schemas import Reading
                m.reading = [Reading(**pick)] + ([Reading(**nxt)] if nxt["url"] != pick["url"] else [])
                i += 1


def _parse_json(raw: str) -> dict:
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            pass
    raise ValueError("Principal did not return valid JSON curriculum")
