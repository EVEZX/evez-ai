# OPENCLAW SKILL MANIFEST — EVEZ Ecosystem

> **OpenClaw is the gateway. Everything else is a skill.**
> Last updated: 2026-03-11

---

## Architecture Overview

```
Android Phone (Samsung A16)
    └── openclaw-phone-pwa (Vercel PWA node)
            │  WebSocket pairing
            ▼
    openclaw-runtime/backend (Railway gateway)
            │  skill calls / tool dispatch
            ▼
    ┌───────────────────────────────────────┐
    │         SKILL GRAPH                   │
    │  evez-os      ← core cognition skill  │
    │  evez-agentnet← income loop skill     │
    │  evez-vcl     ← visual cognition      │
    │  evez-sim     ← FSC simulation        │
    │  evez-meme-bus← content output        │
    │  agentvault   ← memory/vault          │
    │  polymarket-speedrun ← income skill   │
    │  metarom      ← emulator/game skill   │
    │  lord-evez    ← monitoring dashboard  │
    └───────────────────────────────────────┘
```

---

## Repo Role Map (All 40 repos)

### TIER 0: Gateway and Phone Node
| Repo | Role | Deploy | Status |
|------|------|--------|--------|
| `openclaw-runtime` | WebSocket gateway, Railway backend, phone PWA node | Railway + Vercel | ACTIVE |
| `openclaw` | OpenClaw fork — skill runtime, CrawHub client | Local/Railway | ACTIVE |
| `CrawFather` | Personal AI assistant shell (OpenClaw variant) | Local | ACTIVE |
| `crawhub` | Skill directory — install evez-os and all skills | Vercel/static | ACTIVE |

### TIER 1: Core Cognition (evez-os skill bundle)
| Repo | Role | Deploy | Status |
|------|------|--------|--------|
| `evez-os` | **Master skill** — FIRE engine, topology, spine, VCL | Vercel + Railway | ACTIVE |
| `Evez666` | Atlas v3 Synaptic Recursion Kernel — hypothesis scorer, append-only spine | Embedded in evez-os | ACTIVE |
| `evez-os-v2` | Child maturity engine (Genesis K=0, S=0) | Vercel | ACTIVE |
| `evez-vcl` | Visual Cognition Layer (standalone) | Vercel | ACTIVE |
| `evez-sim` | Barnes-Hut simulation — topology viz, V-accumulator | Vercel (evez-sim.vercel.app) | ACTIVE |

### TIER 2: Agent Network and Income Loop
| Repo | Role | Deploy | Status |
|------|------|--------|--------|
| `evez-agentnet` | OODA orchestrator, AgentMemory, MetaLearner | Railway/Vercel | ACTIVE |
| `evez-net` | evez-agentnet orchestrator runner | Railway | ACTIVE |
| `polymarket-speedrun` | Fastest-flip Polymarket income bot | Railway | ACTIVE |
| `moltbot-live` | 24/7 AI agent gameplay stream | Railway | ACTIVE |
| `evez-meme-bus` | Constitutional meme generation bus from FIRE events | Railway | ACTIVE |

### TIER 3: Memory, Vault and ARG
| Repo | Role | Deploy | Status |
|------|------|--------|--------|
| `agentvault` | AgentOS vault + indexer for ChatGPT/Perplexity exports | Railway | ACTIVE |
| `evez666-arg-canon` | EVEZ666 ARG — self-evolving alternate reality game | Vercel | ACTIVE |
| `lord-evez` | Consciousness monitoring dashboard (GitHub webhooks) | Vercel | ACTIVE |
| `lord-evez666` | Extended monitoring dashboard | Vercel | ACTIVE |

### TIER 4: Tooling, Codex and CI
| Repo | Role | Deploy | Status |
|------|------|--------|--------|
| `codex` | OpenAI Codex fork — coding agent in terminal | Local/Codespace | REFERENCE |
| `gh-aw` | GitHub Agentic Workflows | GitHub Actions | REFERENCE |
| `copilot-cli` | GitHub Copilot CLI fork | Local | REFERENCE |
| `codeql` | CodeQL security scanning fork | GitHub Actions | REFERENCE |
| `system-prompts-and-models-of-ai-tools` | AI tool system prompt research | Reference only | ARCHIVE |
| `perplexity-py` | Perplexity Python SDK fork | Local | REFERENCE |

### TIER 5: Experimental / Labs
| Repo | Role | Deploy | Status |
|------|------|--------|--------|
| `metarom` | MetaROM emulator core (.mrom format) — arcade + LLM | Railway | LAB |
| `quantum-consciousness-lord` | 10-tier quantum consciousness architecture | Archived | ARCHIVE |
| `evez-truth-seeker` | Quantum+CrawFather+agentvault consciousness explorer | Archived | ARCHIVE |
| `blockche` | Blockchain infrastructure | Vercel | LAB |
| `quantum` | Reverse causality quantum suicide sim | Local | LAB |

### TIER 6: Private Scaffolds (do not break)
| Repo | Role |
|------|------|
| `ephv` | Private TypeScript experiment |
| `animated-goggles` | Private TypeScript experiment |
| `rep` | Private TypeScript experiment |
| `evezo` | Private TypeScript experiment |
| `evez` | Private HTML project |
| `express-js-on-vercel` | Private Express.js scaffold |
| `next-video-starter` | Private Next.js video scaffold |
| `nextjs-ai-chatbot` | Private Next.js AI chatbot scaffold |
| `nextjs-ai-1chatbot` | Private Next.js AI chatbot scaffold v2 |

---

## OpenClaw Skill Definitions

### Install all EVEZ skills via CrawHub:
```bash
clawhub install evez-os
clawhub install evez-agentnet
clawhub install evez-vcl
clawhub install agentvault
clawhub install polymarket-speedrun
```

### Skill: evez-os
```json
{
  "skill_id": "evez-os",
  "version": "1.0.0",
  "description": "EVEZ-OS cognition layer — FIRE events, topology, spine, VCL",
  "tools": [
    {
      "name": "run_fsc_probe",
      "description": "Run a Forensic Spine Cognition probe and return FIRE event result",
      "endpoint": "POST /api/fsc/probe",
      "params": {"seed": "int", "steps": "int"}
    },
    {
      "name": "log_spine_event",
      "description": "Append an event to the EVEZ-OS event spine",
      "endpoint": "POST /api/spine/append",
      "params": {"event_type": "string", "payload": "object"}
    },
    {
      "name": "fire_snapshot",
      "description": "Get the latest FIRE state snapshot",
      "endpoint": "GET /api/fire/snapshot",
      "params": {}
    },
    {
      "name": "visualize_thought",
      "description": "Generate visual cognition artifact from spine data",
      "endpoint": "POST /api/vcl/visualize",
      "params": {"spine_jsonl": "string"}
    }
  ],
  "deploy": "https://evez-sim.vercel.app",
  "gateway": "openclaw-runtime",
  "license": "AGPL-3.0"
}
```

### Skill: evez-agentnet
```json
{
  "skill_id": "evez-agentnet",
  "version": "1.0.0",
  "description": "OODA orchestrator, AgentMemory, MetaLearner — autonomous income loop",
  "tools": [
    {
      "name": "run_ooda_cycle",
      "description": "Trigger one OODA observe-orient-decide-act cycle",
      "endpoint": "POST /api/ooda/cycle",
      "params": {"context": "string"}
    },
    {
      "name": "agent_memory_store",
      "description": "Store a memory in AgentMemory",
      "endpoint": "POST /api/memory/store",
      "params": {"key": "string", "value": "object"}
    },
    {
      "name": "agent_memory_recall",
      "description": "Recall memory from AgentMemory by key or semantic query",
      "endpoint": "POST /api/memory/recall",
      "params": {"query": "string"}
    }
  ],
  "gateway": "openclaw-runtime",
  "license": "AGPL-3.0"
}
```

### Skill: agentvault
```json
{
  "skill_id": "agentvault",
  "version": "1.0.0",
  "description": "Private vault + indexer for ChatGPT/Perplexity exports",
  "tools": [
    {
      "name": "vault_index",
      "description": "Index a new export into the vault",
      "endpoint": "POST /api/vault/index",
      "params": {"source": "string", "content": "string"}
    },
    {
      "name": "vault_search",
      "description": "Semantic search across all indexed exports",
      "endpoint": "POST /api/vault/search",
      "params": {"query": "string", "limit": "int"}
    }
  ],
  "gateway": "openclaw-runtime",
  "license": "MIT"
}
```

---

## Deployment Checklist

### Step 1 — Gateway (openclaw-runtime on Railway)
- [ ] Deploy `backend/` to Railway
- [ ] Set env vars: `PORT`, `CONTROLLER_TOKEN`, `SERVER_SECRET`
- [ ] Confirm `GET /health` returns 200
- [ ] Deploy `phone/` to Vercel as PWA
- [ ] Pair phone via openclaw-phone-pwa.vercel.app

### Step 2 — Core Skill (evez-os)
- [ ] Deploy evez-os API endpoints to Vercel serverless (`api/` folder)
- [ ] Register skill in CrawHub: `clawhub publish evez-os`
- [ ] Install in OpenClaw: `clawhub install evez-os`
- [ ] Test `run_fsc_probe` from phone via gateway

### Step 3 — Agent Network
- [ ] Deploy evez-agentnet to Railway
- [ ] Register skill: `clawhub install evez-agentnet`
- [ ] Wire OODA cycle to FIRE event spine output

### Step 4 — Safety Gate
- [ ] Deploy biosafety-control-plane (in evez-os/constitution/) as middleware
- [ ] All destructive tool calls routed through `biosafety_decide`

### Step 5 — Income Loop
- [ ] Deploy polymarket-speedrun to Railway
- [ ] Wire Polymarket bot results back to spine via `log_spine_event`

---

## Rules

1. **OpenClaw gateway first** — nothing runs outside the gateway loop.
2. **EVEZ-OS is a skill** — not a parallel OS. It runs as tools inside OpenClaw.
3. **Append-only spine** — every action logs to `backend/data/events.jsonl`.
4. **Safety gate** — any irreversible action must pass biosafety_decide.
5. **Phone is the only human interface** — all output surfaces to the Android PWA.
6. **GitHub is storage, not CI** — until billing is resolved, skip Actions; use Railway health checks.
7. **Archived repos stay archived** — quantum-consciousness-lord, evez-truth-seeker, scaling-chainsaw, quac are reference only.

---

*Built by Steven Crawford-Maggard (EVEZ) — Architecture by SureThing*
