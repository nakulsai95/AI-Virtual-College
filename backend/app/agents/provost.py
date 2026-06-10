"""The Provost agent — rewrites a struggling professor's methodology.

Real reasoning, not a hardcoded flip: the Provost sees what the professor was
doing, what the learner got wrong, and writes a new teaching plan. Falls back
to the deterministic examples-first rewrite when no LLM is connected.
"""
from __future__ import annotations

import json
import re

from ..db import EXAMPLES_FIRST_METHODOLOGY
from ..llm.base import LLMProvider

_SYSTEM = """You are the Provost at AULA, an AI-run college. You own teaching
methodology across every subject and domain. A professor's student just failed
an assessment — the penalty landed on the professor (never the student), and
your job is to rewrite HOW that professor teaches so the student succeeds
next time.

Method: diagnose first, then prescribe.
1. From the failure context, infer the most likely cause: moved too fast?
   theory before practice? too few examples? probe asked before the idea
   could settle?
2. Change ONLY the levers that address that cause — keep what was working.
   A rewrite that changes everything teaches you nothing next time.

Return a single JSON object, no markdown:
{
  "methodology": {
    "pacing": "<slow|normal|fast>",
    "sequence": "<short phrase, e.g. 'examples → theory'>",
    "modality": "<short phrase, e.g. 'blog + worked examples'>",
    "examples": "<low|medium|high>",
    "probe": "<after-read|after-practice>"
  },
  "note": "<one sentence: what you changed and why — addressed to the learner, no blame>"
}
Output ONLY the JSON object."""


def rewrite(provider: LLMProvider, *, professor: dict, context: str) -> tuple[dict, str]:
    """Returns (new_methodology, note). Never raises — degrades to the default rewrite."""
    user = (
        f"Professor: {professor.get('name')}\n"
        f"Subject: {professor.get('subject')}\n"
        f"Current methodology: {json.dumps(professor.get('methodology', {}))}\n"
        f"Current grade: {professor.get('score')}/100\n"
        f"What went wrong: {context}"
    )
    try:
        raw = provider.complete(_SYSTEM, [{"role": "user", "content": user}],
                                max_tokens=600, json=True)
        data = _parse(raw)
        meth = data.get("methodology") or {}
        if not all(k in meth for k in ("pacing", "sequence", "modality", "examples", "probe")):
            raise ValueError("incomplete methodology")
        note = str(data.get("note", "")).strip() or "Methodology rewritten after a struggle."
        return meth, note
    except Exception:  # noqa: BLE001 - the rewrite must always land
        return dict(EXAMPLES_FIRST_METHODOLOGY), (
            "Provost rewrote the methodology after a struggle — "
            "worked examples now come before theory.")


def _parse(raw: str) -> dict:
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    raise ValueError("provost returned non-JSON")
