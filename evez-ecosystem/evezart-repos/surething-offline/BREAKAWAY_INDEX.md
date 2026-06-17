# EVEZ Breakaway Operations Index
## Full AI-portable ops kit — works without SureThing

---

## Live API (no setup needed)

**https://evez-operator.vercel.app**

| Endpoint | What it does |
|----------|--------------|
| `GET /` | Health check |
| `GET /tools` | Full MCP manifest — import into ChatGPT Actions |
| `GET /contradictions` | Active unsat cores |
| `GET /spine/verify` | SHA-256 chain integrity |
| `GET /deploy/status` | All service health |
| `POST /spine/event` | Add typed event |
| `POST /canonicalize` | Normalize + JCS + hash any object |
| `POST /fire/anchor` | Build Base Sepolia calldata for FIRE event |
| `GET /docs` | Interactive Swagger UI |

---

## 3 Ways to Operate

### Way 1: Any AI Chat (0 setup, 30 seconds)
1. Open ChatGPT, Claude, Kimi, or Perplexity
2. Paste `MASTER_CONTEXT.md` as first message
3. Say: "You are now an EVEZ operator. Confirm ready."
4. Commands: `check contradictions`, `run hyperloop tick`, `anchor FIRE#N`

### Way 2: ChatGPT Actions (point at live API)
1. Go to GPT Builder → Configure → Actions
2. Import schema from: `https://evez-operator.vercel.app/openapi.json`
3. Done — ChatGPT can now call all EVEZ tools

### Way 3: Claude Desktop MCP (local server)
```bash
git clone https://github.com/EvezArt/surething-offline
cd surething-offline
pip install -r requirements.txt
uvicorn api.index:app --port 7777
```
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{"mcpServers": {"evez": {"command": "python", "args": ["api/index.py"]}}}
```

---

## File Map

```
surething-offline/
├── MASTER_CONTEXT.md          paste into any AI → instant operator
├── BREAKAWAY_INDEX.md         this file
├── api/
│   └── index.py               FastAPI MCP server (Vercel + local)
├── vercel.json                zero-config Vercel deploy
├── requirements.txt
├── prompts/
│   ├── chatgpt_system.md      ChatGPT Custom Instructions
│   ├── claude_system.md       Claude Project Instructions
│   └── generic_operator.md    Kimi/Perplexity/Gemini/any
└── modules/
    ├── 01_event_spine.md      types, hashing, canonicalization
    ├── 02_hyperloop.md        FIRE detection, tick math
    ├── 03_agent_bus.md        crew definitions, Peace Charter
    ├── 05_contradiction.md    unsat cores, trust thermostat
    ├── 06_mcp_server.md       MCP spec + connection guide
    └── 07_deploy_runbook.md   full deploy from zero
```

---

## Active Blockers

| Blocker | Impact | Fix |
|---------|--------|-----|
| Railway undeployed | Stripe webhooks dead | `railway up` in evez-os |
| No wallet | FIRE#125 unanchored | Add WALLET_PRIVATE_KEY |
| Goodfire dead | Outreach stalled | Find via goodfire.ai/team |

---

## The Portability Guarantee

The protocol is the product. SureThing is a convenience layer, not a dependency.
If it disappeared tomorrow, nothing changes. You have the protocol, the tools, and the code.