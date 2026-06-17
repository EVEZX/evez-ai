# EVEZ-OPENCLAW-MESH

> CLAW GOBLIN MODE — Sovereign EvezArt OpenClaw Gateway

A fully-integrated OpenClaw gateway for the EvezArt/EVEZ-OS ecosystem. Routes queries across a free-tier AI ensemble while maintaining cryptographic audit trails and self-healing infrastructure.

## Architecture

```
Telegram Bot  ──→  tele_mesh_cortex.py
                          │
                    OpenClaw Gateway :18789
                    (openclaw.json → profiles)
                          │
         ┌────────────────┼────────────────┐
      evez-smart      evez-fast        evez-code
    (DeepSeek R1)  (Llama-3.3-70B)  (DeepSeek-R1-70B)
         │              │                 │
      OpenRouter      Groq              Groq
                          │
                    MCP Tool Servers
         ┌───────────────┬─────────────────┐
      GitHub MCP    Cloudflare MCP    Mem0 MCP
```

## Quick Start

```bash
# 1. Run setup
chmod +x setup.sh && ./setup.sh

# 2. Add your API keys
nano ~/.evez.env
source ~/.evez.env

# 3. Start the full mesh
docker compose up -d

# OR start just OpenClaw
openclaw --profile goblin --port 18789
```

## Master Control Phrases

| Phrase | Action |
|--------|--------|
| `full system sync` | Live-state read across all 18+ connectors |
| `advance trunk` | Decompose → branch → Recon + Skeptic → reintegrate |
| `run morning brief` | Gmail + Calendar + Linear + GitHub PRs |
| `immune loop` | Health check + self-heal all nodes |

## Profiles

- **goblin** — full mesh control, all tools, total command
- **code** — DeepSeek-R1-70B, production code only
- **recon** — Perplexity online, real-time web intelligence  
- **fast** — Llama-3.3-70B, rapid-response
- **skeptic** — GPT-4o, critical analysis

## Deployment

```bash
# Fly.io (production)
fly deploy

# Local with ngrok tunnel
docker compose up -d
# Tunnel URL: http://localhost:4040
```

## Telegram Commands

```
/start    — show command list
/status   — mesh health check
/sync     — trigger full system sync
/brief    — morning brief
/goblin <cmd>  — goblin mode prompt
/audit <repo>  — trigger security audit
/issue <repo> <title> — create GitHub issue
```

## Files

| File | Purpose |
|------|---------|
| `openclaw.json` | OpenClaw config — models, profiles, MCP servers, integrations |
| `fly.toml` | Fly.io deployment manifest |
| `Dockerfile` | Container build |
| `docker-compose.yml` | Full stack (gateway + ngrok + telegram bot) |
| `setup.sh` | One-shot local setup |
| `nomad_vault.py` | Encrypted credential store |
| `tele_mesh_cortex.py` | Telegram bot command handler |
| `evez_immune_loop.py` | Self-healing watchdog daemon |

## Environment Variables

Set in `~/.evez.env` or Docker:

```bash
OPENROUTER_API_KEY=   # Primary AI routing
GROQ_API_KEY=         # Fast inference (Llama, DeepSeek)
GITHUB_PAT=           # EvezArt repo access
VERCEL_TOKEN=         # Deployment management
CLOUDFLARE_API_TOKEN= # CF workers + analytics
CLOUDFLARE_ACCOUNT_ID=
FLY_API_TOKEN=        # Fly.io app management
TELEGRAM_BOT_TOKEN=   # Bot command interface
TELEGRAM_CHAT_ID=     # Default notification target
MEM0_API_KEY=         # Memory layer (190+ memories)
STRIPE_SECRET_KEY=    # Revenue pipeline
NGROK_AUTHTOKEN=      # Tunnel for external access
OPENCLAW_GATEWAY_TOKEN= # Gateway auth bearer token
```

---

*EvezArt | EVEZ-OS | ClawBreak — Building AI that builds itself.*