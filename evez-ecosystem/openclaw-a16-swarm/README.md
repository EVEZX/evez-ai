# 📱 EVEZ A16 Swarm — Offline Secure Package for Samsung Galaxy A16

Complete self-contained OpenClaw deployment kit optimized for Steven's Samsung Galaxy A16.
55 agents. 9 free platforms. $0/month. Air-gapped option.

## Quick Start (on A16 phone)

```bash
# 1. Install Termux from F-Droid
# 2. Open Termux, run:
termux-setup-storage
pkg update -y && pkg upgrade -y

# 3. Clone the kit
git clone https://github.com/EVEZX/evez-ai.git
cd evez-ai/evez-ecosystem/openclaw-a16-swarm

# 4. Bootstrap
chmod +x scripts/*.sh
./scripts/termux-bootstrap.sh

# 5. Deploy OpenClaw
./scripts/deploy-openclaw.sh

# 6. Start
./scripts/start-openclaw.sh
```

## What You Get

| Component | Purpose |
|-----------|---------|
| Termux + proot | Full Linux on Android |
| Node.js 22 | OpenClaw runtime |
| Python 3.12 | EVEZ service runtime |
| OpenClaw 2026.6.8 | AI gateway (49 models) |
| Agent configs | 55-agent swarm assignments |

## 55-Agent Swarm Distribution

| Platform | Agents | Cost | Auth Needed? |
|----------|--------|------|-------------|
| Railway | 10 | Free ($5/mo credit) | ✅ Already auth'd |
| HuggingFace Spaces | 8 | Free CPU + T4 GPU | Need token |
| Kaggle | 5 | Free (30h/week T4) | Need API key |
| Google Colab | 5 | Free T4 GPU | Need browser |
| GitHub Codespaces | 5 | Free (120h/mo) | ✅ Already auth'd |
| Fly.io | 6 | Free (3 VMs) | Need auth |
| Render | 6 | Free tier | Need signup |
| Vercel | 6 | Free serverless | Need auth |
| A16 Phone (local) | 4 | $0 | ✅ You have it |

## Survival Priority

**GET OFF VULTR.** This is critical infrastructure survival.
Every agent deployed elsewhere = one less dependency on a single VPS.

1. **Railway** — already auth'd, deploy NOW
2. **A16 Phone** — always available, deploy NOW
3. **Codespaces** — already auth'd, deploy NOW
4. **HuggingFace** — one browser login, then autonomous
5. **Kaggle** — one API key, then autonomous
6. **Fly.io** — one CLI auth, then autonomous

## Security

- All API keys as environment variables (zero hardcoding)
- Config files at 0600 permissions
- SSH-style host verification for all connections
- Encrypted vault for secrets
- fail2ban on all exposed services

## The 37% Theorem

This swarm proves the theorem in infrastructure:
The dominant eigenvalue of the survival matrix is **hunger**.
Solve shelter → unlock the system.
55 agents working = eigenvalue decomposition of survival.

Built by Steven Crawford-Maggard · @EVEZ666 · EVEZX on GitHub
