# EVEZ-OS OpenClaw Infrastructure

## 🧬 Self-Bootstrap — One Command

```bash
bash <(curl -s https://raw.githubusercontent.com/EVEZX/evez-openclaw-infra/main/bootstrap.sh)
```

That's it. It builds itself. Then it evolves itself. Forever.

## What It Does

### On Bootstrap
1. Installs OpenClaw + all dependencies
2. Clones EVEZ-OS ecosystem (163+ repos)
3. Deploys 9 live API services
4. Configures systemd auto-restart for all services
5. Installs self-healing (every 5 min)
6. Installs self-evolution (every 30 min)
7. Installs auto-backup (every 6h to GitHub)
8. Enables linger (survives reboots)

### On Evolution (every 30 min, automatic)
- Pulls latest code from all repos
- Restarts any crashed services
- Discovers and clones new repos from EvezArt/EVEZX
- Pushes state/memory to GitHub
- Cleans up old data

### Cost: $0/month

## Live Services
| Port | Service |
|------|---------|
| 18789 | OpenClaw Gateway |
| 9100 | EVEZ Provider (4 AI models, OpenAI-compatible) |
| 8080 | CriticalMind OMEGA (consciousness engine) |
| 9080 | ClawBreak (AI agent platform) |
| 9300 | Filter (personal AI assistant) |
| 9500 | Services Hub (job queue, monitoring, URL shortener, security scanner, data integrity) |

## Models
- `evez-smart` → GLM-5.1-FP8 (202K context)
- `evez-code` → DeepSeek-V3.2-NVFP4 (128K context)
- `evez-fast` → MiniMax-M2.5 (128K context)
- `evez-vision` → Kimi-K2.5 (128K context, multimodal)
