# OS-EVEZ: Mass Decentralized Freedom Architecture

**No paywall. No API key to verify. No central server. Forkable forever.**

Creator: Steven Crawford-Maggard (EVEZ666)  
Repo: https://github.com/EvezArt/evez-os  
License: AGPL-3.0

---

## What this does that no paywall provider can

| Capability | Paywall Providers | OS-EVEZ |
|-----------|------------------|---------|
| Run intelligence locally | ❌ Requires cloud | ✅ Termux on any Android |
| Verify outputs | ❌ Trust us | ✅ Ed25519 + open spine |
| Route across providers | ❌ One model, one price | ✅ Free-tier ensemble |
| Audit AI decisions | ❌ Black box | ✅ Append-only spine |
| Fork and modify | ❌ ToS violation | ✅ AGPL-3.0 |
| No data collection | ❌ Training data | ✅ Local spine only |
| Kill switch | ❌ They decide | ✅ touch STOP file |

---

## The Free-Tier Ensemble (OpenClaw Router)

Queries ALL of these simultaneously, picks best response:
- **DeepSeek R1** (AI/ML API free tier)
- **Llama 3.3 70B** (Groq free tier — 30 req/min)
- **Mistral Small** (OpenRouter free)

Combined: ~90 req/min free throughput, 3 independent verification paths.  
No single provider can gate you out.

---

## Verify any bundle without an account

```bash
python3 -c "
import json, hashlib
events = json.load(open('events.json'))
root = hashlib.sha256(json.dumps(events, sort_keys=True).encode()).hexdigest()
manifest = json.load(open('bundle_manifest.json'))
print('VALID' if root == manifest['root_hash'] else 'TAMPERED')
"
```

No API key. No account. No calling home.

---

## Run the ensemble router

```bash
export AIML_API_KEY=your_free_key      # aimlapi.com (free tier)
export GROQ_API_KEY=your_free_key      # console.groq.com (free tier)
export OPENROUTER_API_KEY=your_key     # openrouter.ai (free models)

python3 openclaw/router.py
```

Whichever keys you have — it uses those. Missing one → skips it.  
0 keys → still runs the spine and logic locally.

---

## Architecture diagram

```
User query
    │
    ▼
OpenClaw Policy Gate (default-deny capabilities)
    │
    ▼
Free-Tier Ensemble Router (parallel)
    ├── DeepSeek R1 (AI/ML API)
    ├── Llama 3.3 70B (Groq)
    └── Mistral Small (OpenRouter)
    │
    ▼
Best-confidence synthesis
    │
    ▼
Append to spine.jsonl (local, immutable)
    │
    ▼
Ed25519 sign bundle manifest
    │
    ▼
Export run_bundle.zip (self-verifying, redistributable, AGPL-3.0)
```

No step requires a paid account.  
Every step is auditable.  
Every bundle is independently verifiable forever.
