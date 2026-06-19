"""The Lab agent — turns a class into an interactive game you learn by playing.

One engineered, domain-generic prompt produces a playable exercise spec. The
frontend has a generic renderer per kind, so any subject — code, law, biology,
music — gets a real game, not a worksheet. Generated on demand (cached in the
DB), so it never adds to the content-factory cost.
"""
from __future__ import annotations

import json
import re

from ..llm.base import LLMProvider

_SYSTEM = """You are the Lab Designer at AULA, an AI-run college. Turn the given
class into ONE small GAME the learner LEARNS THE CONCEPT BY PLAYING. The test:
someone who knew nothing should understand the idea BETTER after playing —
because the teaching is woven into the play (every step/choice explains the
why). This is not a test at the end of learning; it IS the learning. Any domain.

Pick the kind that best TEACHES this concept:
- "sort": an arcade game — items must be dropped into the right CATEGORY bucket
  against the clock; each reveals why. Best for taxonomies, classification,
  "which type is this", grouping rules.
- "steps": walk the learner through how something works, ONE stage at a time.
  At each stage they PREDICT what happens next, then you reveal and explain.
  Best for processes, mechanisms, algorithms, cause-and-effect, "how X works".
- "scenario": put the learner in realistic situations; each choice reveals its
  consequence and the reasoning. Best for judgment, tradeoffs, "when to use X".
- "match": connect related things (term ↔ meaning, cause ↔ effect). Best for
  vocabulary and relationships.
- "order": arrange steps into the correct sequence. Best for pipelines/procedures.
- "quiz": 4-6 questions, each with a one-sentence teaching explanation. Use only
  when the concept is purely factual recall.
- "bugfix": fix a broken snippet (ONLY for programming topics).

Prefer "steps" or "scenario" — they teach best. Return a single JSON object, no
markdown, matching the chosen kind:
{
  "kind": "sort|steps|scenario|match|order|quiz|bugfix",
  "title": "<short lab title>",
  "intro": "<1 sentence: what the learner will figure out>",
  // sort (arcade — drop items into category buckets):
  "categories": ["<bucket A>", "<bucket B>", "..."],
  "items": [{"text": "<thing to classify>", "category": "<exact bucket name>", "why": "<teach the rule>"}],
  // steps (predict → reveal → explain):
  "steps": [{"stage": "<what's happening now>",
             "predict": {"q": "What happens next?", "options": ["...","..."], "answer": <index>},
             "reveal": "<what actually happens AND why — the teaching>"}],
  // scenario (decide → learn):
  "rounds": [{"situation": "<a concrete situation>",
              "choices": [{"text": "...", "correct": <true|false>, "why": "<teach the reasoning>"}]}],
  // match:
  "pairs": [{"left": "...", "right": "..."}],
  // order:
  "prompt": "<what to order>", "ordered": ["step1","step2","... CORRECT order"],
  "explain": "<why this order>",
  // quiz:
  "questions": [{"q": "...", "options": ["a","b","c","d"], "answer": <index>, "explain": "..."}],
  // bugfix:
  "language": "python", "broken_code": "<code with a bug>", "task": "<what to fix>",
  "check": "<a substring that must appear in correct output>"
}
Include ONLY the fields for the kind you chose. 4-6 steps/rounds/questions.
Output ONLY the JSON object."""


def design_lab(provider: LLMProvider, *, subject: str, topic: str,
               materials: str = "", sandbox: str = "python") -> dict:
    user = f"Subject: {subject}\nClass topic: {topic}\nPractice environment: {sandbox}"
    if materials:
        user += "\n\nWhat this class taught (base the lab on this):\n" + materials[:2500]
    try:
        raw = provider.complete(_SYSTEM, [{"role": "user", "content": user}],
                                max_tokens=2000, json=True)
        spec = _sanitize(_parse(raw), topic, sandbox)
        if spec:
            return spec
    except Exception:  # noqa: BLE001 - a lab is never worth a 500
        pass
    return _fallback_quiz(topic)


def _sanitize(data: dict, topic: str, sandbox: str) -> dict | None:
    kind = str(data.get("kind", "")).lower()
    title = str(data.get("title", "")).strip() or f"{topic} lab"
    intro = str(data.get("intro", "")).strip()
    if kind == "sort":
        cats = [str(c).strip() for c in (data.get("categories") or []) if str(c).strip()]
        items = []
        for it in data.get("items", []):
            t = str(it.get("text", "")).strip()
            cat = str(it.get("category", "")).strip()
            if t and cat in cats:
                items.append({"text": t, "category": cat, "why": str(it.get("why", "")).strip()})
        if 2 <= len(cats) <= 4 and len(items) >= 4:
            return {"kind": "sort", "title": title, "intro": intro,
                    "categories": cats, "items": items[:10]}
    elif kind == "steps":
        steps = []
        for s in data.get("steps", []):
            stage = str(s.get("stage", "")).strip()
            reveal = str(s.get("reveal", "")).strip()
            if not (stage and reveal):
                continue
            step = {"stage": stage, "reveal": reveal}
            p = s.get("predict")
            if isinstance(p, dict):
                opts = [str(o) for o in (p.get("options") or []) if str(o).strip()]
                ans = p.get("answer", 0)
                if len(opts) >= 2 and isinstance(ans, int) and 0 <= ans < len(opts):
                    step["predict"] = {"q": str(p.get("q", "What happens next?")).strip(),
                                       "options": opts[:4], "answer": ans}
            steps.append(step)
        if len(steps) >= 3:
            return {"kind": "steps", "title": title, "intro": intro, "steps": steps[:6]}
    elif kind == "scenario":
        rounds = []
        for r in data.get("rounds", []):
            sit = str(r.get("situation", "")).strip()
            choices = []
            for ch in (r.get("choices") or []):
                t = str(ch.get("text", "")).strip()
                if t:
                    choices.append({"text": t, "correct": bool(ch.get("correct")),
                                    "why": str(ch.get("why", "")).strip()})
            if sit and len(choices) >= 2 and any(c["correct"] for c in choices):
                rounds.append({"situation": sit, "choices": choices[:4]})
        if len(rounds) >= 3:
            return {"kind": "scenario", "title": title, "intro": intro, "rounds": rounds[:6]}
    elif kind == "quiz":
        qs = []
        for q in data.get("questions", []):
            opts = [str(o) for o in (q.get("options") or []) if str(o).strip()]
            ans = q.get("answer", 0)
            if len(opts) >= 2 and isinstance(ans, int) and 0 <= ans < len(opts):
                qs.append({"q": str(q.get("q", "")).strip(), "options": opts[:6],
                           "answer": ans, "explain": str(q.get("explain", "")).strip()})
        if qs:
            return {"kind": "quiz", "title": title, "intro": intro, "questions": qs[:6]}
    elif kind == "match":
        pairs = [{"left": str(p.get("left", "")).strip(), "right": str(p.get("right", "")).strip()}
                 for p in data.get("pairs", [])
                 if str(p.get("left", "")).strip() and str(p.get("right", "")).strip()]
        if len(pairs) >= 3:
            return {"kind": "match", "title": title, "intro": intro, "pairs": pairs[:7]}
    elif kind == "order":
        steps = [str(s).strip() for s in (data.get("ordered") or data.get("steps") or []) if str(s).strip()]
        if len(steps) >= 3:
            return {"kind": "order", "title": title, "intro": intro,
                    "prompt": str(data.get("prompt", "")).strip() or "Put these in order:",
                    "steps": steps[:7], "explain": str(data.get("explain", "")).strip()}
    elif kind == "bugfix":
        broken = str(data.get("broken_code", "")).strip()
        if broken:
            return {"kind": "bugfix", "title": title, "intro": intro,
                    "language": str(data.get("language", sandbox))[:24],
                    "broken_code": broken[:2000], "task": str(data.get("task", "")).strip(),
                    "check": str(data.get("check", "")).strip()}
    return None


_GAME_SYSTEM = """You are the Game Designer at AULA, an AI-run college. Build ONE
small but genuinely PLAYABLE browser game that teaches the given concept BY
PLAYING IT — arcade style (move, collect, dodge, time, aim, build), in the
spirit of a simple NES/Flash game. This is NOT a quiz and NOT multiple choice.

You MAY clone a well-known simple arcade mechanic and reskin it so the content
teaches the concept — e.g. a catcher, endless runner, platform-jumper (Mario-
like), Snake, Breakout, Whack-a-mole, or maze. Proven mechanics play better.

The mechanic must EMBODY the concept: the player wins by acting on the idea
correctly. Examples of the *shape*:
- collect the items that belong, dodge the ones that don't
- a runner where you jump the correct gaps / hit the correct blocks
- guide a value/packet along the correct path through a maze
- stack/build pieces in the right order before time runs out

STORY: this game is one CHAPTER in the learner's ongoing adventure through the
course. If a story-so-far and a next concept are given, open by acknowledging
the journey, theme the level around it, and END by teasing the next chapter —
so the adventure flows from topic to topic.

Output a SINGLE self-contained HTML document that runs entirely on its own:
- One <canvas> and a vanilla-JS game loop (requestAnimationFrame). NO external
  files, libraries, fonts, images, or network calls of any kind.
- Keyboard controls (Arrow keys and/or Space). Print the controls on screen.
- A visible title, live score, and a clear WIN/LOSE end screen.
- Brief on-screen "why" feedback when the player does the concept-action right
  or wrong, so playing teaches the idea.
- When the game ends, post the result to the host exactly like this:
    parent.postMessage({aula:'score', value: SCORE_0_TO_100}, '*')
- Keep it tight (~150 lines) and make sure it actually runs with no errors.

Return a single JSON object, no markdown:
{"kind":"arcade","title":"<game name>","goal":"<how playing teaches the concept>",
 "controls":"<e.g. ← → to move, Space to jump>","html":"<!doctype html> ... full game ..."}
Output ONLY the JSON object."""


def design_arcade(provider, *, subject: str, topic: str, materials: str = "",
                  next_topic: str = "", story: str = "") -> dict | None:
    """Author a self-contained playable HTML5 game, framed as a chapter in the
    learner's continuing adventure. None if it doesn't come out runnable."""
    user = f"Subject (this world): {subject}\nConcept to turn into a game (this chapter): {topic}"
    if story:
        user += f"\nStory so far: {story}"
    if next_topic:
        user += f"\nNext chapter (tease it at the end): {next_topic}"
    if materials:
        user += "\n\nWhat the class taught (base the game's content on this):\n" + materials[:2000]
    try:
        raw = provider.complete(_GAME_SYSTEM, [{"role": "user", "content": user}],
                                max_tokens=4000, json=True)
        data = _parse(raw)
        html = str(data.get("html", "")).strip()
        # Must be a real, self-contained, runnable canvas game that reports a score.
        low = html.lower()
        if ("<canvas" in low and "<script" in low and "postmessage" in low
                and len(html) > 400):
            return {"kind": "arcade", "title": str(data.get("title", "")).strip() or f"{topic} game",
                    "goal": str(data.get("goal", "")).strip(),
                    "controls": str(data.get("controls", "Arrow keys")).strip(),
                    "html": html[:24000]}
    except Exception:  # noqa: BLE001 - fall back to a structured lab
        pass
    return None


def _fallback_quiz(topic: str) -> dict:
    return {
        "kind": "quiz", "title": f"{topic} — quick check",
        "intro": "Answer to lock in the idea.",
        "questions": [
            {"q": f"What is the main purpose of {topic}?",
             "options": ["It solves a real problem in this subject",
                         "It has no practical use", "It is only theoretical",
                         "It replaces the whole subject"],
             "answer": 0, "explain": f"{topic} exists to solve a concrete problem."},
            {"q": "Best way to truly learn it?",
             "options": ["Memorize the definition", "Work an example and explain it back",
                         "Skip the basics", "Read once quickly"],
             "answer": 1, "explain": "Active recall and worked examples beat rote reading."},
        ],
    }


def _parse(raw: str) -> dict:
    raw = (raw or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    raise ValueError("lab returned non-JSON")
