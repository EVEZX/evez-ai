# ⚡ ClawBreak — Free AI Agent Platform

> Self-hosted, self-healing AI that runs anywhere for free.

## 60-Second Setup

```bash
# 1. Clone
git clone https://github.com/EvezArt/clawbreak-ai.git && cd clawbreak-ai

# 2. Set your API key  
export CLAWBREAK_LLM_API_KEY=your_vultr_key

# 3. Run
pip install fastapi uvicorn httpx pyyaml
python3 server.py
```

Open **http://localhost:8080** — done.

## What It Does

| Feature | Description |
|---------|-------------|
| 🤖 Multi-LLM | 4 providers with auto-fallback |
| 🔧 9 Tools | shell, search, memory, file, weather, email, GitHub, sysinfo, image gen |
| 🧠 Memory | SQLite FTS5 with semantic search |
| 📧 Email | Send via Composio (Gmail, Outlook) |
| 🐙 GitHub | Full API proxy |
| 🌤️ Weather | Real-time for any city |
| ⏰ Cron | Built-in scheduler |
| 🔌 Plugins | Load community plugins |
| 💬 Channels | Telegram bot (needs token) |
| 🛡️ Self-Healing | Triple-redundancy watchdogs |
| 📱 Web UI | Dark theme, mobile-friendly |
| 🐳 Docker | ARM64 + AMD64 |
| 🐍 Python | Pure Python, 256MB RAM, zero Node.js |

## API

```
POST /chat          — Chat with AI
POST /chat/stream   — Streaming chat  
WS   /ws            — Real-time chat
GET  /memory        — List stored facts
POST /memory        — Store a fact
GET  /weather/{loc} — Get weather
POST /email         — Send email
GET  /providers     — List LLM providers
GET  /mcp/tools     — List MCP tools
POST /mcp/call      — Call MCP tool
GET  /crons         — List cron jobs
POST /crons         — Add cron job
GET  /sessions      — List sessions
POST /export        — Export all data
POST /import        — Import data
GET  /health        — Health check
GET  /              — Web UI
```

## Self-Healing

Three independent watchdogs = 99.9% uptime:

1. **daemon.py** — continuous, 60s checks
2. **healer.py** — crontab, 3 min checks  
3. **health-guardian.sh** — crontab, 5 min checks

Kill any process and it comes back within 60 seconds.

## Deploy Anywhere

```bash
bash boot.sh           # One-command bootstrap
docker-compose up -d   # Docker
```

## License

MIT
