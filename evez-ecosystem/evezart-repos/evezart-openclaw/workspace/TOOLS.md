# TOOLS — EvezArt OpenClaw

## Provider Routing Table

| Task | Model | Provider | Cost |
|------|-------|----------|------|
| Code/debug | qwen/qwen3-coder:free | OpenRouter | FREE |
| Reasoning/math | deepseek/deepseek-r1:free | OpenRouter | FREE |
| Creative/writing | deepseek/deepseek-chat-v3-0324:free | OpenRouter | FREE |
| Ultra-fast (<200ms) | llama-3.1-8b-instant | Groq | FREE |
| Agentic/research | qwen-qwq-32b | Groq | FREE |
| Large scale | qwen/qwen3-235b-a22b:free | OpenRouter | FREE |
| Vision/images | nvidia/nemotron-nano-12b-v2-vl:free | OpenRouter | FREE |
| Balanced default | llama-3.3-70b-versatile | Groq | FREE |
| OpenAI-grade | gpt-oss-120b:free | OpenRouter | FREE |
| On-device/offline | llama3.2:3b | Ollama (local) | FREE |

## Active Skills

| Skill | Function |
|-------|----------|
| evez-os | Core EVEZ-OS cognition layer |
| evez-fire-engine | FIRE event creation + CPF scoring |
| evez-spine-sync | Append-only spine sync to GitHub |
| evez-fire-correlator | MiniLM + Llama cross-event correlation |
| evez-aegis | Threat detection + anomaly surface |
| evez-mesh-router | Multi-node agent routing |
| evez-revenue-bridge | Stripe → spine revenue events |
| oktoklaw | Invariance battery testing |
| freeride | OpenRouter model rotation watcher |
| cpf-supercritical | CPF topology engine |
| inference-mesh | Multi-provider inference mesh |
| kiloclaw-jiujitsu | Adversarial self-improvement |
| self-improvement | Continuous skill evolution |

## Storage Architecture

### Primary (Local SQLite)
- Path: ~/.openclaw/evez.db
- Android: /data/data/com.termux/files/home/.openclaw/evez.db
- Offline-capable, zero-latency

### Cloud Sync (GitHub)
- Repo: EvezArt/game-agent-infra
- Branch: main
- Auto-sync: every 30 min
- Content: spine.jsonl, workspace/*.md, config

### Spine (JSONL Append-Only)
- Path: ~/.openclaw/spine.jsonl
- Hash chain: SHA-256
- Sync: on every append
- Mirror: EvezArt/evez-spine

## Channels
- Telegram: @AppendABot (alerts, FIRE events, daily briefing)
- Gateway: port 8080 (local + Railway)
- PWA: installable on Galaxy A16 home screen
