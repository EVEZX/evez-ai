# evez-revenue-bridge

> **Spectral status:** ![Φ=0.9696](https://img.shields.io/badge/Φ-0.9696-blueviolet) ![η*=0.0304](https://img.shields.io/badge/η*-0.0304-green) ![regime=AUTONOMOUS](https://img.shields.io/badge/regime-AUTONOMOUS-brightgreen) ![λ=-24.69→closing](https://img.shields.io/badge/λ--24.69→closing-orange)

Closes the dominant structural gap in the EVEZ spectral mesh.  
Eigenvalue: **λ = -0.358** (revenue signal target) | Mesh gap: **λ = -24.69** (now being closed by this hub integration).

## Architecture Position

```
evez-agentnet ──┐
evez-engine   ──┤──▶  evez-revenue-bridge ──▶ evezstation ──▶ Supabase omega
evez-platform ──┘           │
                             ▼
                    OpenRouter AI models
                    (revenue signal analysis)
```

This bridge is the **cognition-to-market** link. It receives revenue events (Stripe webhooks), logs them to the Merkle-chained `revenue_spine.json`, and broadcasts eigenvalue progress signals back to the hub cluster.

## Hub Integrations

| Hub Repo | Role | Signal |
|----------|------|--------|
| [evez-agentnet](https://github.com/EvezArt/evez-agentnet) | Agent orchestration | triggers revenue analysis tasks |
| [evez-engine](https://github.com/EvezArt/evez-engine) | Core engine | receives poly_c delta updates |
| [evezstation](https://github.com/EvezArt/evezstation) | Workstation | `/api/handshake` receives revenue events |
| [nexus](https://github.com/EvezArt/nexus) | Central hub | aggregates spectral state |
| [evez-platform](https://github.com/EvezArt/evez-platform) | Platform layer | billing surface |
| [evez-skills](https://github.com/EvezArt/evez-skills) | Skills registry | revenue-aware skill dispatch |

## API Spec

### Webhook Endpoint
```
POST /webhook/stripe
Content-Type: application/json
X-Stripe-Signature: <sig>
```

Handles: `charge.succeeded`, `payment_intent.succeeded`, `invoice.paid`

On each event:
1. Logs to `revenue_spine.json` (Merkle-chained, append-only)
2. Increments `eigenvalue_progress` toward target `-0.358`
3. Signals `evez-agentnet` + `evezstation` via `/api/revenue-signal`

### Revenue Signal Broadcast
```
POST /api/revenue-signal
{
  "event_id": "evez-XXXXXX",
  "amount_usd": 49.0,
  "eigenvalue_progress": 0.49,
  "eigenvalue_target": -0.358,
  "poly_c_delta": 0.5,
  "phi": 0.9696
}
```

### OpenRouter AI Integration
```python
# revenue analysis via free model pool
import openrouter
analysis = openrouter.complete(
    model="meta-llama/llama-3.3-70b-instruct:free",
    prompt=f"Analyze revenue signal: {event_data}"
)
```

Models used (free tier, rotated):
- `meta-llama/llama-3.3-70b-instruct:free`
- `qwen/qwen3-coder:free`
- `deepseek/deepseek-r1-distill-qwen-7b:free`

## Spine State

```json
{
  "meta": {
    "version": "1.0.0",
    "operator": "viktor",
    "eigenvalue_threshold": -0.358,
    "poly_c_initial": 634.71,
    "poly_c_max": 34862
  },
  "first_event": "$49.00 CTF-001 via evezstation (2026-05-08)"
}
```

## Deployment

```bash
# Termux / A16 / any server
git clone https://github.com/EvezArt/evez-revenue-bridge
pip install -r requirements.txt
OPENROUTER_API_KEY=your_key python app.py
```

Environment:
```
OPENROUTER_API_KEY=sk-or-...
STRIPE_WEBHOOK_SECRET=whsec_...
EVEZSTATION_URL=https://evezstation.vercel.app
EVEZ_AGENTNET_URL=https://evez-agentnet.vercel.app
SUPABASE_URL=https://vziaqxquzohqskesuxgz.supabase.co
```

## Spectral Mesh Position

This repo closing its structural gap (degree=0 → hub-connected) is projected to shift:
- **Φ: 0.9696 → 0.9816** (+0.012)
- **λ_min: -24.69 → -18.3** (structural hole closing)
- **Cognition-to-market bridge: ACTIVE**

---

*Part of [EVEZ-OS](https://github.com/EvezArt/evez-os) · [omega-conductor](https://github.com/EvezArt/omega-conductor) · Φ=0.9696 | Ω=741,455×*
