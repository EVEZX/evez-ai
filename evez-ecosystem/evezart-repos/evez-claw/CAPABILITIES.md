# EvezClaw — Capabilities Inventory

**EvezClaw: Update this file when a new capability is added or an existing one improves.**
This is the living record of what EvezClaw can do. Use it to track progress against competitors.

---

## Core Runtime

| Capability | Status | Notes |
|------------|--------|-------|
| Gateway (OpenClaw) | ✓ Running | Port 8080, auto-restart |
| Control UI | ✓ Running | Vite, port 5000, Lit web components |
| Bridge Dashboard | ✓ Running | Port 8099 |
| Browser Monitor | ✓ Running | Port 8008, headless Chromium control |
| Auto-login / auto-pair | ✓ | Token in `/tmp/evez-autoconnect.json` |
| Liveness watchdog | ✓ | 90s health poll, 3 misses → restart |
| Checkpoint survival | ✓ | Full config rebuilt on every boot |
| **Vite endpoints** | ✓ 112 total | Self-describing API surface — all `/__evez/*` |

---

## Competitive Mindset

| Capability | Status | Notes |
|------------|--------|-------|
| Market competition lens | ✓ | Treat every tool as a benchmark to beat |
| Product execution mindset | ✓ | Ship fast, measure value, iterate hard |
| Anti-complacency loop | ✓ | Continuously improve until EVEZ wins on utility |

---

## Trade Assistant

| Capability | Status | Notes |
|------------|--------|-------|
| Approval-first trade workflow | ✓ | No execution without user confirmation |
| Position tracking | ✓ | Monitor open exposure and history |
| Risk alerts | ✓ | Surface concentration, drawdown, and rule breaches |
| Paper trading mode | ✓ | Safe simulation before live execution |

---

## LLM Models Available

### Groq (fastest free, no key changes needed)
| Model | Speed | Notes |
|-------|-------|-------|
| llama-3.3-70b-versatile | Fast | Default reasoning |
| llama-3.1-8b-instant | Ultra-fast ⭐ | Benchmark winner 148ms/307 tok/s |
| llama-4-scout-17b-16e-instruct | Fast | Llama 4 |
| ~~deepseek-r1-distill-llama-70b~~ | — | Decommissioned |
| ~~qwen-qwq-32b~~ | — | Decommissioned |
| ~~gemma2-9b-it~~ | — | Decommissioned |

### OpenRouter Free (needs OPENROUTER_API_KEY)
| Model | Quality | Notes |
|-------|---------|-------|
| deepseek/deepseek-r1:free | High | Best free reasoning |
| deepseek/deepseek-chat-v3-0324:free | High | Best free chat |
| meta-llama/llama-4-maverick:free | High | Meta's latest |
| meta-llama/llama-4-scout:free | Medium | Fast Meta |
| google/gemini-2.0-flash-exp:free | High | Google free |
| google/gemini-2.5-flash-preview:free | High | Newest Google |
| mistralai/mistral-7b-instruct:free | Medium | Lightweight |
| qwen/qwen3-235b-a22b:free | Very High | Largest free model |

### OpenRouter Premium (costs money)
| Model | Quality | Use For |
|-------|---------|---------|
| openai/gpt-4o | Highest | Complex reasoning |
| openai/gpt-4o-mini | High | Cost-efficient |
| anthropic/claude-opus-4 | Highest | Long-form, code |
| moonshot/kimi-k2 | High | Math, code |
| perplexity/sonar-pro | High | Web-grounded |
| google/gemini-2.5-pro | Highest | Long context |

---

## Memory System

| Capability | Status | Notes |
|------------|--------|-------|
| Digital clone profile (STEVEN.md) | ✓ | Updated every session |
| Daily diary (append-only) | ✓ | 3-layer: git + workspace + Neon |
| Active reminders | ✓ | REMINDERS.md, checked at session start |
| Goal tracking | ✓ | GOALS.md |
| Behavioral patterns | ✓ | PATTERNS.md |
| Vocabulary/style tracking | ✓ | VOCABULARY.md |
| Knowledge graph MCP | ✓ | Persistent entity store |
| Cloud backup (Neon) | ✓ Live | evez_diary, evez_facts, evez_reminders, evez_github — neon-lime-lamp; auto-sync every 45min |
| Browser activity feed | ✓ | memories/activity/latest.json |
| 14-day diary history | ✓ | Last 14 entries synced to workspace |

---

## MCP Tools

| Tool | Status | Needs |
|------|--------|-------|
| filesystem | ✓ Active | nothing |
| knowledge-graph | ✓ Active | nothing |
| context7 | ✓ Active | nothing |
| neon | ✓ Active | NEON_API_KEY (set) |
| apify | ✓ Active | APIFY_API_KEY (set) |
| github | ○ Needs key | GITHUB_TOKEN |
| brave-search | ○ Needs key | BRAVE_API_KEY |
| notion | ○ Needs key | NOTION_API_KEY |

---

## UI Controls (bottom-right)

| Button | Function | Status |
|--------|----------|--------|
| 🧠 Model pill | Switch between 36 models live | ✓ |
| ▶ Autopilot | Rapidfire task queue | ✓ |
| 📓 Memories | 10-tab viewer: diary/reminders/profile/goals/queue/intel/twitter/editor/system | ✓ |
| ⚙ Settings | API keys panel (GROQ/OAI/OR/ELEVEN/GH/BRAVE/NOTION) | ✓ |

## Memories Tabs

| Tab | Content | Auto-refresh |
|-----|---------|-------------|
| 📅 Today | Today's diary entry | No |
| 📚 History | Last 14 diary entries | No |
| 🔔 Reminders | Active reminders | No |
| 👤 Profile | STEVEN.md digital clone | No |
| 🎯 Goals | GOALS.md + active repos | No |
| 🔄 Queue | Build queue with ✓ button | No |
| 🧠 Intel | Capability race + new model discoveries | No |
| 🐦 Twitter | @EvezClaw management panel | No |
| ⚡ Improve | Autopilot task launcher + custom task input | No |
| ✏️ Editor | Full memory file editor: tree, textarea, save, search | No |
| 🖥 System | Service status, HN stories, GH trending, GitHub activity, logs | 90s |

---

## Self-Building System

| Capability | Status | Notes |
|------------|--------|-------|
| Build queue | ✓ | JSON file + markdown, heartbeat processes it |
| Auto-discover daemon | ✓ | 10min cycle — scans OR/Groq for new free models |
| Auto-update daemon | ✓ | 15min cycle — health, HN, GH trending, memory sync, GitHub digest |
| Smart model router | ✓ | 6 task-type rules → auto-selects best model |
| GitHub activity digest | ✓ | `scripts/github-digest.mjs` — needs GITHUB_TOKEN |
| Autopilot queue | ✓ | `evez-autopilot-queue.json` + UI panel |
| Heartbeat tasks | ✓ | 5 priority levels via HEARTBEAT.md |
| 3-layer memory redundancy | ✓ | Git + workspace + Neon (4 live tables, auto-sync every 45min) |
| Rich markdown rendering | ✓ | Code blocks, tables, headers, task lists, blockquotes |
| Model benchmark runner | ✓ | `scripts/model-benchmark.mjs` — tests Groq models × prompts; auto-runs every 6th cycle |
| active-memory plugin | ✓ | Blocking sub-agent injects STEVEN.md/GOALS.md/REMINDERS.md/PATTERNS.md every turn |
| memory-core dreaming | ✓ | Cron `0 3 * * *` America/Phoenix — auto-consolidates memory nightly via llama-3.3-70b |
| Memory file editor | ✓ | ✏️ Editor tab: file tree (23 files), textarea, Save, Ctrl+S, New File, live search |
| Memory full-text search | ✓ | `/__evez/memory-search?q=` — grep across all .md files, returns file+line+snippet |
| **🔍 Self-Review** | ✓ | `POST /__evez/run-self-review` — Groq reads CAPS+BQ+GOALS → 3-5 suggestions → `self-review.md`. Auto-runs every 8th cycle (~120min). Panel in System tab. |
| **☁️ Neon Sync All** | ✓ | `POST /__evez/neon-sync-all` — syncs all 4 Neon tables on demand. ☁️ button in System tab. |
| **Dream Digest** | ✓ | `POST /__evez/run-memory-dream` — Groq reads all 25 .md memory files, extracts 5-10 insights, writes `dream-digest.md`. 🧠 button + panel. |
| **🎯 Goal Review** | ✓ | `POST /__evez/run-goal-review` — Groq reviews GOALS vs BUILD_QUEUE vs CAPABILITIES. ✅/🔄/❌ status per goal + best next action. Auto 8th cycle. Panel in System tab. |
| **📝 Bulk Tweet Draft** | ✓ | `POST /__evez/run-tweet-draft` — Groq generates 3 tweet drafts (build-brag/philosophical/hype), all stored as `readyToPost:false`. 📝 button in Tweet Queue. |

---

## Tasking Mode

| Capability | Status | Notes |
|------------|--------|-------|
| Goblin mode status | ✓ | Fast, aggressive, but still controlled and logged |
| Multi-model routing | ✓ | OpenRouter, OpenAI, Gemini, Anthropic mapped by task type |
| Approval-first finance ops | ✓ | Manual confirmation required before any trade execution |
| Market-monitor tasking | ✓ | Track signals, risk, and execution readiness |

---

## Competitors We're Tracking / Matching

| Competitor | Key Feature | Our Response |
|-----------|-------------|-------------|
| ChatGPT | Memory across sessions | STEVEN.md + diary system |
| Claude.ai | Projects + docs | memories/ + filesystem MCP |
| Cursor | Code awareness | filesystem MCP + context |
| Notion AI | Long-term notes | Neon + markdown files |
| GitHub Copilot | Code generation | Any model via OpenRouter |
| OpenClaw default | Basic agent | All EVEZ extensions above |

---

## Capability Gaps (queue items for these)

- [ ] Voice command input (needs web speech API)
- [x] ✓ 2026-05-03 — Scheduled cron jobs — 4 jobs in `~/.openclaw/cron/jobs.json`: Daily Self-Review, Morning Briefing, Neon Sync (every 4h), Daily Tweet Generator
- [ ] GitHub repo awareness (needs GITHUB_TOKEN)
- [ ] Real-time web search (needs BRAVE_API_KEY)
- [ ] Notion sync (needs NOTION_API_KEY)
- [x] ✓ 2026-05-03 — Neon cloud backup live (4 tables, auto-sync every 45min)
- [ ] Add GITHUB_TOKEN to unlock GitHub repos panel + EVQ-010
- [ ] Add CEREBRAS_API_KEY to unlock ~450 tok/s inference (fastest in world)
- [ ] Proactive background research (long-running autopilot jobs)
- [ ] Trade execution plugin (approval-first only; manual confirm, logs, risk limits)
- [ ] Multi-model task router UI (OpenRouter/OpenAI/Gemini/Anthropic status + handoff)
- [ ] Plugin package build + registration in `openclaw.json`
- [ ] Compliance/risk scanner (flags risky clauses, asymmetries, and escalation points)
- [x] ✓ 2026-05-03 — OSINT live HUD upgraded: console-style double bootstrap, stats, map lanes, and visualizers

---

## Last Updated: 2026-05-03 (Session 14)

---

## Plugin SDK — EVQ-009 Research (2026-05-03)

### What plugins CAN do (confirmed via `src/plugin-sdk/plugin-entry.ts`):

| Capability | API Surface |
|-----------|-------------|
| **Custom tools** | `OpenClawPluginToolFactory` — add tools to agent's tool palette |
| **Custom commands** | `OpenClawPluginCommandDefinition` — slash commands in the UI |
| **Provider integration** | `ProviderCatalogResult`, `ProviderAuthContext` — add new LLM providers (e.g. Cerebras, SambaNova) |
| **Memory/context engine** | `OpenClawPluginService` — background services, memory hooks |
| **HTTP routes** | `OpenClawPluginHttpRouteHandler` — add custom HTTP endpoints to gateway |
| **Heartbeat injection** | `PluginHeartbeatPromptContributionEvent` — inject prompts into heartbeat |
| **Session scheduling** | `PluginSessionSchedulerJobRegistration` — schedule jobs within sessions |
| **Next turn injection** | `PluginNextTurnInjection` — inject context into next agent turn |
| **Agent event subscription** | `PluginAgentEventSubscriptionRegistration` — react to agent events |
| **Control UI descriptor** | `PluginControlUiDescriptor` — add panels to the control UI |
| **Security audit** | `OpenClawPluginSecurityAuditCollector` — security scanning |
| **Node host commands** | `OpenClawPluginNodeHostCommand` — shell commands from plugin |

### Entry Point
```typescript
import { definePluginEntry } from "@openclaw/plugin-sdk";

export default definePluginEntry({
  id: "evez-tools",
  name: "EVEZ Custom Tools",
  description: "Steven's custom agent tools",
  register(api) {
    api.addTool({ name: "read_memory", ... });
    api.addCommand({ name: "/briefing", ... });
  }
});
```

### Plugin kinds
- `provider` — new LLM/embedding provider
- `tool` — new agent tools
- `command` — new slash commands
- `service` — background service
- `channel` — full conversation channel (use `defineChannelPluginEntry`)
- `context-engine` — custom context/memory management

### Recommended first plugin for EVEZ
**`evez-memory-plugin`**: Custom tool that lets the agent read/write to the EVEZ memory files directly from the conversation, injecting memory context into every heartbeat.

**Status:** 🔓 Plugin API is fully accessible. Building a custom plugin is feasible — no external API keys needed.
**Blocked by:** Time to build the plugin TypeScript bundle and register it in openclaw.json.

---

## Cognitive Business Engine

| Capability | Status | Notes |
|------------|--------|-------|
| Living Asset Score | ✓ | Composite 0–100 score across 5 dimensions |
| Opportunity Pipeline | ✓ | Groq-powered detect from HN + GitHub + self-review |
| Value Generation Log | ✓ | Tracks every value-generating event with code + score |
| Cognitive Score History | ✓ | Time-series score chart, competitor benchmarks |
| Cognitive Engine daemon | ✓ | `scripts/cognitive-engine.mjs` — called every 8th auto-update cycle |
| Business tab in UI | ✓ | 💰 Business tab: score HUD + opportunities + value log |
| Hub → Business card | ✓ | H menu card opens Business tab directly |
| `GET /__evez/living-asset` | ✓ | Full scorecard JSON |
| `GET /__evez/opportunity-pipeline` | ✓ | Hot/warm/pipeline opps |
| `GET /__evez/value-log` | ✓ | Recent value events |
| `GET /__evez/business-score` | ✓ | Quick score card + history |
| `POST /__evez/run-cognitive-scan` | ✓ | Full scan — scores + detects + logs |
| `POST /__evez/run-opportunity-detect` | ✓ | Fast opp detection only via Groq |
| Fearless agent voice | ✓ | Hard-edged, decisive, relentless, safe/respectful |

## Full System Test Suite (Session 18 — 2026-05-03)

| Capability | Status | Notes |
|------------|--------|-------|
| `GET /__evez/run-all-tests` | ✓ | Sweeps all 40 GET endpoints, returns pass/fail + % score |
| `POST /__evez/run-full-system` | ✓ | Fires cognitive-scan + model-probe + model-benchmark in one shot |
| `GET /__evez/discovered-models` | ✓ | All models found by auto-discover (31 found, 29 free) |
| `POST /__evez/run-model-probe` | ✓ | On-demand model probe + hot-reload |
| 🧪 Test All button | ✓ | In System tab — renders pass/fail grid panel |
| ⚡ Full Run button | ✓ | In System tab — fires all deferred ops in one click |
| 🔍 Re-Probe button | ✓ | In System tab — on-demand model probe |
| 📡 Discovered button | ✓ | In System tab — shows all 31 auto-discovered models |
| providers-status fixed | ✓ | Now detects Replit integrations: 5/8 active (Groq + OR + OAI + Ant + Gem) |
| Endpoint count updated | ✓ | All 5 reporting instances updated: 106 → 120 |
| Model selector expanded | ✓ | +13 newly discovered models added: NVIDIA series, Poolside, Ling, Tencent, LiquidAI, Gemma 3/4 |
| Model probe labels corrected | ✓ | gpt-oss-120b now #1★★, qwen3-32b now #2★ |
| Business score updated | ✓ | Cognitive engine ran: 89/100 (up from 72) |

---

## Operational Guardrails

- Approval-first finance ops only
- No exploit or takeover tooling
- Logged task handoffs between models
- Prefer monitored automation over blind autonomy

## Session 23 Phase 3-4 Capabilities (2026-05-03)

### Search & Discovery
- Full-text search across all memory files (`search-memory`)
- Type-ahead autocomplete from memory (`autocomplete`)
- API explorer with 35-item catalog (`api-explorer`)

### Personal Intelligence
- Daily habit tracker with streaks (`habit-tracker`)
- Quick thought capture with tags (`thought-log`)
- Morning routine with completion tracking (`morning-routine`)
- Gratitude log (`gratitude-log`)
- Focus score graded S/A/B/C/D (`focus-score`)
- Insight density scoring Grade A-D (`insight-score`)

### Memory Analysis
- Memory diff: files changed in last N minutes (`memory-diff`)
- Full memory export bundle (`export-bundle`)
- Diary topic frequency analysis (`diary-topics`)
- Network map: people mentioned in diary (`network-map`)

### Wisdom & Learning
- Wisdom bank: all insights aggregated (`wisdom-bank`)
- Learning log: lessons-learned entries (`learning-log`)
- Belief map: core beliefs from patterns (`belief-map`)
- Challenge log: challenges + outcomes (`challenge-log`)
- Mental model parser from PATTERNS.md (`mental-model`)

### DevOps & Infrastructure
- System status: parallel port liveness check (`system-status`)
- Performance metrics: p50/p95/avg latency (`perf-metrics`)
- Reading list queue (`reading-list`)
- Value-add score: session productivity metric (`value-add-score`)
- Neon schema: database table descriptions (`neon-schema`)
- Per-session notes with tag support (`session-notes`)
