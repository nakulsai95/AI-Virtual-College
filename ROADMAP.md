# AULA roadmap

What's built, and what's planned. The product is an AI-run university: agents
research real curricula, design a degree-scale plan, gather textbooks, and
author full "101" lessons, exams, labs, and spaced-repetition cards — all
metered against a credit budget, runnable locally with your own model key.

## Done

- Pluggable LLM connectors (Claude / OpenAI / Gemini / Mistral / Groq / Ollama) + credit budget with auto-downshift
- Principal researches university syllabi → designs + validates a 6–8 subject, degree-scale curriculum
- Content factory: hundreds of full 101 lessons (objectives, multi-paragraph sections, code, Mermaid diagrams, takeaways), tiered model cost, resumable
- All 7 agents real (Principal, Provost, Professors, Examiner, Registrar, Guide, Counselor)
- Real exams (Examiner writes + grades), reward loop, AI Provost methodology rewrites
- **Learn-by-playing labs**: predict→reveal **steps**, decision **scenarios**, match, order, quiz, bugfix (runs in sandbox)
- Narrated **lecture mode** (browser TTS slide player)
- **Spaced repetition** review (flashcards authored inside every lesson) + **transcript / GPA / degree**
- Accounts: sign-in (local Gmail profile), start-fresh, sign-out
- SQLite persistence, Windows-native run, offline demo mode

## Planned

### Flash games — arcade-style learning (next up)
Make the labs feel like the educational Flash games people grew up on: timed,
animated, scored, played — but every interaction teaches. The safe, robust way
(no LLM-generated code execution): a library of **generic arcade templates** the
Lab agent fills with concept content, rendered with animation + timer + combo
scoring. The teaching ("why") surfaces on every hit/miss.

Templates to build:
- **Sort** (shipping first): items stream in; drop each into the right category
  bucket against a timer; each reveals why. Great for taxonomies/classification.
- **Catch / Dodge**: catch correct answers, dodge wrong ones; lives + score.
- **Tap-the-right-one**: rapid-fire identify correct items, combo multiplier.
- **Wire / Connect**: draw links between related nodes (visual match).
- **Memory pairs**: flip-card matching of term ↔ meaning.
- **Timeline drag**: drag events/steps onto a timeline in order.

Design rules: domain-generic (works for code, law, biology, music); content from
the same materials grounding; bulk (cheap) model tier; cached per topic; finishing
awards XP + mastery like today's labs.

### Other planned
- Real Google Sign-In (OAuth Client ID) replacing the local profile
- Per-account college isolation (each Gmail its own university + budget)
- Video lectures (text-to-video API) — opt-in, paid
- Raster concept images (image API) + inline SVG illustrations — opt-in
- Hardened sandbox isolation (containers) for untrusted code
