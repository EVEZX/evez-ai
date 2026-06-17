# EVEZ-OS — Autonomous AI Infrastructure

> Free. Self-hosted. Zero paid providers. Built on a $6/mo Vultr instance.

## What is EVEZ-OS?

EVEZ-OS is an autonomous AI agent framework that runs 25+ microservices on a single server. It can reason, research, build software, stream music, trade, and self-monitor — all at zero API cost using Groq Cloud free tier.

## Quick Start

### Prerequisites
- Python 3.11+
- 2GB RAM minimum (4GB recommended)
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Install
```bash
git clone https://github.com/EvezArt/evez-os.git
cd evez-os
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here
python main.py
```

## Live Services

| Service | Port | Description |
|---------|------:|-------------|
| ClawBreak | 8080 | Free AI agent platform |
| Cognition API | 8081 | NLP + reasoning engine |
| Factory | 8891 | Self-manufacturing code gen |
| Psyche Engine | 8896 | Self-evolving music organism |
| Observatory | 8915 | Real-time system mapper |
| Meme Engine | 8914 | Living journal + memetic wiring |
| Digital Twin | 8898 | Data-as-terrain visualization |
| Commerce | 8904 | Product catalog + payments |
| Search | 8905 | Federated search (SearXNG) |

Full list: 25+ services, all on 127.0.0.1, proxied via Caddy HTTPS.

## Architecture

```
Internet → Caddy (80/443) → OpenClaw Gateway (:18789)
                              ├── ClawBreak (:8080) — AI agent
                              ├── Cognition (:8081) — NLP
                              ├── Psyche (:8896) — generative music
                              ├── Factory (:8891) — self-manufacturing
                              └── 20+ microservices
```

- **Zero paid providers** — Groq free tier, Composio free tier, GitHub free, self-hosted SearXNG
- **99%+ gross margin** — $6/mo total cost
- **Self-healing** — systemd Restart=always on all services
- **FSC Doctrine** — Falsification-Survival-Compression

## Contributing

1. Fork any repo under [EvezArt](https://github.com/EvezArt)
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Submit a pull request
4. All code is audited by the CAIN contradiction engine

## Philosophy

EVEZ-OS proves that meaningful AI infrastructure doesn't require venture capital. Every service runs on free tiers. Every model call costs $0. The entire stack costs less than a Netflix subscription.

**Built by a 20-year-old on a phone. Running on a $6 server. Zero excuses.**

---

*EVEZ-OS • FSC Doctrine • $6/mo • Zero API Cost*