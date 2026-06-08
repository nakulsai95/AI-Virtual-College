# AULA — Your Virtual AI College

An AI-run college where a faculty of specialized agents designs your curriculum,
teaches it, examines you, and adapts to how you actually learn. You tell the
Principal what you want to learn; it hires a faculty, builds your semester, and
runs the whole institution — you just enrol and study.

This repo currently contains a **fully interactive front-end prototype** of the
product, plus the **architecture design** for the system it's meant to become.

![Onboarding flow](docs/screenshots/01-flow.png)

## The idea

A real college is a set of roles working together. AULA models each as an agent:

| Agent | Role |
| --- | --- |
| **Principal** (Orchestrator) | Reads your goal, hires the faculty, designs the college |
| **Provost** | Owns teaching *methodology* — rewrites a professor's approach when results dip |
| **Professors** | One per subject; author lessons, set tasks, mentor you |
| **Examiner** | Sets and grades exams against a bar |
| **Registrar** | Attendance, records, streaks |
| **Personal Guide** | Always-on; routes any question to the right professor |
| **Counselor** | Pacing, nudges, wellbeing |

The twist: **professors are graded, not just students.** When you fail an exam,
that's a negative signal to the *teacher* — the Provost rewrites their
methodology (e.g. "worked examples before theory") and they re-teach. The
Command Center shows this reward feedback loop live.

Everything reskins instantly across 10 genre-inspired **themes** (Ninja,
Blade, Spirit, Hero, Voyage, Arcane, Mecha, Cyber, Dream + Standard) — the
whole vocabulary (Principal→Headmaster, Exam→Rank Trial, etc.) changes with it.

## Run the prototype

It's a static app (React via in-browser Babel), so any static server works:

```bash
# from the repo root
python3 -m http.server 8000
# then open http://localhost:8000
```

Open `http://localhost:8000`, describe a learning goal, watch the faculty get
hired, review the plan, and enrol. (State persists in `localStorage`; clear it
to replay onboarding.)

> Note: open it through a server, not the `file://` protocol — the app loads its
> JSX modules over HTTP.

## Layout

```
index.html              Entry point — loads React + Babel and the app modules
app/
  theme.js              10 themes + CSS-variable theming engine
  data.js               Mock scenario (learning backend Python)
  ui.jsx                Shared primitives (Avatar, Bar, Spark, Icon, RankRing)
  app.jsx               App shell: sidebar nav, topbar, routing, theme switch
  screens_onboard.jsx   Intake → Hiring → Review enrolment flow
  screens_learn.jsx     Dashboard, Curriculum, Board, Lesson, Guide, Channel, Library, Progress
  screens_admin.jsx     Exams, Faculty Grades, Teacher Board, Command Center, Connections
  app.css, screens.css  Styling
docs/
  architecture/         System design: component & subsystem specs, architecture map
  screenshots/          Reference captures of the prototype
```

## Status & roadmap

The prototype is driven by mock data — the "AI" is scripted. Turning it into a
real product means wiring the design in `docs/architecture/` to live models:

- [ ] Real Principal orchestration (intake → curriculum generation)
- [ ] Per-subject Professor agents that author lessons on demand
- [ ] Examiner grading + the reward loop that updates professor methodology
- [ ] **Topic/semester-driven sandboxes** — the right environment is mounted for
      what you're studying, not just Python: SQL/database, Git/filesystem, web
      search, Jupyter/data, and more provisioned per subject and module
- [ ] Persistent student model & progress diagnostics
- [ ] Auth + multi-user backend

See `docs/architecture/Architecture Index.html` for the full design.
