"""Sandbox execution.

Runs learner code in the environment a subject mounts. Two real backends today:
  - python : isolated subprocess (`python3 -I`) with a wall-clock + CPU + memory
             cap and bounded output. Best-effort isolation for local dev — NOT a
             hardened multi-tenant sandbox. Don't expose this to the public
             internet without container/network isolation.
  - sql    : in-memory SQLite seeded with a small `users` table.

Other sandbox ids (git, jupyter, shell, web-search) map onto these or report
"not yet wired" rather than pretending to run.
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import time

SUPPORTED = ["python", "sql"]

_TIMEOUT_S = 6
_MAX_OUTPUT = 20_000  # chars
_MEM_BYTES = 256 * 1024 * 1024


def run_code(sandbox: str, code: str) -> dict:
    sandbox = (sandbox or "python").lower()
    code = code or ""
    if sandbox in ("python", "jupyter", "git", "shell"):
        return _run_python(code)
    if sandbox == "sql":
        return _run_sql(code)
    return {
        "ok": False, "stdout": "", "duration_ms": 0,
        "stderr": f"Sandbox '{sandbox}' is recognised but not wired for execution yet.",
    }


# --- Python -------------------------------------------------------------

def _limits():  # pragma: no cover - POSIX preexec, exercised at runtime
    try:
        import resource
        cpu = _TIMEOUT_S + 1
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
        resource.setrlimit(resource.RLIMIT_AS, (_MEM_BYTES, _MEM_BYTES))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1_000_000, 1_000_000))
    except Exception:
        pass


def _run_python(code: str) -> dict:
    start = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "main.py")
        with open(path, "w") as f:
            f.write(code)
        try:
            proc = subprocess.run(
                [sys.executable, "-I", path],
                capture_output=True, text=True, timeout=_TIMEOUT_S,
                cwd=tmp, env={"PATH": "/usr/bin:/bin", "PYTHONIOENCODING": "utf-8"},
                preexec_fn=_limits if os.name == "posix" else None,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "stdout": "", "stderr": f"⏱ Timed out after {_TIMEOUT_S}s.",
                    "duration_ms": int((time.monotonic() - start) * 1000)}

    return {
        "ok": proc.returncode == 0,
        "stdout": _clip(proc.stdout),
        "stderr": _clip(proc.stderr),
        "duration_ms": int((time.monotonic() - start) * 1000),
    }


# --- SQL ----------------------------------------------------------------

_SEED = """
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER);
INSERT INTO users (name, age) VALUES
  ('Alex', 27), ('Mei', 31), ('Kenji', 24), ('Sora', 38), ('Yuki', 22);
"""


def _run_sql(code: str) -> dict:
    import sqlite3
    start = time.monotonic()
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(_SEED)
        out = io.StringIO()
        # Execute possibly several statements; show rows for the last SELECT.
        last = None
        for stmt in [s.strip() for s in code.split(";") if s.strip()]:
            cur = conn.execute(stmt)
            if cur.description:  # a SELECT
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()
                last = (cols, rows)
        if last:
            cols, rows = last
            out.write(" | ".join(cols) + "\n")
            out.write("-" * (len(" | ".join(cols))) + "\n")
            for r in rows[:200]:
                out.write(" | ".join(str(v) for v in r) + "\n")
            out.write(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")
        else:
            out.write("OK — no rows returned.")
        return {"ok": True, "stdout": _clip(out.getvalue()), "stderr": "",
                "duration_ms": int((time.monotonic() - start) * 1000)}
    except sqlite3.Error as e:
        return {"ok": False, "stdout": "", "stderr": f"SQL error: {e}",
                "duration_ms": int((time.monotonic() - start) * 1000)}
    finally:
        conn.close()


def _clip(s: str) -> str:
    s = s or ""
    return s if len(s) <= _MAX_OUTPUT else s[:_MAX_OUTPUT] + "\n… (truncated)"
