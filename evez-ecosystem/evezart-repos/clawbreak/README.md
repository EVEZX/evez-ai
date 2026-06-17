# ClawBreak — Free AI Agent Platform

A lightweight, self-hosted AI agent that runs anywhere for free.

## Why ClawBreak?

OpenClaw costs money to host and needs 512MB+ RAM. ClawBreak runs on a free Oracle VM, a Raspberry Pi, or even Termux.

## Quick Start

### Install
```bash
git clone https://github.com/EvezArt/clawbreak.git
cd clawbreak
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here  # Free at console.groq.com
python daemon.py
```

### Use
```bash
# Chat
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain quantum computing", "model": "llama-3.3-70b"}'

# Health check
curl http://localhost:8080/health
```

## Stack
- Python 3.11+ (no Node.js needed)
- FastAPI (async, lightweight)
- SQLite (zero-config persistence)
- Groq Cloud API (free models: llama-3.3-70b, qwen3-32b, llama-4-scout)
- Docker-ready (single container, <100MB)

## Features
- Built-in memory with semantic search (SQLite + FTS5)
- Web UI included (no separate install)
- One-file deploy (no npm, no node-gyp, no native modules)
- Works on ARM (Oracle free tier)
- Session export/import (portable conversations)
- Built-in cron (no external scheduler needed)
- MCP client (connects to Composio, etc.)

## Self-Healing
ClawBreak includes a built-in healer that:
- Monitors service health every 30 seconds
- Auto-restarts on failure
- Logs all healing actions
- Integrates with MAES event spine

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Free API key from console.groq.com |
| `PORT` | No | Default: 8080 |
| `MEMORY_PATH` | No | Default: ./data/memory.db |

## Docker
```bash
docker build -t clawbreak .
docker run -p 8080:8080 -e GROQ_API_KEY=your_key clawbreak
```

## Contributing
1. Fork this repo
2. Create a feature branch
3. Submit a pull request

---

*Part of [EVEZ-OS](https://github.com/EvezArt/evez-os) • $6/mo • Zero API Cost*

---

## ⚡ OpenClaw Surface

This project now exposes/links into the EVEZ OpenClaw stack.

- Main deploy repo: https://github.com/EvezArt/evez-openclaw-deploy
- Android/A16 app: https://github.com/EvezArt/evez-openclaw-apk
- Local dashboard: `http://localhost:18789`
- Termux bootstrap: `scripts/a16-termux-bootstrap.sh` in the deploy repo

Run the OpenClaw gateway once, then point this surface at the same gateway URL so EVEZ Station, VCL, NEXUS, ClawBreak, Telegram, Slack, PWA, and Android all hit the same brain.
