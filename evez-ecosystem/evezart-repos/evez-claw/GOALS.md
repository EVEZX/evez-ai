# Steven's Goals — Living Document

**EvezClaw: Update this file as goals are mentioned, refined, or completed.**
Mark completed goals with ✓ and the date. Never delete them.

---

## Active Goals

### EvezClaw — Digital Clone Agent (PRIMARY)
**Vision**: Make EVEZ a fully autonomous, self-improving digital extension of Steven.

Sub-goals:
- [x] ✓ 2026-05-03 — EVEZ has persistent memory injection via `active-memory` plugin — blocking memory sub-agent runs before every conversational reply, auto-injects STEVEN.md/GOALS.md/REMINDERS.md/PATTERNS.md. `memory-core` plugin provides memory_get + memory_search tools every session.
- [x] ✓ 2026-05-03 — Memory file editor — ✏️ Editor tab with file tree, live search, Save + Ctrl/Cmd+S. Steven can directly inspect and edit his own digital clone files.
- [x] ✓ 2026-05-03 — Gateway live log viewer — 📟 in System tab, shows real-time gateway activity, color-coded by severity, refresh button.
- [x] ✓ 2026-05-03 — Nightly memory dreaming — cron `0 3 * * *` Phoenix auto-consolidates memories at 3am via llama-3.3-70b.
- [x] EVEZ maintains a comprehensive, auto-updating memory of Steven across all sessions
- [x] EVEZ proactively suggests and implements improvements without being asked
- [x] EVEZ can operate on tasks autonomously via the autopilot queue
- [x] EVEZ has rich recall — can answer "what did we work on last Tuesday?"
- [x] EVEZ reads device activity (browser, clipboard) to stay in sync with what Steven is doing
- [x] ✓ 2026-05-03 — EVEZ stores diary + profile in multiple redundant locations (git + Neon + file) — Neon tables live, auto-sync every 45min
- [x] EVEZ can be deployed as a permanent presence, not just a chat session

### Model Intelligence
- [x] Switch to higher-capability models (GPT-4o, Claude Opus 4) for complex reasoning automatically
- [x] ✓ 2026-05-03 — Model auto-selection via smart router (POST /__evez/smart-route — 6 rules: code→Qwen3Coder, reason→R1, write→V3, fast→8B, vision→Maverick, web→LLaMA3.3)

### Automation Pipeline
- [x] Autopilot queue for batch research/drafting/coding tasks
- [x] ✓ 2026-05-03 — EVEZ has 4 scheduled cron jobs: Daily Self-Review (8am UTC), Morning Briefing (8am Phoenix), Neon Sync (every 4h), Tweet Generator (9:30am Phoenix)
- [x] ✓ 2026-05-03 — EVEZ monitors HN + GitHub trending (hn-latest.json, gh-trending.json, weekly-briefing.md — updated every 45min via auto-update daemon)

---

## Completed Goals ✓

- ✓ 2026-05-03 — Gateway, Control UI, Bridge Dashboard, Browser Monitor all running
- ✓ 2026-05-03 — Auto-login, auto-pair, liveness watchdog
- ✓ 2026-05-03 — MCP tools: filesystem, knowledge-graph, context7, neon, apify, github, brave-search, notion
- ✓ 2026-05-03 — Settings panel with API key management
- ✓ 2026-05-03 — Model selector pill (7 models: Groq + 6 OpenRouter)
- ✓ 2026-05-03 — Autopilot rapidfire task queue
- ✓ 2026-05-03 — HEARTBEAT.md with autopilot queue check + memory tasks
- ✓ 2026-05-03 — Digital clone memory system initialized (this file)
- ✓ 2026-05-03 — Self-build queue (BUILD_QUEUE.md): 8 items completed this session (EVQ-001/003/004/008/012 + more)
- ✓ 2026-05-03 — Intelligence feeds: HN AI stories + GH trending + weekly briefing auto-updated every 45min
- ✓ 2026-05-03 — Neon cloud backup live: evez_diary, evez_facts, evez_reminders, evez_github — project neon-lime-lamp

---

## Longer-Term Aspirations (vague but noted)

- Being able to have EVEZ work on tasks overnight and wake up to completed work
- EVEZ that "knows" Steven as well as his closest collaborator would
- A persistent AI presence that evolves alongside Steven's work and life

---

## Last Updated: 2026-05-03 (Session 14)
