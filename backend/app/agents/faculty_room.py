"""The Faculty Room — where the student's agents talk about their progress.

A coordinator builds a short, in-character conversation among the faculty
(Principal, Provost, Professors, Examiner) grounded in the live state: each
professor's grade and trend, recent reward events, and any methodology rewrite.
The learner can read along.
"""
from __future__ import annotations

import json
import re

_HUES = {"principal": "#6e8efb", "provost": "#46d6ad", "examiner": "#f0846b",
         "guide": "#9b6cff", "professor": "#f5a623"}

_SYSTEM = """You are orchestrating the Faculty Room of AULA, an AI college,
where the teaching agents discuss one student's progress. Speak in character,
concise and natural — like colleagues in a staff channel. Ground every line in
the provided state (grades, trends, recent events). Return a single JSON object:
{"messages": [{"who": "<name>", "role": "<principal|provost|professor|examiner>", "text": "<one short message>"}]}
4 to 6 messages, different speakers, building on each other. Output ONLY JSON."""


def discuss(provider, *, faculty: list[dict], professors: list[dict],
            feed: list[dict], mission: str) -> list[dict]:
    name_by_role = {f["role"]: f["name"] for f in faculty}
    if getattr(provider, "id", "") == "mock":
        return _scripted(professors, feed, name_by_role, mission)

    ctx = _context(professors, feed, mission)
    try:
        raw = provider.complete(_SYSTEM, [{"role": "user", "content": ctx}],
                                max_tokens=1400, json=True)
        data = _parse(raw)
        out = []
        for m in data.get("messages", [])[:6]:
            if not isinstance(m, dict) or not m.get("text"):
                continue
            role = (m.get("role") or "professor").lower()
            out.append({"who": m.get("who") or name_by_role.get(role, role.title()),
                        "role": role, "hue": _HUES.get(role, "#f5a623"), "text": m["text"]})
        if out:
            return out
    except Exception:  # noqa: BLE001
        pass
    return _scripted(professors, feed, name_by_role, mission)


def _context(professors, feed, mission) -> str:
    lines = [f"Student goal: {mission}", "", "Faculty grades:"]
    for p in professors:
        lines.append(f"- {p['name']} ({p['subject']}): {p['letter']} {p['score']}/100, "
                     f"trend {p['trend']}, methodology v{p['version']} — {p.get('note','')}")
    lines.append("")
    lines.append("Recent events:")
    for ev in feed[:6]:
        lines.append(f"- {ev['text']}")
    return "\n".join(lines)


def _scripted(professors, feed, name_by_role, mission) -> list[dict]:
    """State-driven fallback so the room is lively without an LLM."""
    msgs = []
    principal = name_by_role.get("principal", "Iroha")
    provost = name_by_role.get("provost", "Daichi")
    examiner = name_by_role.get("examiner", "Rei")

    # A professor opens with their own standing.
    if professors:
        p = professors[0]
        verb = {"up": "trending up", "down": "recovering", "flat": "holding steady"}.get(p["trend"], "steady")
        msgs.append({"who": p["name"], "role": "professor", "hue": _HUES["professor"],
                     "text": f"My {p['subject']} grade is {p['letter']} and {verb}. "
                             + ("The learner is getting it." if p["score"] >= 80 else "Working to lift retention.")})

    # Provost reacts to any methodology rewrite in the feed.
    rewrote = next((e for e in feed if "Rewrote" in e.get("text", "")), None)
    if rewrote:
        msgs.append({"who": provost, "role": "provost", "hue": _HUES["provost"],
                     "text": f"I just {rewrote['text'].split('·')[0].strip().lower()} — worked examples before theory should land better."})
    else:
        msgs.append({"who": provost, "role": "provost", "hue": _HUES["provost"],
                     "text": "Methodologies look well-calibrated. I'll watch the next exam before any changes."})

    # Examiner notes the latest assessment signal.
    exam_ev = next((e for e in feed if "Exam" in e.get("text", "") or "Probe" in e.get("text", "")), None)
    if exam_ev:
        msgs.append({"who": examiner, "role": "examiner", "hue": _HUES["examiner"],
                     "text": exam_ev["text"].split("·")[0].strip() + " — bar held at the standard."})

    # A second professor if present.
    if len(professors) > 1:
        p2 = professors[1]
        msgs.append({"who": p2["name"], "role": "professor", "hue": _HUES["professor"],
                     "text": f"On {p2['subject']}: I'll pair the next lesson with a hands-on task to reinforce it."})

    # Principal wraps up tied to the mission.
    msgs.append({"who": principal, "role": "principal", "hue": _HUES["principal"],
                 "text": f"Good. Keep the through-line to “{mission or 'the goal'}” — that's the signal that matters."})
    return msgs


def _parse(raw: str) -> dict:
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    raise ValueError("faculty room returned non-JSON")
