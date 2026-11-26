# FMM — instructions for Gemini / Antigravity (same as AGENTS.md)

The one handbook is **CLAUDE.md** (same rules for every agent; the name is historical). Read it first, then
**HANDOVER.md** (current status, open items, things that must not be reintroduced) and the notes in **docs/memory/**.

Owner shortcuts (defined in CLAUDE.md): **Go**, **BU**, **YT**, **CHK**, **STATS**, **SAVE**.

Hard rules (details in CLAUDE.md):
- Work in ponytail ULTRA mode: smallest complete change; push back on parts the need does not justify.
- Only the cloud posts (GitHub Actions `codes.yml`). Never run `fmm.run_cloud` or any posting from the PC.
- Repo is PUBLIC: never commit `.env`, `secrets/`, tokens or `docs/history/`.
- Save state with `python -m fmm.savestate "msg"`; never plain-push `content/*.json`.
- No scheduled tasks on the PC (shared family computer).
- Owner is non-technical, in Bangladesh (BDT, UTC+6), zero budget: short answers, click-by-click steps.
