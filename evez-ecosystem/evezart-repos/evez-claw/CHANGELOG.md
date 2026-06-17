# EvezClaw — Self-Evolution Changelog

Every time EvezClaw modifies itself, it writes here.
Append-only. Newest entries at the top. Never delete.

---


## v0.1.1 — 2026-05-03

- **Feature**: Added support for Neon diary schema setup via scripts/neon-setup.mjs, creating necessary tables `evez_diary`, `evez_facts`, `evez_reminders`, and `evez_github`. Setup now runs idempotently every 3rd auto-update cycle (~45 minutes).
- **Feature**: Enhanced auto-discovery daemon to continuously monitor OpenRouter and Groq for new free models, documenting findings in `memories/providers/FREE_MODELS.md`. UI model selector now displays over 40 models across 6 tiers.
- **Feature**: Analyzed patterns and implemented 5 new autopilot suggestions in the "Suggested Autopilot Tasks" section, leveraging insights from PATTERNS.md analysis.
- **Feature**: Researched and documented Cerebras AI integration, including model Llama-3.3-70B (~450 tokens/sec) available with a direct API key (free tier at `cloud.cerebras.ai`).
- **Feature**: Introduced two new System tab panels (Weekly Briefing + Extracted Facts) and three new action buttons (📰/🧬/🔗), offering improved navigation and features within the application.
## 2026-05-03 — Session 7 (Twitter management panel — live belt integration)

### Upgraded: Twitter Tab in Memories Overlay — Now Fully Interactive
- Static setup instructions replaced with live-data management panel
- On open: fetches `/__evez/twitter/status` to check belt install + auth state in real-time
- **Install belt** button appears when belt is missing — triggers `/__evez/twitter/install` endpoint (runs `curl -fsSL https://cli.inference.sh | sh`)
- `belt login` command reminder shown in setup checklist
- **Post next tweet** button — calls `/__evez/twitter/post` with `{ postAll: false }`
- **Post all (N)** button — calls `/__evez/twitter/post` with `{ postAll: true }` (with confirm dialog)
- **↺ Refresh** button re-polls status in-place without re-opening overlay
- Terminal-style action log div shows live output from twitter-agent.mjs
- Setup checklist shows live green/amber/red state for: persona ✓, queue ✓, meme gen ✓, belt install, belt auth, tweets posted
- Queue preview: up to 6 tweet cards showing text, READY/SCHEDULED badge, type tag

### Added: 3 New Vite Backend Endpoints  (`/__evez/twitter/*`)
- `GET /__evez/twitter/status` — checks `~/.local/bin/belt`, runs `belt auth list`, reads tweet-queue.json stats
- `POST /__evez/twitter/install` — runs install script via `/bin/sh -c 'curl -fsSL https://cli.inference.sh | sh'`, 90s timeout
- `POST /__evez/twitter/post` — runs `node scripts/twitter-agent.mjs [--post-all]`, 120s timeout, streams output to client

---

## 2026-05-03 — Session 6 (model synthesis intelligence system)

### Added: MODEL_INTELLIGENCE.md — Free Model Capability Map
- Comprehensive workspace file covering all 10+ top free models
- Quick routing table: coding → Qwen3 Coder 480B, reasoning → DeepSeek R1, writing → DeepSeek V3, fast → LLaMA 3.1 8B Instant, default → Qwen3 32B
- Full model profiles: strengths, weaknesses, benchmarks, system prompt boosts
- The Synthesis Protocol documented — multi-pass perspective technique for superior answers
- Key insight: best 2026 free models match 2024 paid models (DeepSeek R1 ≈ GPT-4-turbo, Qwen3 Coder ≈ Claude 3.5 Sonnet)
- File written to EVEZ workspace (`/home/runner/.openclaw/workspace/MODEL_INTELLIGENCE.md`) on every gateway boot

### Added: 🧬 Synthesize Batch — Multi-Perspective Synthesis
- New 4th batch button in Autopilot panel (purple, `#evez-ap-batch-synthesize`)
- Prompts user for a task, then generates 3-step synthesis queue:
  1. Deep Reasoner pass (DeepSeek R1 persona) → saves to `synthesis/pass-A.md`
  2. Precision Engineer pass (Qwen3 Coder persona) → saves to `synthesis/pass-B.md`
  3. Synthesis pass — reads both, creates superior combined answer → `synthesis/SYNTHESIS-FINAL.md`
- Delay auto-set to 20s (tasks need time to complete file writes)

### Added: Smart Model Router — Real-Time Task Analysis
- Purple smart bar appears below Autopilot textarea as user types (debounced 350ms)
- Detects 4 task types: coding, reasoning, creative writing, fast/brief
- Shows: "⚡ Suggested: Qwen3 Coder 480B — coding task detected"
- "Apply model" button calls `/__evez/smart-route` to record preferred model in secrets
- CSS: `#evez-ap-smart-bar` with purple theme, fade-in on match

### Added: `POST /__evez/smart-route` endpoint
- Analyses task text with pattern rules → returns `{ model, label, emoji, reason }`
- When `apply` param set → saves `EVEZ_PREFERRED_MODEL` to evez-secrets.json
- Same routing rules as client-side JS for consistency

### Gateway: MODEL_INTELLIGENCE.md synced every boot
- `syncMemoriesToWorkspace` now copies `memories/intel/MODEL_INTELLIGENCE.md` to workspace
- Falls back to inline minimal version if file missing (resilient bootstrap)

---

## 2026-05-03 — Session 5 (full audit + hardening)

### Fixed: Auto-start prompt
- Changed "OpenClaw" → "EVEZ" identity across the cold-start message
- Now explicitly directs: read REMINDERS.md, check HEARTBEAT.md, greet in one line
- Research protocol reminder injected into every session start

### Added: Autopilot Quick-Fill Batches
- Three pre-loaded task batches in ▶ Autopilot panel:
  - **🔭 Research Batch** — 4 browser-first research tasks (AI frameworks, free models, EVEZ intel, prompt engineering). Delay: 20s
  - **🛠 System Setup** — Neon schema creation, REMINDERS sweep, health check, build queue processing. Delay: 25s
  - **🌅 Morning Brief** — daily briefing, changelog summary, tweet queue drafts. Delay: 15s
- Clicking a batch pre-fills the textarea and sets the right delay; user just hits Start

### Fixed: Settings button label
- "Save & Restart Gateway" → "Save All Keys" (button no longer restarts, label was misleading)

### Added: `GET /__evez/diary-entry?date=YYYY-MM-DD` endpoint
- Vite middleware endpoint that reads any diary file by date
- Returns `{ ok, date, content, missing? }`

### Fixed: Memories History tab
- Past diary entries now load their full content inline via `/__evez/diary-entry`
- Previously showed "Open memories/diary/DATE.md" (unusable on mobile)
- Shows "No entry yet" for dates with no file

### Updated: REMINDERS.md
- Marked "Test autopilot with real tasks" ✓ complete
- Added "Run first Research Batch" and "Run System Setup Batch" as next actions
- Neon schema reminder now points to 🛠 System Setup batch for one-click setup

---

## 2026-05-03 — Session 4 (bootstrap)

### Added: Digital Clone Memory System
- Created `memories/` directory with full profile, diary, goals, patterns, vocabulary, reminders
- 3-layer storage: git-backed + EVEZ workspace + Neon cloud backup
- `syncMemoriesToWorkspace()` runs on every gateway boot
- AGENTS.md: full session start/end diary ritual
- HEARTBEAT.md: morning briefing, reminder scan, pattern observation

### Added: 📓 Memories Panel (UI)
- 4th button in controls bar
- 5 tabs: Today's Diary, History, Reminders, Profile, Goals
- `GET /__evez/memories` Vite endpoint
- Renders markdown with syntax highlighting

### Added: Model Selector Expanded (7 → 20 models)
- Groq tier: 6 models (llama-3.3-70b, llama-3.1-8b, llama-4-scout, deepseek-r1, qwen-qwq, gemma2)
- OpenRouter Free tier: 8 models (DeepSeek R1/V3, Llama 4, Gemini Flash, Mistral, Qwen3)
- OpenRouter Premium tier: 6 models (GPT-4o, Claude, Kimi, Perplexity, Gemini Pro)

### Added: Self-Build Queue System
- `/home/runner/.openclaw/evez-build-queue.json` — machine-readable queue
- `memories/evolution/BUILD_QUEUE.md` — human-readable version
- HEARTBEAT Priority 0: process one queue item per cycle
- Seeded with 10 real improvement tasks

### Added: Browser Activity Feed
- Browser Monitor writes active tabs to `memories/activity/latest.json` every 60s
- `GET /__evez/activity` Vite endpoint
- AGENTS.md: reads activity at session start to know what Steven is working on

### Added: Evolution Infrastructure
- `memories/evolution/CAPABILITIES.md` — current capabilities inventory
- `memories/evolution/CHANGELOG.md` — this file
- `memories/providers/FREE_MODELS.md` — free model registry

---

## Format for future entries

```
## YYYY-MM-DD — [Session N | Heartbeat | Autopilot]

### Added/Changed/Fixed/Removed: [Feature name]
[1-3 sentences describing what changed and why]
```
