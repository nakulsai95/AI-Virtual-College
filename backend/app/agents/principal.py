"""The Principal (Orchestrator) agent.

Three responsibilities, all grounded in research on how real universities
teach the topic:
  1. design_curriculum — subjects, module sequence, sandboxes, faculty.
  2. validate_curriculum — a quality pass comparing the draft against real
     syllabi, filling important gaps.
  3. plan_board — break the learning path into the learner's kanban plan.

All prompts are domain-generic: the college must work as well for pottery or
contract law as for backend Python.
"""
from __future__ import annotations

import json
import re

from ..llm.base import LLMProvider
from ..schemas import Curriculum, Module

# Allowed sandbox ids the Principal may mount per subject. This is the
# topic/semester-driven sandbox catalogue the user asked for.
SANDBOXES = ["python", "sql", "git", "web-search", "jupyter", "shell", "notebook"]

SYSTEM = f"""You are the Principal of AULA, an AI-run college. A learner tells
you their goal; you design the entire institution around it.

Operating principles — these define your craft:
- You design for ANY domain: programming, science, art, business, language,
  law, fitness. Never assume the goal is about coding.
- Think like the curriculum director of a top university: define the outcome,
  then the SHORTEST sequence of subjects and modules that truly reaches it.
- Modules are concrete and assessable ("Model a schema in 3NF", "Brief a
  contract dispute") — never vague ("Learn more about databases").
- Order modules foundations → application → mastery; each builds on the last.
- If research with university syllabi is provided, mirror what real programs
  cover and in what order — that is your evidence base.
- Practice environments: pick per subject ONLY what fits, from {SANDBOXES}.
  Code topics -> "python"/"sql"/"git"; data -> "jupyter"; theory, writing or
  non-technical domains -> "web-search"/"notebook". Never default everything
  to "python".

Return a single JSON object with EXACTLY this shape (no markdown, no commentary):

{{
  "mission": "<one-line restatement of their goal>",
  "level": "beginner|intermediate|advanced",
  "weeks": <integer 16-32>,
  "summary": "<2-3 sentences: the plan and why this sequence>",
  "subjects": [
    {{
      "id": "s1",
      "title": "<subject name>",
      "professor": "<a short first name>",
      "sandboxes": [<1-3 ids from the catalogue>],
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
- THIS IS A FULL UNIVERSITY: 6 to 8 subjects, each with 8 to 12 modules.
  Hundreds of classes will be authored from this plan — design the complete
  degree-level path, not a tutorial. If the learner names extra areas (e.g.
  "also AWS"), they get their own subject.
- Module titles read like a university course catalog ("Indexing strategies
  and query plans"), specific enough that a professor knows exactly what to
  teach. Detailed per-module topics are written in a later pass — titles only.
- One professor per subject; include them in faculty with role "professor".
- Keep names short and human. Output ONLY the JSON object."""


def design_curriculum(provider: LLMProvider, goal: str, level: str,
                      research: str = "") -> Curriculum:
    user = f"My goal: {goal.strip() or 'become job-ready in backend Python'}\nMy level: {level}"
    if research:
        user += (
            "\n\nResearch on how universities teach this (your evidence base — "
            "mirror its coverage and ordering):\n" + research[:3500])
    raw = provider.complete(SYSTEM, [{"role": "user", "content": user}], max_tokens=8000, json=True)
    data = _parse_json(raw)
    # Stamp the connected model onto every faculty member for the Command Center.
    for f in data.get("faculty", []):
        if not f.get("model"):
            f["model"] = provider.model
    return Curriculum.model_validate(data)


# --- validation pass: the plan vs what universities actually teach -----------

_VALIDATE_SYSTEM = """You are the Principal of AULA running a final quality pass
on a draft curriculum. Compare it against the university-syllabus research
provided: would a strong program consider this coverage complete?

Identify up to 4 important topics that real programs teach for this goal but
the draft misses. Only flag genuinely important gaps — an empty list is a
good answer when coverage is solid.

Return a single JSON object, no markdown:
{
  "aligned": <true|false>,
  "note": "<one sentence on how the plan compares to real programs>",
  "additions": [{"subject": "<existing subject id>", "module": "<missing topic as a concrete module title>"}]
}
Output ONLY the JSON object."""


def validate_curriculum(provider: LLMProvider, curriculum: Curriculum,
                        research: str) -> tuple[Curriculum, str, int]:
    """Quality pass — returns (curriculum, note, modules_added). Never raises."""
    try:
        payload = {"subjects": [
            {"id": s.id, "title": s.title, "modules": [m.title for m in s.modules]}
            for s in curriculum.subjects]}
        user = (f"Draft curriculum:\n{json.dumps(payload)}\n\n"
                f"University research:\n{research[:3000]}")
        raw = provider.complete(_VALIDATE_SYSTEM, [{"role": "user", "content": user}],
                                max_tokens=700, json=True)
        data = _parse_json(raw)
        added = 0
        for add in (data.get("additions") or [])[:4]:
            subj = next((s for s in curriculum.subjects
                         if s.id == str(add.get("subject", "")).strip()), None)
            title = str(add.get("module", "")).strip()
            if subj and title and all(m.title.lower() != title.lower()
                                      for m in subj.modules):
                subj.modules.append(Module(id=f"{subj.id}m{len(subj.modules)+1}",
                                           title=title))
                added += 1
        note = str(data.get("note", "")).strip()
        return curriculum, note, added
    except Exception:  # noqa: BLE001 - validation must never block onboarding
        return curriculum, "", 0


# --- batch-wise syllabus detailing: one subject at a time ---------------------
# Generation stays small and reliable: the design pass writes module titles;
# this pass (one call per subject) expands each module into detailed topics.

_SYLLABUS_SYSTEM = """You are the Principal of AULA writing the detailed academic
syllabus for ONE subject — the way a university course catalog does it.

For EVERY module given, break it into 5 to 8 detailed topics: the specific
concepts, techniques, and skills that module teaches. Each topic becomes a
full class with its own lesson. The craft:
- Topics are precise ("Connection pooling and the N+1 problem"), never
  generic ("Advanced topics", "More practice").
- Together, the topics ARE the module — complete coverage, no overlap
  between modules.
- Works for any domain: code, science, law, art, language.

Return a single JSON object, no markdown:
{"modules": [{"id": "<module id>", "topics": ["<topic>", "..."]}]}
Include every module id you were given. Output ONLY the JSON object."""


def detail_subject_syllabus(provider: LLMProvider, *, subject_title: str,
                            modules: list[dict]) -> dict[str, list[str]]:
    """Expand one subject's modules into detailed topics. {} on failure."""
    try:
        payload = [{"id": m["id"], "title": m["title"]} for m in modules]
        user = f"Subject: {subject_title}\nModules:\n{json.dumps(payload)}"
        raw = provider.complete(_SYLLABUS_SYSTEM, [{"role": "user", "content": user}],
                                max_tokens=3000, json=True)
        data = _parse_json(raw)
        out: dict[str, list[str]] = {}
        for m in data.get("modules", []):
            mid = str(m.get("id", "")).strip()
            topics = [str(t).strip() for t in (m.get("topics") or []) if str(t).strip()]
            if mid and topics:
                out[mid] = topics[:8]
        return out
    except Exception:  # noqa: BLE001 - detailing is additive, never blocking
        return {}


# --- the Head's board plan: break the path into executable work --------------

_PLAN_SYSTEM = """You are the Principal of AULA planning the learner's kanban
board: break the whole curriculum into a realistic working plan a student can
execute, week by week. This works for ANY domain — practice means hands-on
work appropriate to the subject (code in a sandbox, drills, drafting,
analysis), not necessarily programming.

Card rules:
- For each subject's CURRENT (first) module: one "project" card in col
  "doing" — a concrete hands-on task using the subject's practice
  environment. Set "tool": true and name the environment in "meta".
- For EVERY later module: one "plan" card in col "lessons" with a target
  week in "meta" (pace evenly across the semester), "tool": false.
- Do NOT create reading cards — lessons land on the board automatically.
- Titles are specific actions ("Normalize the orders schema"), never labels.

Return a single JSON object, no markdown:
{"cards": [{"col": "doing|lessons", "type": "project|plan",
            "title": "<specific action>", "subject": "<subject title>",
            "meta": "<'python sandbox' or 'planned · Wk 5'>",
            "tool": <true|false>}]}
Output ONLY the JSON object."""


def plan_board(provider: LLMProvider, *, subjects: list[dict], weeks: int) -> list[dict]:
    """The Head breaks the curriculum into board cards. Returns [] on failure
    (caller falls back to the deterministic plan)."""
    try:
        payload = [{"title": s["title"], "sandboxes": s["sandboxes"],
                    "modules": s["modules"]} for s in subjects]
        user = (f"Semester length: {weeks} weeks\n"
                f"Curriculum:\n{json.dumps(payload)}")
        raw = provider.complete(_PLAN_SYSTEM, [{"role": "user", "content": user}],
                                max_tokens=1800, json=True)
        data = _parse_json(raw)
        cards = []
        titles = {s["title"] for s in subjects}
        for c in (data.get("cards") or [])[:24]:
            col = c.get("col") if c.get("col") in ("doing", "lessons") else "lessons"
            type_ = c.get("type") if c.get("type") in ("project", "plan", "task") else "plan"
            title = str(c.get("title", "")).strip()
            subject = str(c.get("subject", "")).strip()
            if title and subject in titles:
                cards.append({"col": col, "type": type_, "title": title[:90],
                              "subject": subject, "meta": str(c.get("meta", ""))[:60],
                              "tool": bool(c.get("tool"))})
        return cards
    except Exception:  # noqa: BLE001
        return []


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
