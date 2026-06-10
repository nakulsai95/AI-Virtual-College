# AULA — Your Virtual AI College

An AI-run college where a faculty of specialized agents designs your curriculum,
teaches it, examines you, and adapts to how you actually learn. You tell the
Principal what you want to learn; it hires a faculty, builds your semester, and
runs the whole institution — you just enrol and study.

This repo is the **full working app**: a React frontend, a Python (FastAPI)
backend with a persistent SQLite college, all seven agents implemented, real
code sandboxes, and a credit-budget system that meters every model call.

![Onboarding flow](docs/screenshots/01-flow.png)

## The idea

A real college is a set of roles working together. AULA models each as an agent
— all seven are live:

| Agent | Role |
| --- | --- |
| **Principal** (Orchestrator) | Reads your goal, hires the faculty, designs the college |
| **Provost** | Owns teaching *methodology* — an LLM reasons about what went wrong and rewrites a professor's approach when results dip |
| **Professors** | One per subject; author lessons (persisted to your Library), set tasks, answer DMs |
| **Examiner** | Writes real exams per module, grades them blind against a bar |
| **Registrar** | Attendance, streaks, XP — logged daily |
| **Personal Guide** | Always-on; routes any question to the right professor, who writes you a lesson |
| **Counselor** | Looks at your weakest concept each day and sends one pacing nudge |

The twist: **professors are graded, not students.** When you fail a probe or an
exam, that's a negative signal to the *teacher* — the Provost rewrites their
methodology (e.g. "worked examples before theory") and they re-teach. Your own
XP and mastery only ever go up. The Command Center shows the reward loop live.

Everything reskins instantly across 10 genre-inspired **themes** (Ninja,
Blade, Spirit, Hero, Voyage, Arcane, Mecha, Cyber, Dream + Standard) — the
whole vocabulary (Principal→Headmaster, Exam→Rank Trial, etc.) changes with it.

## Run it (one command, one server)

The backend serves both the API and the frontend at **http://localhost:8000**.

**Windows**

```bat
backend\run.bat        :: or: powershell backend\run.ps1
```

**macOS / Linux**

```bash
cd backend && ./run.sh
```

Then open **http://localhost:8000**. Describe a learning goal, watch the
faculty get hired, review the plan, and enrol. Everything — curriculum, lessons,
exams, faculty grades, your mastery and streak — persists in `backend/aula.db`
across restarts.

No API key? The whole loop still works on the built-in demo model. To make the
agents *real*, open **Connections**, pick a provider, paste a key, **Test**,
**Connect**.

## Bring your own model (connectors)

The agents are model-agnostic. You choose the provider and supply your own key
in the UI — nothing is hard-coded:

| Provider | Notes |
| --- | --- |
| **Claude (Anthropic)** | Official `anthropic` SDK, adaptive thinking. `claude-opus-4-8` default. |
| **OpenAI (GPT)** | Official `openai` SDK. |
| **Gemini (Google)** | OpenAI-compatible endpoint — long context. |
| **Mistral** | OpenAI-compatible endpoint — fast & open models. |
| **Groq** | OpenAI-compatible — very fast inference. |
| **Ollama** | Runs locally — no key, fully private, $0. |

Your key is saved on *your* backend (`backend/.connectors.json`, git-ignored)
and used to call the provider. It never lands in the repo.

### Credits & budget

Every agent call is metered: token usage × the provider's price, recorded per
agent (see the Command Center budget bars and **Connections → Credits &
budget**). The default cap is **$5.00**:

- When **less than 25%** of the budget remains, agents automatically downshift
  to the provider's **cheapest model** to stretch your credits.
- When the budget is **spent**, agents fall back to demo mode instead of
  charging you — raise the cap to keep going.

## Layout

```
index.html              Entry point — loads React + Babel and the app modules
app/
  theme.js              10 themes + CSS-variable theming engine
  data.js               Demo scenario (used until the backend hydrates real state)
  api.js                Backend client + /api/state hydration
  ui.jsx                Shared primitives (Avatar, Bar, Spark, Icon, RankRing)
  app.jsx               App shell: sidebar nav, topbar, routing, theme switch
  screens_onboard.jsx   Intake → Hiring → Review enrolment flow (calls the Principal)
  screens_learn.jsx     Dashboard, Curriculum, Board, Lesson, Guide, Channel, Library, Progress
  screens_admin.jsx     Exams (take them for real), Faculty Grades, Teacher Board,
                        Command Center, Connections (+ Credits & budget)
  app.css, screens.css  Styling
backend/
  app/main.py           FastAPI app — API + serves the frontend
  app/db.py             SQLite persistence: the whole college survives restarts
  app/llm/              Provider layer (Claude/OpenAI/Gemini/Mistral/Groq/Ollama + mock)
  app/llm/metering.py   Credit budget: per-call cost, cap enforcement, auto-downshift
  app/agents/           principal, professor, examiner, provost, guide, counselor
  app/routers/          connectors, onboard, faculty (lessons+grading), college
                        (/api/state, guide, channels, exams, budget), sandbox
  app/sandbox/runner.py Python (isolated subprocess, Windows-safe) + SQL (SQLite)
  run.bat / run.ps1 / run.sh, requirements.txt, .env.example
  smoke_test.py         End-to-end test of the whole loop (mock provider)
docs/
  architecture/         System design: component & subsystem specs, architecture map
  screenshots/          Reference captures of the prototype
```

## Status & roadmap

- [x] **Pluggable LLM connectors** — Claude/OpenAI/Gemini/Mistral/Groq/Ollama, bring your key
- [x] **Credits & budget** — every call metered, per-agent spend, cap + auto-downshift
- [x] **Real Principal orchestration** — intake → live curriculum generation
- [x] **Persistent college (SQLite)** — curriculum, faculty grades, lessons, exams,
      board, channels, mastery, streaks all survive restarts
- [x] **All 7 agents real** — including the Guide (routes questions → professor
      writes a lesson), an LLM Provost (reasons about failures), the Counselor
      (daily nudges) and Registrar (attendance/XP/streaks)
- [x] **Real exams** — the Examiner writes questions per module, grades blind,
      passing advances the curriculum and unlocks the next module
- [x] **Student mastery model** — per-concept diagnostics that drive My Progress
- [x] **Real sandbox execution** — Python (isolated subprocess) and SQL (SQLite),
      Windows/macOS/Linux
- [x] **Channels** — DM your professors and Guide; they answer in persona
- [ ] Auth + multi-user storage
- [ ] Hardened sandbox isolation (container/network) for untrusted code

Verify the whole loop without a key:

```bash
cd backend && .venv/Scripts/python smoke_test.py    # Windows: .venv\Scripts\python
```

> ⚠️ The Python sandbox runs code in a subprocess with CPU/memory/time limits —
> fine for local single-user dev, **not** a hardened multi-tenant boundary. Don't
> expose it to the public internet without real container/network isolation.

See `docs/architecture/Architecture Index.html` for the full design.
