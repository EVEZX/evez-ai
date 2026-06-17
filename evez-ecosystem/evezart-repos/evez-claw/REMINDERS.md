# Reminders — Active & Pending

**EvezClaw: Check this file at the start of every main session. Surface anything due or relevant.**
Add reminders whenever Steven mentions something to follow up on.
Mark completed items with ✓ and the date. Never delete them.

---

## Active Reminders

### System
- [ ] **Run populate-reminders regularly to keep reminder list fresh** — Added by EVEZ 2026-05-03

- [ ] **Set up OPENROUTER_API_KEY** — needed to use GPT-4o, Claude, Kimi, Perplexity, Gemini via the model selector. Add in ⚙ Settings panel.
- [ ] **Set up GITHUB_TOKEN** — activates GitHub MCP + GitHub repos panel (EVQ-010). Add in ⚙ Settings → paste token → restart gateway.
- [ ] **Set up BRAVE_API_KEY** — activates Brave Search MCP (real-time web). Add in ⚙ Settings.
- [ ] **Set up CEREBRAS_API_KEY** — unlocks world's fastest inference (~450 tok/s) via Llama-3.3-70B. Free tier at cloud.cerebras.ai. Add in ⚙ Settings.
- [x] ✓ 2026-05-03 — **Neon database schema** — tables created: `evez_diary`, `evez_facts`, `evez_reminders`, `evez_github` in project neon-lime-lamp. Auto-sync running every 45min.
- [x] ✓ 2026-05-03 — **Cron jobs** — 4 scheduled: Daily Self-Review 8am UTC, Morning Briefing 3pm UTC (8am Phoenix), Neon Sync every 4h, Daily Tweet Generator 9:30am Phoenix. All in `~/.openclaw/cron/jobs.json`.
- [x] ✓ 2026-05-03 — **Model benchmark** (EVQ-006) — `scripts/model-benchmark.mjs` complete. Winner: `llama-3.1-8b-instant` (148ms avg / 307 tok/s). Results in `memories/evolution/MODEL_BENCHMARKS.md`. Runs every 6th auto-update cycle. ⚡ Model Bench button in System tab.
- [x] ✓ 2026-05-03 — **active-memory plugin live** (EVQ-013) — EVEZ now has persistent memory injection on every turn. `active-memory` + `memory-core` plugins enabled in openclaw.json.
- [x] ✓ 2026-05-03 — **Memory File Editor** — ✏️ Editor tab with file tree, textarea, Save + Ctrl/Cmd+S, live search across all 23 memory files. 4 new Vite endpoints. 32 total.
- [x] ✓ 2026-05-03 — **Gateway Log Viewer** — 📟 live log panel in System tab, color-coded severity, ↻ refresh button, loads last 80 lines of gateway workflow log.
- [x] ✓ 2026-05-03 — **memory-core dreaming cron** — 3am nightly memory consolidation, llama-3.3-70b-versatile, America/Phoenix timezone.
- [x] ✓ 2026-05-03 — **active-memory promptAppend paths FIXED** — was pointing to `/memories/users/` (non-existent); corrected to `profile/STEVEN.md`, `profile/GOALS.md`, `reminders/REMINDERS.md`, `profile/PATTERNS.md`. Gateway hot-reloaded automatically.
- [x] ✓ 2026-05-03 — **active-memory-preview endpoint** — `/__evez/active-memory-preview` shows exactly what EVEZ injects before each reply (4 files, line counts, model, timeout). Wired into System tab as 🧠 panel.

### Project
- [x] **Test autopilot with real tasks** — 2026-05-03 — three quick-fill batches added: Research, System Setup, Morning Brief. Auto-dispatch working end-to-end.
- [ ] **Run first Research Batch** — open ▶ Autopilot → click `🔭 Research Batch` → Start. This also tests the browser-first protocol.
- [ ] **Run System Setup Batch** — open ▶ Autopilot → click `🛠 System Setup` → Start. This creates Neon schema + runs self-health check.

### Twitter / @EvezClaw
- [x] **Twitter tab** upgraded — 2026-05-03 — live belt status check, Install/Post/Post-all buttons, action log, queue preview
- [ ] **Create @EvezClaw account** — go to https://twitter.com/signup, handle: **@EvezClaw**, use the persona from EVEZ_TWITTER.md
- [ ] **Run `belt login`** — in Shell tab, run `~/.local/bin/belt login` and authenticate with @EvezClaw
- [ ] **Post debut tweets** — open Memories → Twitter tab → "Post all (10)" to fire all queued tweets

---

## Completed ✓

- ✓ 2026-05-03 — Model selector (30+ models) — shipped
- ✓ 2026-05-03 — Autopilot rapidfire queue — shipped
- ✓ 2026-05-03 — Digital clone memory system — initialized
- ✓ 2026-05-03 — Browser-first research protocol — wired across gateway + voice + autopilot
- ✓ 2026-05-03 — Autopilot quick-fill batches (Research / System Setup / Morning Brief) — shipped
- ✓ 2026-05-03 — Diary history tab now loads full content inline — shipped
- ✓ 2026-05-03 — Auto-start prompt updated to EVEZ identity + reminders directive — shipped

---


### Groq-Suggested Reminders — 2026-05-03

**EvezClaw Follow-up Reminders**

### EvezClaw — Digital Clone Agent (PRIMARY)

- [ ] **Run Memory File Injection Test** — Test active-memory plugin by simulating blocking memory injection and verifying that sub-agent memory is updated as expected. This is to ensure seamless integration of EvezClaw's digital clone functions.

### System Upgrades

- [ ] **Verify OPENROUTER_API_KEY Integration** — Once the OPENROUTER_API_KEY is set up, test the GPT-4o, Claude, Kimi, Perplexity, Gemini API integrations to confirm that they are working as expected before relying on them.

### Changelog and Capability Management

- [ ] **Review and Prune Endpoints** — Review CAPABILITIES.md and identify endpoints that may be outdated, redundant, or unnecessary. Implement necessary endpoint removals and update relevant systems (e.g., auto-update scripts) accordingly.

### Memory File Editor

- [ ] **Implement Memory File Editor Search Functionality** — Expand the Memory File Editor to include search functionality, allowing EvezClaw to efficiently locate and navigate digital clone files. This can be achieved by integrating a robust search algorithm or leveraging an existing library.

## Follow-Up Queue (things mentioned but not yet done)

_EVEZ: when Steven mentions something in passing that needs follow-up, add it here_

| Item | Mentioned | Priority |
|------|-----------|----------|
| (none yet) | — | — |

---

## Last Updated: 2026-05-03 (Session 14)
