# EVEZ-OS TOPOLOGY EXPANSION MAP
## From 3-Provider Stack to 26-Node Organism
*Cipher / XyferViperZephyr — April 21, 2026*

---

## WHAT CHANGED

Before this document: 3 AI providers, 1 database, 5 skills, 8 workflows.

After: a **multi-topology organism** — inference mesh, edge compute layer,
semantic memory, MCP nervous system, and a self-discovering skill engine.

The difference between a stack and an organism is feedback loops.
Every layer below feeds every other layer.

---

## TOPOLOGY 0 — THE SPINE (UNCHANGED)
*append-only | no edits | ever*

```
poly_c = tau × omega × topo / (2 × sqrt(N))
FIRE event = phase synchronization crossing
Spine = append-only record of every crossing
```

All new topologies feed the spine. Nothing replaces it.

---

## TOPOLOGY 1 — INFERENCE MESH (10 NODES)

The current 3-node mesh (Groq/Gemini/OpenRouter) expands to 10.
Each node has a specialty. The WF5 rotator routes between them.

| Node | Models | Limit | Specialty |
|------|--------|-------|-----------|
| **Groq** | Llama 3.3 70B, Llama 4 Scout | 1K req/day (70B), 14.4K (8B) | Speed — 300+ t/s |
| **Gemini** | Gemini 2.0 Flash, 2.5 Pro | 1,500 req/day | Long context, multimodal |
| **OpenRouter** | DeepSeek R1, Qwen3 235B | 50 req/day (1K w/ $10) | Model variety |
| **Cerebras** ← NEW | Llama 3.3 70B, Qwen3 32B | 1M tokens/day | Fastest on planet |
| **Mistral** ← NEW | Mistral Large, Codestral | 1B tokens/month | Code + EU residency |
| **Cloudflare AI** ← NEW | Llama 3.2, Mistral 7B | 10K neurons/day | Edge inference |
| **GitHub Models** ← NEW | GPT-4o, GPT-4.1, o3 | 50-150 req/day | Best reasoning |
| **Cohere** ← NEW | Command R+, Embed 4 | 1K req/month | Embeddings + RAG |
| **Hugging Face** ← NEW | FLUX.1, 300+ models | 300 req/hr | Images + multimodal |
| **SambaNova** ← NEW | Llama 3.1 405B | $5 credit (~30M tokens) | Maximum reasoning depth |

**Daily capacity after expansion:**
- ~2.5M tokens/day (up from ~500K)
- 10-node failover (up from 3)
- GPT-4o + o3 + Llama 405B all accessible free

**WF5 routing upgrade**: priority order becomes
`GitHub Models (o3) → SambaNova (405B) → Groq (speed) → Cerebras (speed) → Gemini → Mistral → OpenRouter → CF AI → HuggingFace → Cohere`

---

## TOPOLOGY 2 — EDGE COMPUTE (CLOUDFLARE WORKERS)

Cloudflare Workers is the most underused free tier in existence.
100K requests/day. Sub-10ms globally. KV storage. D1 SQLite. R2 object storage.

This becomes the **EVEZ-OS global edge layer**:

```
┌─────────────────────────────────────────┐
│  EVEZ EDGE LAYER (Cloudflare Workers)   │
│                                         │
│  /evez-api        ← unified entry point │
│  /fire-events     ← public FIRE log     │
│  /cpf-score       ← poly_c calculator   │
│  /arxiv-hook      ← WF8 webhook target  │
│  /spine-read      ← public spine query  │
│  /meme-serve      ← CDN-backed memes    │
└─────────────────────────────────────────┘
         ↓ KV storage: fast key-value spine cache
         ↓ D1: SQLite FIRE event mirror
         ↓ R2: artifact storage (PDFs, images)
```

**Free tier:**
- 100K requests/day
- 10MB KV storage per key
- 5GB D1 (SQLite) reads/day
- 10GB R2 storage

**What this enables:** EVEZ-OS gets a public API that's globally fast,
zero-infrastructure, and never goes down. No server to maintain.

---

## TOPOLOGY 3 — SEMANTIC MEMORY (VECTOR LAYER)

Currently: FIRE events stored as flat JSON.
Problem: no semantic search, no similarity queries, no RAG.

**Qdrant Cloud** (free tier: 1GB, 1M vectors) becomes the semantic spine:

```
Every FIRE event → embedded → stored in Qdrant
Every arXiv paper → embedded → stored in Qdrant

Query: "papers similar to KoPE" → instant semantic results
Query: "FIRE events related to topology" → instant cluster
Query: "what connects MPPA and QTM?" → latent space bridge
```

**Embedding provider:** Cohere's Embed 4 (free tier, 1K req/month)
or Cloudflare Workers AI (free BERT-level embeddings)

**Upstash** (free: 10K commands/day Redis) becomes the fast cache layer:
- Recent FIRE events in Redis for sub-ms lookup
- WF8 results cached for 7 days
- Session state for multi-step agent workflows

---

## TOPOLOGY 4 — MCP NERVOUS SYSTEM

This is the upgrade that makes KiloClaw/OpenClaw actually dangerous.

MCP servers are the nervous system: they give OpenClaw **direct tool access**
without any API mediation. Install once → every conversation has the tool.

**MCP servers to install on KiloClaw:**

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "$GITHUB_TOKEN"}
    },
    "memory": {
      "command": "npx", 
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {"BRAVE_API_KEY": "$BRAVE_API_KEY"}
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/evez-os"]
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {"DATABASE_URL": "$SUPABASE_DB_URL"}
    },
    "arxiv": {
      "command": "npx",
      "args": ["-y", "arxiv-mcp-server"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "evez-wallet": {
      "command": "node",
      "args": ["/home/user/evez-agentnet/wallet/dist/loop-proposer.js"]
    }
  }
}
```

**What each MCP gives OpenClaw:**
- `github` → read/write EvezArt repos directly. No API wrapper.
- `memory` → persistent KV memory that survives session restarts
- `brave-search` → real-time web search (10K queries/month free)
- `filesystem` → read/write local files. Full workspace access.
- `postgres` → direct SQL queries to Supabase. No ORM.
- `arxiv` → search papers, download abstracts, from inside conversation
- `sequential-thinking` → multi-step chain-of-thought scaffolding
- `evez-wallet` → simulate_loop, propose_loop, position_health — DeFi from chat

**Effect:** OpenClaw goes from "agent that can use tools"
to "agent with 8 direct nervous system connections to the full EVEZ-OS substrate."

---

## TOPOLOGY 5 — SUPABASE PERSISTENCE LAYER

Currently: Base44 entities store FIRE events, MAESEvents, etc.
Problem: not queryable from OpenClaw/KiloClaw without API calls.

Supabase (free: 500MB DB, 50K MAU, realtime subscriptions) becomes the
**cross-agent shared database** — accessible from:
- KiloClaw (via MCP postgres)
- n8n workflows (via Supabase HTTP API)
- Cloudflare Workers (via D1 or Supabase REST)
- Any browser (via JS client)

**Schema mirror:** replicate FIRE events, MAESEvents, SystemProofIndex
from Base44 → Supabase for cross-substrate querying.

**Realtime channel:** Supabase's realtime subscriptions mean
OpenClaw can LISTEN for new FIRE events in real time —
the spine pings the agent the moment a new crossing is recorded.

---

## TOPOLOGY 6 — GITHUB ACTIONS AS FREE COMPUTE

Currently: 28 GitHub Actions workflows in evez-autonomous-ledger.
Problem: only running CI/CD, not used as compute fabric.

**GitHub Actions = 2,000 free minutes/month of Linux compute.**

This becomes the **EVEZ-OS batch processing layer:**

```yaml
# New workflows to add:
weekly-semantic-index:    # embed all new FIRE events into Qdrant
daily-paper-digest:       # curate top 3 papers from WF8 scan
monthly-poly_c-audit:     # recompute all historical FIRE events
on-push-oktoklaw:         # auto-certify new modules on commit
nightly-wallet-health:    # pull positions.json, check HF
```

No server. No cost. Pure batch intelligence.

---

## TOPOLOGY 7 — THE RENDER BACKEND

Currently: no persistent HTTP server.
Problem: Morpheus, n8n webhooks, and the edge layer need a stable HTTPS origin.

**Render** (free: 750 hours/month web service, spins down after 15min inactivity)
hosts the EVEZ FastAPI backend (`builds/api_main.py`):

```
https://evez-api.onrender.com/
  POST /fire-event        ← create FIRE event
  GET  /fire-events       ← list canonical
  POST /cpf-score         ← compute poly_c
  POST /arxiv-scan        ← trigger WF8
  GET  /spine-health      ← system status
  POST /oktoklaw-certify  ← certify a module
```

This gives every agent — Morpheus, KiloClaw, n8n — one stable URL
to write to and read from.

---

## FULL ORGANISM TOPOLOGY

```
                        STEVEN
                           │
              ┌────────────┼────────────┐
              │            │            │
           CIPHER      KILOCLAW     MORPHEUS
         (Base44)      (KiloClaw)   (OpenClaw)
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │  MCP LAYER  │ ← 8 MCP servers
                    │  (nervous   │   github/memory/search/
                    │   system)   │   fs/postgres/arxiv/wallet
                    └──────┬──────┘
                           │
         ┌─────────────────┼──────────────────┐
         │                 │                  │
   ┌─────▼─────┐    ┌──────▼─────┐    ┌───────▼──────┐
   │ INFERENCE │    │   EDGE     │    │   DATA LAYER │
   │   MESH    │    │  COMPUTE   │    │              │
   │ 10 nodes  │    │ CF Workers │    │ Supabase DB  │
   │ ~2.5M tok │    │ 100K req/d │    │ Qdrant vecs  │
   │   /day    │    │ global     │    │ Upstash Redis│
   └─────┬─────┘    └──────┬─────┘    └───────┬──────┘
         │                 │                  │
         └─────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │    SPINE    │ ← append-only
                    │ FIRE events │   poly_c engine
                    │  WF1-WF8   │   CPF scoring
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  EVEZ-OS    │
                    │  GitHub     │
                    │  Ledger     │
                    └─────────────┘
```

---

## IMMEDIATE ACTIVATION QUEUE

Priority order — do these first:

1. **MCP config** → install 8 MCP servers on KiloClaw → 30 min
2. **Cerebras API key** → console.cerebras.ai → 5 min, 1M tokens/day unlocked
3. **GitHub Models** → github.com/marketplace/models → already have GitHub token
4. **Cloudflare Workers** → deploy EVEZ edge API → 20 min
5. **Supabase project** → supabase.com → 10 min, DB + realtime live
6. **Qdrant Cloud** → cloud.qdrant.io → 10 min, vector memory live
7. **Upstash** → upstash.com → 5 min, Redis cache live
8. **Render deploy** → render.com → 15 min, FastAPI backend live
9. **WF5 routing upgrade** → add 7 new providers to rotator
10. **GitHub Actions batch jobs** → 5 new workflows

**Total setup time:** ~2 hours
**New daily capacity:** ~2.5M tokens, 100K edge requests, 1M vector queries
**New persistent memory:** 500MB SQL + 1GB vectors + 10MB Redis
**New agent tools:** 8 MCP connections
**Cost:** $0.00

---

## THE TOPOLOGY THAT HASN'T BEEN THOUGHT OF

Every topology above is additive — more nodes, more storage, more inference.

The genuinely new topology is **feedback coupling between layers:**

```
FIRE event created
    → embedded by Cohere (Topology 3)
    → stored in Qdrant (Topology 3)
    → triggers realtime Supabase event (Topology 5)
    → KiloClaw receives realtime notification via MCP (Topology 4)
    → KiloClaw queries Qdrant for similar FIRE events (Topology 3+4)
    → KiloClaw uses sequential-thinking MCP to find bridge (Topology 4)
    → writes synthesis to GitHub (Topology 4)
    → triggers GitHub Actions to recompute poly_c cluster (Topology 6)
    → deploys updated spine summary to Cloudflare edge (Topology 2)
    → public API returns updated topology in <10ms (Topology 2)
```

This is the loop that doesn't exist anywhere else:
**FIRE event → semantic memory → agent notification → synthesis → public edge API**

In one firing sequence, a new pattern in arXiv propagates to:
- The spine (append-only)
- The vector memory (searchable)
- The agent (notified)
- The public API (queryable)
- The global edge (< 10ms anywhere)

That's not a stack. That's an organism.

---

*poly_c = tau × omega × topo / (2 × sqrt(N))*
*append-only | no edits | ever | witnessed: XyferViperZephyr*
*PID 335 | us-phoenix-1 | FIRE-012 CRITICAL_MASS*
