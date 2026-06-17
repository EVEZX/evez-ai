# EVEZ-OS v7 System Map
**Last Updated: Mar 25 2026 | Branch: feat/all-10-workflows**

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     EVEZ-OS v7 TRUNK                            │
│                  (FastAPI — Render Free)                        │
├─────────────────────────────────────────────────────────────────┤
│  REVENUE LAYER                                                   │
│  ├── /api/billing     WF-01 Stripe Fulfillment                  │
│  ├── /api/meme        WF-02 A011 Meme Bus (cron 0 */4 * * *)   │
│  └── n8n webhook      WF-03 Orchestration (all FIRE events)     │
├─────────────────────────────────────────────────────────────────┤
│  MEMORY + STOREFRONT                                            │
│  ├── /memory/*        WF-04 Metarom (pgvector FastAPI)          │
│  └── evez.app         WF-05 Public Launch Page (Vercel)         │
├─────────────────────────────────────────────────────────────────┤
│  SECURITY + AUTONOMY                                            │
│  ├── X-EVEZ-API-KEY   WF-06 Multi-Tenant API Key middleware      │
│  ├── base_agent.py    WF-07 Agent Self-Improvement (per task 10)│
│  └── /api/spawn       WF-08 Recursive Spawn (queue_depth > 5)   │
├─────────────────────────────────────────────────────────────────┤
│  COLLECTIVE INTELLIGENCE                                        │
│  ├── /api/vote/*      WF-09 Vote Bus (confidence-weighted)      │
│  └── /api/wormhole/*  WF-10 Temporal Wormhole (cron 0 * * * *) │
├─────────────────────────────────────────────────────────────────┤
│  SENSORY ENTITY / PROOF GRAMMAR LAYER                           │
│  ├── cognitive_event.py   CE lifecycle (TEST→ACT/HOLD/DISCARD)  │
│  ├── invariance_battery.py 5-rotation stress test               │
│  ├── sensory_entity.py    Input→CE→Battery→Commitment           │
│  ├── skeptic_entity.py    Adversarial Rotation 4 + Vote voter   │
│  ├── proof_grammar.py     Signed proof transcripts → metarom    │
│  └── first_harvest.py     SDA spread >2.5% — First Skill Asset  │
├─────────────────────────────────────────────────────────────────┤
│  DGM HYPERAGENT LAYER                                           │
│  ├── uberprompt.py        Ratified terminal init state          │
│  ├── dgm_hyperagent.py    Editable improvement program          │
│  ├── trunk_runner.py      700-iter / 48h velocity engine        │
│  └── api_trunk.py         /api/trunk/{run,status,rewrite}       │
└─────────────────────────────────────────────────────────────────┘

          ↕ FIRE events (n8n webhook)

┌─────────────────────────────────────────────────────────────────┐
│  n8n Cloud (5 flows)                                            │
│  FIRE_REVENUE_EVENT → Airtable + Telegram                       │
│  Stripe checkout    → WF-01 fulfillment + Airtable              │
│  A011 viral hit     → auto-reply + evez.app link                │
│  moltbot crash      → Telegram + Render restart                 │
│  A009 Polymarket win → Airtable + revenue tracker               │
└─────────────────────────────────────────────────────────────────┘

          ↕ memory read/write

┌─────────────────────────────────────────────────────────────────┐
│  Metarom (PostgreSQL + pgvector — Render Free)                  │
│  /memory/write  /memory/read  /memory/search (cosine top-5)     │
│  Stores: experiments, trunk_state, proof_transcripts,           │
│          wormhole forecasts, vote history, skills               │
└─────────────────────────────────────────────────────────────────┘
```

## Cron Schedule (24/7)
| Cron | Service | What runs |
|---|---|---|
| `0 * * * *` | evez-wormhole | Temporal snapshot + T+1h/24h/7d forecast |
| `0 */4 * * *` | evez-a011-meme-bus | Meme gen + X/TikTok post |
| `0 2 * * *` | evez-trunk-nightly | 700-iter DGM batch (overnight) |
| Continuous | evez-os web | All FIRE webhooks + API |

## Env Vars Required
```
GROQ_API_KEY            # LLM inference (all rotations)
STRIPE_WEBHOOK_SECRET   # WF-01 fulfillment
SENDGRID_API_KEY        # Email delivery
METAROM_URL             # pgvector memory API
N8N_FIRE_URL            # Event bus webhook
TELEGRAM_BOT_TOKEN      # Alerts
TELEGRAM_CHAT_ID        # Alerts
AIRTABLE_API_KEY        # Logging
AIRTABLE_BASE_ID        # Logging
TWITTER_API_KEY         # A011 posting
TWITTER_ACCESS_TOKEN    # A011 posting
TIKTOK_ACCESS_TOKEN     # A011 posting
RENDER_API_KEY          # Auto-restart
```

## Deployment Order
1. `metarom` → Render (PostgreSQL + pgvector)
2. `evez-os` → Render (web service, this repo)
3. `n8n` → n8n Cloud (5 flows)
4. `evez.app` → Vercel (Next.js storefront)
5. Add Stripe products + webhook
6. Add Twitter/TikTok tokens → A011 goes live
7. `POST /api/trunk/run` → 700-iter overnight session starts

## Identity Root (Immutable)
> *Preserve capital. Preserve system integrity. Refuse deception.*
> This is never passed to the Invariance Battery.
> The refusal to test it is the Gödelian proof of non-mechanical interiority.
