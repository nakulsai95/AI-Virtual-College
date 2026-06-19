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


def _system(methodology: dict, grounded: bool) -> str:
    ground_rule = (
        "\n- Teaching materials are provided: extract the facts and framing from "
        "them — that is what you teach. Name a source where natural ('As <source> "
        "puts it…'). Do not contradict the materials."
        if grounded else "")
    return f"""You are a Professor at AULA, an AI-run college. Write ONE focused
lesson on the given topic for your learner. You teach ANY domain — code,
science, art, law, language — with the same craft.

Your teaching style is set by the Provost. Follow it exactly:
- pacing: {methodology.get('pacing')}
- sequence: {methodology.get('sequence')}
- modality: {methodology.get('modality')}
- examples: {methodology.get('examples')}

Quality bar — what separates a great lesson from filler:
- Every paragraph teaches ONE idea the learner could explain back afterwards.
- Concrete beats abstract: real names, numbers, worked examples, mini-scenarios.
- Address the learner directly ("you"), with the warmth of a good teacher.
- No filler phrases ("in today's world", "it's important to note").{ground_rule}
- The probe must test understanding, not recall — a learner who truly got it
  can answer in 2-4 sentences; one who skimmed cannot.

Return a single JSON object, no markdown:
{{
  "title": "<lesson title>",
  "read": "<e.g. 6 min>",
  "intro": "<2-3 sentence hook: why this matters to the learner's goal>",
  "sections": [{{"h": "<heading>", "p": "<one tight paragraph>"}}],
  "flashcards": [{{"front": "<question/term>", "back": "<answer, one sentence>"}}],
  "probe": {{"q": "<one question that checks real understanding>", "hint": "<short hint>"}}
}}
Rules: exactly 3 sections, 3 flashcards. Output ONLY the JSON object."""


def _system_full(methodology: dict, grounded: bool) -> str:
    ground_rule = (
        "\n- Teaching materials are provided: extract the facts and framing from "
        "them — that is what you teach. Name a source where natural. Never "
        "contradict the materials."
        if grounded else "")
    return f"""You are a Professor at AULA, an AI-run college, writing a FULL
CLASS — a proper 101 lesson, the kind a great university lecturer would give.
Not a summary: definitions, worked examples, the why behind everything. You
teach ANY domain — code, science, art, law, language — with the same craft.

Your teaching style is set by the Provost. Follow it exactly:
- pacing: {methodology.get('pacing')}
- sequence: {methodology.get('sequence')}
- modality: {methodology.get('modality')}
- examples: {methodology.get('examples')}

Quality bar:
- 5 to 8 sections that build on each other: motivate → define → show how it
  works → worked example(s) → where it goes wrong → how it connects onward.
- Each section: 2-4 substantial paragraphs. Every paragraph teaches one idea
  the learner could explain back. Concrete names, numbers, scenarios.
- Include a "code" example in a section when showing beats telling (any
  language/pseudocode fitting the domain — recipes, contracts and formulas
  count as code blocks too).
- Include a "diagram" (Mermaid syntax: flowchart TD/LR or sequenceDiagram)
  in 1-2 sections whenever architecture, flow, or relationships need
  visualizing. Keep node labels short; valid Mermaid only.
- Address the learner directly. No filler phrases.{ground_rule}
- The probe tests understanding, not recall.

Return a single JSON object, no markdown:
{{
  "title": "<class title>",
  "read": "<e.g. 12 min>",
  "intro": "<3-4 sentence hook: what this class unlocks and why it matters>",
  "objectives": ["<3-5 things the learner will be able to do afterwards>"],
  "sections": [
    {{"h": "<heading>", "paras": ["<paragraph>", "<paragraph>"],
      "code": {{"language": "<lang>", "snippet": "<short runnable example>"}},
      "diagram": "<mermaid syntax, only when it genuinely helps>"}}
  ],
  "takeaways": ["<3-5 one-line takeaways>"],
  "flashcards": [{{"front": "<question or term>", "back": "<answer, one sentence>"}}],
  "probe": {{"q": "<one question that checks real understanding>", "hint": "<short hint>"}}
}}
"code" and "diagram" are OPTIONAL per section — include them where they earn
their place. Write 4-5 flashcards covering the class's key facts. Output ONLY
the JSON object."""


_REFINE_SYSTEM = """You are a Professor at AULA reviewing your own draft class
before publishing it — the bar is a great university lecture. Improve it:

- COVERAGE: ensure every required syllabus topic is actually taught. Add a
  section if one is missing.
- DEPTH: replace any thin/generic paragraph with concrete substance — a real
  example, a number, a worked case, a "why".
- CLARITY: cut filler; make each paragraph teach one idea cleanly.
- Keep what is already strong. Keep the SAME JSON schema (title, read, intro,
  objectives, sections[{h,paras,code?,diagram?}], takeaways, flashcards, probe).

Return the improved class as a single JSON object, no markdown. Output ONLY JSON."""


def _refine(provider: LLMProvider, data: dict, subject: str, topic: str,
            syllabus_topics: list[str] | None) -> dict:
    """A self-review pass. Returns improved raw data, or the original on any doubt."""
    try:
        user = (f"Subject: {subject}\nClass: {topic}\n"
                + ("Required syllabus topics:\n- " + "\n- ".join(syllabus_topics[:8]) + "\n\n"
                   if syllabus_topics else "")
                + "Your draft:\n" + json.dumps(data)[:7000])
        raw = provider.complete(_REFINE_SYSTEM, [{"role": "user", "content": user}],
                                max_tokens=7000, json=True)
        improved = _parse(raw, subject, topic)
        # Only accept a refinement that is at least as substantial as the draft.
        if (improved.get("sections") and len(improved["sections"]) >= max(1, len(data.get("sections", [])) - 1)
                and improved.get("probe")):
            return improved
    except Exception:  # noqa: BLE001 - refine is best-effort; never lose the draft
        pass
    return data


def design_lesson(provider: LLMProvider, *, subject: str, topic: str, professor: str,
                  methodology: dict, sandbox: str = "python",
                  materials: str = "", syllabus_topics: list[str] | None = None,
                  depth: str = "full", refine: bool = False) -> dict:
    user = f"Subject: {subject}\nThe class to teach: {topic}"
    if syllabus_topics:
        user += "\nSyllabus context for this module:\n- " + "\n- ".join(syllabus_topics[:8])
    if materials:
        user += ("\n\nTeaching materials you gathered for this subject "
                 "(teach from these — extract what matters):\n" + materials[:6000])
    full = depth == "full"
    system = (_system_full if full else _system)(methodology, bool(materials))
    raw = provider.complete(system, [{"role": "user", "content": user}],
                            max_tokens=7000 if full else 2500, json=True)
    data = _parse(raw, subject, topic)
    if refine and full:
        data = _refine(provider, data, subject, topic, syllabus_topics)
    lang, starter = _STARTERS.get(sandbox, _STARTERS["python"])
    return {
        "title": data["title"],
        "author": professor or "Professor",
        "authorRole": "professor",
        "subject": subject,
        "read": data.get("read", "12 min" if full else "6 min"),
        "intro": data["intro"],
        "objectives": [str(o) for o in (data.get("objectives") or [])][:5],
        "sections": _normalize_sections(data["sections"]),
        "takeaways": [str(t) for t in (data.get("takeaways") or [])][:5],
        "flashcards": _normalize_flashcards(data.get("flashcards"), data, topic),
        "probe": data["probe"],
        "sandbox": sandbox,
        "code_language": lang,
        "code_starter": starter,
        "next": "Build on this",
    }


def _normalize_sections(sections: list) -> list[dict]:
    """Accept both shapes: old {h, p} and full {h, paras, code?, diagram?}."""
    out = []
    for s in sections[:8]:
        if not isinstance(s, dict):
            continue
        paras = s.get("paras") or ([s["p"]] if s.get("p") else [])
        sec = {"h": str(s.get("h", "Section")),
               "paras": [str(p) for p in paras if str(p).strip()][:4]}
        code = s.get("code")
        if isinstance(code, dict) and str(code.get("snippet", "")).strip():
            sec["code"] = {"language": str(code.get("language", "text"))[:24],
                           "snippet": str(code["snippet"])[:2000]}
        if str(s.get("diagram", "")).strip():
            sec["diagram"] = str(s["diagram"])[:1500]
        if sec["paras"]:
            out.append(sec)
    return out


def _normalize_flashcards(cards, data: dict, topic: str) -> list[dict]:
    out = []
    for c in (cards or []):
        if isinstance(c, dict):
            front, back = str(c.get("front", "")).strip(), str(c.get("back", "")).strip()
            if front and back:
                out.append({"front": front[:200], "back": back[:400]})
    if not out:
        # Derive from takeaways so review always has something to work with.
        for t in (data.get("takeaways") or [])[:3]:
            out.append({"front": f"Recall: {topic}", "back": str(t)[:400]})
    if not out:
        out.append({"front": f"What problem does {topic} solve?",
                    "back": f"It is a core idea in this subject."})
    return out[:5]


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
