"""A curated catalogue of open, linkable learning resources.

Always available (no network), legally clean (we link, never copy). Buckets are
matched by keyword against the learner's goal/topic; a general bucket backstops.
"""
from __future__ import annotations

_BUCKETS = [
    (("python", "backend", "api", "flask", "django", "fastapi", "web server"), [
        {"title": "Python Official Tutorial", "url": "https://docs.python.org/3/tutorial/", "kind": "docs"},
        {"title": "Full Stack Python", "url": "https://www.fullstackpython.com/", "kind": "web"},
        {"title": "MIT 6.0001 — Intro to CS & Programming in Python (OCW)", "url": "https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/", "kind": "course"},
        {"title": "FastAPI Documentation", "url": "https://fastapi.tiangolo.com/", "kind": "docs"},
    ]),
    (("sql", "database", "databases", "postgres", "data engineering", "relational"), [
        {"title": "OpenStax / Open SQL — SQLBolt interactive", "url": "https://sqlbolt.com/", "kind": "course"},
        {"title": "PostgreSQL Documentation", "url": "https://www.postgresql.org/docs/", "kind": "docs"},
        {"title": "CMU 15-445 Database Systems (open lectures)", "url": "https://15445.courses.cs.cmu.edu/", "kind": "course"},
    ]),
    (("react", "frontend", "javascript", "typescript", "ui"), [
        {"title": "React Official Docs (Learn)", "url": "https://react.dev/learn", "kind": "docs"},
        {"title": "MDN Web Docs — JavaScript", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript", "kind": "docs"},
        {"title": "freeCodeCamp — Front End Libraries", "url": "https://www.freecodecamp.org/learn/front-end-development-libraries/", "kind": "course"},
    ]),
    (("machine learning", "ml", "deep learning", "neural", "ai", "data science", "pandas"), [
        {"title": "Stanford CS229 — Machine Learning (open notes)", "url": "https://cs229.stanford.edu/", "kind": "course"},
        {"title": "fast.ai — Practical Deep Learning", "url": "https://course.fast.ai/", "kind": "course"},
        {"title": "scikit-learn User Guide", "url": "https://scikit-learn.org/stable/user_guide.html", "kind": "docs"},
        {"title": "OpenStax — Introductory Statistics", "url": "https://openstax.org/details/books/introductory-statistics", "kind": "book"},
    ]),
    (("math", "calculus", "linear algebra", "statistics", "probability"), [
        {"title": "MIT 18.06 Linear Algebra (OCW)", "url": "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/", "kind": "course"},
        {"title": "OpenStax — Calculus", "url": "https://openstax.org/details/books/calculus-volume-1", "kind": "book"},
        {"title": "Khan Academy — Math", "url": "https://www.khanacademy.org/math", "kind": "course"},
    ]),
]

_GENERAL = [
    {"title": "MIT OpenCourseWare", "url": "https://ocw.mit.edu/", "kind": "course"},
    {"title": "OpenStax — free, peer-reviewed textbooks", "url": "https://openstax.org/subjects", "kind": "book"},
    {"title": "freeCodeCamp", "url": "https://www.freecodecamp.org/learn/", "kind": "course"},
]


def search(query: str, n: int = 6) -> list[dict]:
    q = (query or "").lower()
    items: list[dict] = []
    for keys, bucket in _BUCKETS:
        if any(k in q for k in keys):
            items.extend(bucket)
    if not items:
        items = list(_GENERAL)
    seen, out = set(), []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        out.append({**it, "snippet": "Open resource", "source": "open-index"})
        if len(out) >= n:
            break
    return out
