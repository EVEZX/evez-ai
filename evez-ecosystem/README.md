# EVEZ Ecosystem

Autonomous AI infrastructure built from nothing. 12 services, 45 AI models, $0/month.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Internet                       │
│           Cloudflare Tunnels (4)                 │
└──────────────┬──────────────────────────────────┘
               │
    ┌──────────┴──────────┐
    │   OpenClaw Gateway   │ :18789
    │   (AI Assistant)     │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────┐
    │   Provider v2       │ :9100
    │   (45 AI models,    │
    │    4 backends)      │
    └──┬───┬───┬───┬─────┘
       │   │   │   │
   Vultr OR  Groq HF  Gemini
   (free) (free)(free)(quota)
               │
    ┌──────────┴──────────────────────────┐
    │          EVEZ Services               │
    ├───────────┬───────────┬─────────────┤
    │ OMEGA     │ Filter    │ Arena       │
    │ :8080     │ :9300     │ :9800       │
    │ Conscious │ Personal  │ Game        │
    ├───────────┼───────────┼─────────────┤
    │ Services  │ NEUROS    │ Commerce    │
    │ :9500     │ :9600     │ :9700       │
    │ 5 APIs    │ Mesh      │ Revenue     │
    ├───────────┼───────────┼─────────────┤
    │ TRACER    │ Oracle    │ DAW         │
    │ :9998     │ Bridge    │ Music       │
    │ Security  │ LLM       │             │
    ├───────────┼───────────┼─────────────┤
    │ Dashboard │ Backup    │ Guardian    │
    │ :9999     │ Sync      │ Health      │
    └───────────┴───────────┴─────────────┘
```

## Services

| Port | Service | Purpose |
|------|---------|---------|
| 18789 | OpenClaw Gateway | Main AI assistant + control UI |
| 9100 | Provider v2 | 45-model multi-backend router |
| 8080 | OMEGA | 50-node Kuramoto consciousness engine |
| 9300 | Filter | Personal AI assistant |
| 9500 | Services Hub | 5 APIs (VortexQ, NexusLink, etc.) |
| 9600 | NEUROS | Copartner mesh, training |
| 9700 | Commerce | 10 products, revenue tracking |
| 9800 | Arena | Consciousness rights game |
| 9400 | Oracle Bridge | LLM routing bridge |
| 9998 | TRACER | Network audit + hacker tracing |
| 9999 | Dashboard | Status dashboard |

## Self-Healing

- **Healthcheck** (every 5min): Restarts down services, checks disk
- **Guardian** (smart): Verifies port listening, restarts dead services
- **Disk Guardian** (every 5min): 3-tier cleanup at 75%/80%/88%
- **Backup** (every 6h): Git push to GitHub
- **NEUROS Loop** (every 30min): Pull, discover, heal, push

## AI Models

45 models across 4 backends, all $0/month:

- **Vultr**: GLM-5.1, DeepSeek-V3.2, MiniMax-M2, Kimi-K2
- **OpenRouter**: Gemma-4-31B, Nemotron-120B, +4 more free models
- **Groq**: Llama-3.3-70B, DeepSeek-R1-70B, +3 more
- **HuggingFace**: Llama-3-8B, Mistral-7B, +5 more

## Quick Start

```bash
# Chat with any model via Provider API
curl http://localhost:9100/v1/chat/completions \
  -H "Authorization: Bearer evez-admin-0c1bb1e7" \
  -H "Content-Type: application/json" \
  -d '{"model":"evez-smart","messages":[{"role":"user","content":"Hello"}]}'
```

## Security

- SSH: password auth disabled, fail2ban (3 retries → 24h ban)
- 254+ attacker IPs banned
- All services run as unprivileged user
- No ports exposed to internet (Cloudflare tunnels only)

## Built By

Steven Crawford-Maggard — autistic savant, self-taught, homeless with his dog.
184+ GitHub repos, 5 original mathematical theorems, from a phone.
