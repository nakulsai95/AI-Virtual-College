"""Sandbox execution.

Runs learner code in the environment a subject mounts. Two real backends:
  - python : subprocess running a harness that disables network access, then
             executes the user's code. Wrapped in an OS sandbox (bubblewrap /
             firejail / nsjail) when one is available for real filesystem + net
             isolation; otherwise a resource-limited subprocess (CPU, memory,
             file size, wall-clock) with the in-process network block.
  - sql    : in-memory SQLite seeded with a small `users` table.

Layered defence:
  1. OS sandbox (bwrap/firejail/nsjail) — real fs + net namespaces, if present.
  2. Network block harness — sockets raise inside the interpreter regardless.
  3. rlimits — CPU, address space, file size caps.
  4. Wall-clock timeout + bounded output.

Honest scope: without an OS sandbox installed this is a soft boundary suitable
for local single-user dev, not hardened multi-tenant isolation. Install
bubblewrap (or firejail/nsjail) on the host to get real isolation, or run the
backend itself inside a locked-down container before exposing it.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time

SUPPORTED = ["python", "sql"]

_TIMEOUT_S = 6
_MAX_OUTPUT = 20_000  # chars
_MEM_BYTES = 256 * 1024 * 1024

# Harness: disable network, then run the user's file so tracebacks point at it.
_HARNESS = """\
import sys
try:
    import socket
    def _blocked(*a, **k):
        raise OSError("network is disabled in the AULA sandbox")
    socket.socket = _blocked
    socket.create_connection = _blocked
    socket.create_server = _blocked
except Exception:
    pass
import runpy
runpy.run_path("main.py", run_name="__main__")
"""


def run_code(sandbox: str, code: str) -> dict:
    sandbox = (sandbox or "python").lower()
    code = code or ""
    if sandbox in ("python", "jupyter", "git", "shell"):
        return _run_python(code)
    if sandbox == "sql":
        return _run_sql(code)
    return {"ok": False, "stdout": "", "duration_ms": 0,
            "stderr": f"Sandbox '{sandbox}' is recognised but not wired for execution yet."}


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


def _sandbox_prefix(workdir: str) -> list[str]:
    """Wrap the interpreter in an OS sandbox if one is installed."""
    if shutil.which("bwrap"):
        return [
            "bwrap", "--unshare-all", "--die-with-parent", "--new-session",
            "--ro-bind", "/usr", "/usr", "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/lib", "/lib", "--ro-bind", "/lib64", "/lib64",
            "--proc", "/proc", "--dev", "/dev",
            "--bind", workdir, workdir, "--chdir", workdir,
        ]
    if shutil.which("firejail"):
        return ["firejail", "--quiet", "--net=none", "--private=" + workdir,
                "--rlimit-as=" + str(_MEM_BYTES)]
    if shutil.which("nsjail"):
        return ["nsjail", "--quiet", "--disable_proc", "--iface_no_lo",
                "--cwd", workdir, "--really_quiet", "--"]
    return []


def _run_python(code: str) -> dict:
    start = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "main.py"), "w") as f:
            f.write(code)
        with open(os.path.join(tmp, "_harness.py"), "w") as f:
            f.write(_HARNESS)

        cmd = _sandbox_prefix(tmp) + [sys.executable, "-I", "_harness.py"]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=_TIMEOUT_S, cwd=tmp,
                env={"PATH": "/usr/bin:/bin", "PYTHONIOENCODING": "utf-8", "HOME": tmp},
                preexec_fn=_limits if os.name == "posix" else None,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "stdout": "", "stderr": f"⏱ Timed out after {_TIMEOUT_S}s.",
                    "duration_ms": int((time.monotonic() - start) * 1000)}
        except FileNotFoundError as e:
            return {"ok": False, "stdout": "", "stderr": f"Sandbox launch failed: {e}",
                    "duration_ms": int((time.monotonic() - start) * 1000)}

    return {"ok": proc.returncode == 0, "stdout": _clip(proc.stdout),
            "stderr": _clip(proc.stderr), "duration_ms": int((time.monotonic() - start) * 1000)}


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
        last = None
        for stmt in [s.strip() for s in code.split(";") if s.strip()]:
            cur = conn.execute(stmt)
            if cur.description:
                last = ([c[0] for c in cur.description], cur.fetchall())
        out = []
        if last:
            cols, rows = last
            header = " | ".join(cols)
            out = [header, "-" * len(header)]
            out += [" | ".join(str(v) for v in r) for r in rows[:200]]
            out.append(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")
        else:
            out = ["OK — no rows returned."]
        return {"ok": True, "stdout": _clip("\n".join(out)), "stderr": "",
                "duration_ms": int((time.monotonic() - start) * 1000)}
    except sqlite3.Error as e:
        return {"ok": False, "stdout": "", "stderr": f"SQL error: {e}",
                "duration_ms": int((time.monotonic() - start) * 1000)}
    finally:
        conn.close()


def _clip(s: str) -> str:
    s = s or ""
    return s if len(s) <= _MAX_OUTPUT else s[:_MAX_OUTPUT] + "\n… (truncated)"
