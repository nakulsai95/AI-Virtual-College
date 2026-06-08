"""Per-user college state (faculty grades, methodology versions, reward feed).

Loaded from / saved to the repo per request, so each user has their own faculty
and reward history. Seeded from the generated curriculum at onboarding; the
Examiner/Provost mutate it as the learner works.
"""
from __future__ import annotations

import time

from . import repo

DEFAULT_METHODOLOGY = {
    "pacing": "normal", "sequence": "concept → practice",
    "modality": "blog + diagrams", "examples": "medium", "probe": "after-read",
}
EXAMPLES_FIRST_METHODOLOGY = {
    "pacing": "slow", "sequence": "examples → theory",
    "modality": "blog + worked examples", "examples": "high", "probe": "after-practice",
}


class CollegeState:
    def __init__(self, data: dict | None = None):
        data = data or {}
        self.professors: dict[str, dict] = data.get("professors", {})
        self.feed: list[dict] = data.get("feed", [])

    # -- persistence -----------------------------------------------------
    @classmethod
    def load(cls, user_id: int) -> "CollegeState":
        return cls(repo.get_faculty(user_id))

    def save(self, user_id: int):
        repo.set_faculty(user_id, {"professors": self.professors, "feed": self.feed})

    def to_dict(self) -> dict:
        return {"professors": self.professors, "feed": self.feed}

    # -- lifecycle -------------------------------------------------------
    def init_from_curriculum(self, curriculum: dict):
        self.professors = {}
        self.feed = []
        for f in curriculum.get("faculty", []):
            if f.get("role") != "professor":
                continue
            pid = f.get("id") or f"prof-{len(self.professors)+1}"
            self.professors[pid] = {
                "id": pid, "name": f.get("name", "Professor"),
                "subject": f.get("subject", ""), "score": 78, "history": [78],
                "version": 1, "methodology": dict(DEFAULT_METHODOLOGY),
                "note": "Just hired — fresh methodology.",
            }
        self._log("Iroha", "College staffed — faculty hired.", "update")

    # -- lookup ----------------------------------------------------------
    def resolve_professor(self, *, professor_id: str = "", subject: str = "", name: str = "") -> dict | None:
        if professor_id and professor_id in self.professors:
            return self.professors[professor_id]
        for p in self.professors.values():
            if name and p["name"].lower() == name.lower():
                return p
            if subject and p["subject"].lower() == subject.lower():
                return p
        return next(iter(self.professors.values()), None)

    # -- mutation --------------------------------------------------------
    def reward(self, prof: dict, delta: int, reason: str) -> dict:
        prof["score"] = max(0, min(100, prof["score"] + delta))
        prof["history"] = (prof["history"] + [prof["score"]])[-10:]
        sign = f"+{delta}" if delta >= 0 else str(delta)
        self._log(prof["name"], f"{reason} · {sign} to {prof['name']}",
                  "pos" if delta >= 0 else "neg")
        return self._snap(prof)

    def rewrite_methodology(self, prof: dict) -> dict:
        prof["version"] += 1
        prof["methodology"] = dict(EXAMPLES_FIRST_METHODOLOGY)
        prof["note"] = (f"Provost rewrote methodology (v{prof['version']-1} → v{prof['version']}) "
                        "after a struggle — worked examples now come before theory.")
        self._log("Daichi", f"Rewrote {prof['name']}’s methodology · v{prof['version']-1} → v{prof['version']}", "update")
        return self._snap(prof)

    def log_lesson(self, prof_name: str, title: str):
        self._log(prof_name, f"Published lesson · “{title}”", "neutral")

    # -- snapshots -------------------------------------------------------
    def snapshot(self) -> dict:
        return {
            "professors": [self._snap(p) for p in self.professors.values()],
            "feed": list(self.feed[:12]),
            "has_curriculum": bool(self.professors),
        }

    def _snap(self, prof: dict) -> dict:
        score = prof["score"]
        letter = "A−" if score >= 86 else "B+" if score >= 76 else "C" if score >= 60 else "D"
        hist = prof["history"]
        trend = "up" if len(hist) > 1 and hist[-1] > hist[0] else "down" if len(hist) > 1 and hist[-1] < hist[0] else "flat"
        return {"id": prof["id"], "name": prof["name"], "subject": prof["subject"],
                "score": score, "letter": letter, "trend": trend, "version": prof["version"],
                "history": list(hist), "methodology": dict(prof["methodology"]), "note": prof["note"]}

    def _log(self, who: str, text: str, kind: str):
        self.feed.insert(0, {"t": time.strftime("%H:%M"), "who": who, "text": text, "kind": kind})
        self.feed = self.feed[:30]
