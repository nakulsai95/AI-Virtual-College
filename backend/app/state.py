"""In-process college state.

Single-user/dev model: one global CollegeState holds the faculty's live grades,
methodology versions, and the reward feed. Onboarding seeds it from the
generated curriculum; the Examiner/Provost mutate it as the learner works.

Not multi-user or durable — that's a roadmap item. Good enough to make the
reward loop real end to end.
"""
from __future__ import annotations

import threading
import time

DEFAULT_METHODOLOGY = {
    "pacing": "normal",
    "sequence": "concept → practice",
    "modality": "blog + diagrams",
    "examples": "medium",
    "probe": "after-read",
}

# What the Provost switches a struggling professor to.
EXAMPLES_FIRST_METHODOLOGY = {
    "pacing": "slow",
    "sequence": "examples → theory",
    "modality": "blog + worked examples",
    "examples": "high",
    "probe": "after-practice",
}


class CollegeState:
    def __init__(self):
        self._lock = threading.Lock()
        self.curriculum: dict | None = None
        self.professors: dict[str, dict] = {}
        self.feed: list[dict] = []

    # -- lifecycle -------------------------------------------------------
    def init_from_curriculum(self, curriculum: dict):
        with self._lock:
            self.curriculum = curriculum
            self.professors = {}
            self.feed = []
            for f in curriculum.get("faculty", []):
                if f.get("role") != "professor":
                    continue
                pid = f.get("id") or f"prof-{len(self.professors)+1}"
                self.professors[pid] = {
                    "id": pid,
                    "name": f.get("name", "Professor"),
                    "subject": f.get("subject", ""),
                    "score": 78,
                    "history": [78],
                    "version": 1,
                    "methodology": dict(DEFAULT_METHODOLOGY),
                    "note": "Just hired — fresh methodology.",
                }
            self._log("principal", "Iroha", "College staffed — faculty hired.", "update")

    # -- lookup ----------------------------------------------------------
    def resolve_professor(self, *, professor_id: str = "", subject: str = "", name: str = "") -> dict | None:
        with self._lock:
            if professor_id and professor_id in self.professors:
                return self.professors[professor_id]
            for p in self.professors.values():
                if name and p["name"].lower() == name.lower():
                    return p
                if subject and p["subject"].lower() == subject.lower():
                    return p
            # fall back to the first professor so the loop still demonstrates
            return next(iter(self.professors.values()), None)

    # -- mutation --------------------------------------------------------
    def reward(self, prof: dict, delta: int, reason: str, kind: str) -> dict:
        """Apply a reward signal to a professor (never to the student)."""
        with self._lock:
            prof["score"] = max(0, min(100, prof["score"] + delta))
            prof["history"] = (prof["history"] + [prof["score"]])[-10:]
            sign = f"+{delta}" if delta >= 0 else str(delta)
            self._log(
                prof["name"], prof["name"],
                f"{reason} · {sign} to {prof['name']}",
                "pos" if delta >= 0 else "neg",
            )
            return self._snapshot_prof(prof)

    def rewrite_methodology(self, prof: dict) -> dict:
        """Provost rewrites a struggling professor's approach (version bump)."""
        with self._lock:
            prof["version"] += 1
            prof["methodology"] = dict(EXAMPLES_FIRST_METHODOLOGY)
            prof["note"] = (
                f"Provost rewrote methodology (v{prof['version'] - 1} → v{prof['version']}) "
                "after a struggle — worked examples now come before theory."
            )
            self._log(
                "Daichi", "Daichi",
                f"Rewrote {prof['name']}’s methodology · v{prof['version']-1} → v{prof['version']}",
                "update",
            )
            return self._snapshot_prof(prof)

    def log_lesson(self, prof_name: str, title: str):
        with self._lock:
            self._log(prof_name, prof_name, f"Published lesson · “{title}”", "neutral")

    # -- snapshots -------------------------------------------------------
    def snapshot(self) -> dict:
        with self._lock:
            return {
                "professors": [self._snapshot_prof(p) for p in self.professors.values()],
                "feed": list(self.feed[:12]),
                "has_curriculum": self.curriculum is not None,
            }

    def _snapshot_prof(self, prof: dict) -> dict:
        score = prof["score"]
        letter = "A−" if score >= 86 else "B+" if score >= 76 else "C" if score >= 60 else "D"
        hist = prof["history"]
        trend = "up" if len(hist) > 1 and hist[-1] > hist[0] else "down" if len(hist) > 1 and hist[-1] < hist[0] else "flat"
        return {
            "id": prof["id"], "name": prof["name"], "subject": prof["subject"],
            "score": score, "letter": letter, "trend": trend,
            "version": prof["version"], "history": list(hist),
            "methodology": dict(prof["methodology"]), "note": prof["note"],
        }

    def _log(self, who: str, name: str, text: str, kind: str):
        # called with lock held
        self.feed.insert(0, {"t": _ago(), "who": who, "text": text, "kind": kind})
        self.feed = self.feed[:30]


def _ago() -> str:
    return time.strftime("%H:%M")


# Module-level singleton.
STATE = CollegeState()
