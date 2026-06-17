# SureThing Offline — Self-Hosted Edition

> A fully offline, paywall-free, self-hosted digital twin assistant.  
> Runs 100% locally. No cloud calls required. No subscription gates.

---

## Quick Start

```bash
git clone https://github.com/EvezArt/surething-offline
cd surething-offline
bash bootstrap.sh
```

Opens at `http://localhost:8420`.

---

## What This Is

| Feature | Implementation |
|--------|----------------|
| Chat interface | FastAPI + vanilla HTML/JS |
| AI brain | Ollama (Mistral 7B, Llama3, phi3) |
| Email monitoring | IMAP polling |
| Task queue | SQLite spine |
| Event spine | SHA-256 chained JSONL ledger |
| Memory | Chroma vector DB |
| Scheduled tasks | APScheduler |

---

## Architecture

```
Browser (localhost:8420)
       │
       ▼
FastAPI HTTP Server (api/)
  ├── /chat     → Ollama LLM
  ├── /tasks    → SQLite
  ├── /drafts   → file store
  ├── /spine    → JSONL ledger
  ├── /memory   → Chroma
  └── /health   → system status
```

See [DEPLOY.md](DEPLOY.md) for Docker, Raspberry Pi, and systemd deployment.

---

## No Paywall. Full Control.

| Cloud | Offline |
|-------|---------|
| Monthly subscription | $0 |
| Cloud API calls | Local Ollama |
| Data in cloud | `./data/` — yours |
| Feature gates | None |
| Account required | No |
