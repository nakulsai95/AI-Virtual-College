"""End-to-end smoke test against the real app (mock LLM provider, temp DB).

Run: .venv\\Scripts\\python.exe smoke_test.py
"""
from __future__ import annotations

import os
import sys
import tempfile

# Use a throwaway database so the test never touches the real college.
_tmp = tempfile.mkdtemp()
os.environ["AULA_TEST"] = "1"

from app import db  # noqa: E402
from pathlib import Path  # noqa: E402

db.DB_PATH = Path(_tmp) / "aula-test.db"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
FAILED = []


def check(name: str, cond: bool, detail: str = ""):
    status = "ok " if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


db.init_db()

# 1. health + providers
r = client.get("/api/health")
check("health", r.status_code == 200 and r.json()["status"] == "ok")

r = client.get("/api/connectors/providers")
ids = [p["id"] for p in r.json()["providers"]]
check("providers include mistral+gemini", "mistral" in ids and "gemini" in ids, str(ids))

# 2. state before enrolment
r = client.get("/api/state")
check("state pre-enrol", r.status_code == 200 and r.json()["enrolled"] is False)

# 3. onboard (mock principal)
r = client.post("/api/onboard", json={"goal": "Become job-ready in backend Python", "level": "intermediate"})
check("onboard", r.status_code == 200, r.text[:300])
cur = r.json()["curriculum"]
roles = {f["role"] for f in cur["faculty"]}
check("all 7 roles hired", {"principal", "provost", "professor", "examiner",
                            "registrar", "guide", "counselor"} <= roles, str(roles))

# 4. full state after enrolment
r = client.get("/api/state")
s = r.json()
check("state enrolled", s["enrolled"] is True)
check("state has subjects", len(s["SUBJECTS"]) >= 2)
check("state has faculty", len(s["FACULTY"]) >= 7)
check("state has channels", len(s["CHANNELS"]) >= 2)
check("state has mastery", len(s["MASTERY"]) >= 1 and len(s["MASTERY"][0]["concepts"]) >= 1)
check("state has next exam", s["NEXT_EXAM"] is not None, str(s.get("NEXT_EXAM")))
check("usage shape", "cap" in s["USAGE"] and "used" in s["USAGE"])
first_subject = s["SUBJECTS"][0]

# 5. guide -> routed lesson
r = client.post("/api/guide", json={"message": "I don't get how JWT auth works"})
check("guide ask", r.status_code == 200, r.text[:300])
g = r.json()
check("guide routed", bool(g["route"]["subject"]) and bool(g["route"]["professor"]))
check("guide lesson authored", bool(g["lesson"]["title"]) and g["lesson"]["id"] > 0)
lesson_id = g["lesson"]["id"]

# 6. lesson library + detail
r = client.get("/api/state")
check("library has lesson", len(r.json()["LIBRARY"]) >= 1)
check("kanban has lesson card", len(r.json()["KANBAN"]["lessons"]) >= 1)
r = client.get(f"/api/lessons/{lesson_id}")
check("lesson detail", r.status_code == 200 and r.json()["lesson"]["id"] == lesson_id)

# 7. direct lesson endpoint
r = client.post("/api/lesson", json={"subject": first_subject["title"], "topic": "indexes",
                                     "professor": first_subject["profName"], "sandbox": "python"})
check("author lesson", r.status_code == 200 and bool(r.json()["lesson"]["title"]))

# 8. probe grading + reward loop
probe_q = g["lesson"]["probe"]["q"]
r = client.post("/api/grade", json={"kind": "probe", "question": probe_q,
                                    "answer": "It carries signed claims so the server can verify identity without storing sessions.",
                                    "bar": 70, "subject": first_subject["title"],
                                    "professor": first_subject["profName"]})
check("grade probe", r.status_code == 200, r.text[:300])
gr = r.json()
check("probe reward applied", gr["reward"] is not None and "professor" in gr["reward"])

# failing answers until the provost rewrites
changed = False
for _ in range(6):
    r = client.post("/api/grade", json={"kind": "probe", "question": probe_q, "answer": "no",
                                        "bar": 70, "subject": first_subject["title"],
                                        "professor": first_subject["profName"]})
    if r.json().get("reward", {}).get("methodology_changed"):
        changed = True
        break
check("provost rewrite triggers on repeated failure", changed)

r = client.get("/api/state")
grades = r.json()["GRADES"]
check("methodology version bumped", any(p["version"] > 1 for p in grades),
      str([(p["name"], p["version"]) for p in grades]))
check("xp awarded", r.json()["STUDENT"]["xp"] > 0, str(r.json()["STUDENT"]["xp"]))

# 9. exams: generate -> submit -> module advances
mod = r.json()["NEXT_EXAM"]
r = client.post("/api/exams/generate", json={"module_id": mod["module_id"]})
check("exam generated", r.status_code == 200, r.text[:300])
exam = r.json()["exam"]
check("exam has questions", len(exam["questions"]) >= 3)

answers = ["A thorough, reasoned answer explaining the concept with an example and tradeoffs."] * len(exam["questions"])
r = client.post(f"/api/exams/{exam['id']}/submit", json={"answers": answers})
check("exam submitted", r.status_code == 200, r.text[:300])
res = r.json()
check("exam graded", isinstance(res["score"], int) and len(res["per_question"]) == len(exam["questions"]))

r = client.get("/api/state")
s = r.json()
exam_row = next(e for e in s["EXAMS"] if e["id"] == exam["id"])
check("exam recorded", exam_row["status"] in ("passed", "failed"), exam_row["status"])
if res["passed"]:
    subj = next(x for x in s["SUBJECTS"] if x["title"] == exam["subject"])
    statuses = [m["status"] for m in subj["modules"]]
    check("module advanced", "done" in statuses, str(statuses))

# 10. channels: send a DM, get a persona reply
ch = next(c for c in s["CHANNELS"] if c["kind"] == "dm")
r = client.post(f"/api/channel/{ch['id']}/messages", json={"text": "Can you give me a hint?"})
check("channel send", r.status_code == 200 and len(r.json()["messages"]) == 2, r.text[:300])

# 11. sandbox runs real code on Windows
r = client.post("/api/sandbox/run", json={"sandbox": "python", "code": "print(sum(range(10)))"})
check("python sandbox", r.status_code == 200 and "45" in r.json()["stdout"], r.text[:300])
r = client.post("/api/sandbox/run", json={"sandbox": "sql", "code": "SELECT name FROM users ORDER BY age LIMIT 1;"})
check("sql sandbox", r.status_code == 200 and "Yuki" in r.json()["stdout"], r.text[:300])

# 12. budget endpoints
r = client.get("/api/usage")
check("usage endpoint", r.status_code == 200 and "cap" in r.json())
r = client.put("/api/budget", json={"cap": 12.5})
check("budget set", r.status_code == 200 and r.json()["cap"] == 12.5)

# 13. feed shows the whole story
r = client.get("/api/state")
feed_text = " | ".join(f["text"] for f in r.json()["FEED"])
check("feed has reward events", "to " in feed_text or "passed" in feed_text, feed_text[:200])

print()
if FAILED:
    print(f"{len(FAILED)} FAILED: {FAILED}")
    sys.exit(1)
print("ALL CHECKS PASSED")
