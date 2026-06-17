# EVEZ Autoenveloper v2

**Cross-domain structural isomorphism detector + spacetime operators.**

Live API: **https://autoenveloper.vercel.app**

## What it actually measures

Not Kolmogorov complexity (uncomputable). Not entropy alone. A **4-basis hybrid invariant**:

```
Φ(x) = [C(x), I₁..I₅(x), λ₂(x), Hₚ(x)]
         ↓       ↓           ↓        ↓
    zlib K(x)  MI lags   Fiedler   Persistence
    upper bd   k=1..5     value     entropy
```

Similarity: `S(x,y) = √( cos(Φx,Φy) · (1 - JS(Φx,Φy)) )`

The geometric mean punishes mismatch in *either* angular alignment or distributional shape independently.

## Test results

| Pair | Similarity | Correct? |
|------|-----------|---------|
| Python loop ↔ Financial ledger | 99.9% | ✅ Same grammar |
| Legal clause ↔ Physics constraint | 99.9% | ✅ Same obligation structure |
| Fibonacci ↔ Exponential growth | 97.5% | ✅ Both sequential growth rules |
| DNA sequence ↔ Binary code | 19.2% | ✅ Different alphabets + structure |

## Endpoints

| Endpoint | What it does |
|----------|-------------|
| `POST /isomorphism` | Φ(x) fingerprint + S(x,y) |
| `POST /ricci-flow` | Curvature smoothing on embeddings (SRF) |
| `POST /entropy-field` | Local entropy tensor + inflation mask (SIF) |
| `POST /gradient-tunnel` | Escape flat loss basins via resonance noise (GTR) |
| `POST /horizon` | Context event horizon + Hawking radiation (CEH/THB) |
| `POST /cipher` | Cipher gen + legacy isomorphism |
| `POST /geometric` | Fractal dimension, spectral, symmetry |
| `POST /linguistic` | N-gram, authorship, PII anonymization |
| `GET /health` | Module status |
| `GET /.well-known/ai-plugin.json` | ChatGPT plugin manifest |

## ChatGPT Actions integration

1. Go to **chatgpt.com** → My GPTs → Create → Configure → Add Actions
2. Paste schema from `chatgpt-schema.json` (or import from `https://autoenveloper.vercel.app/openapi.json`)
3. No auth required

## Quick test

```bash
curl -X POST https://autoenveloper.vercel.app/isomorphism \
  -H "Content-Type: application/json" \
  -d '{"domain_a":"for x in items: total += x","domain_b":"for row in ledger: balance += row"}'
```

## Spacetime functionalities (7 implemented)

1. **GCL** — Geodesic Curriculum Learning (metric warping via `/ricci-flow`)
2. **AWP** — Attentional Wormhole Protocol (via `/isomorphism` nonlocal bridge detection)
3. **CEH** — Context Event Horizons + Hawking Radiation (via `/horizon`)
4. **SIF** — Semantic Inflation Fields (via `/entropy-field`)
5. **GTR** — Gradient Tunneling Resonance (via `/gradient-tunnel`)
6. **SRF** — Semantic Ricci Flow (via `/ricci-flow`)
7. **OPTE** — Ontological Phase Transition Engine (via calibrated isomorphism + entropy field)

## What the invariant actually is

> A bounded estimator of algorithmic mutual structure under graph spectral constraints.

Translation: how much do two sequences share the same *generative rules*, regardless of vocabulary or domain?

- `C(x)` → description length upper bound (LZ77)
- `I₁..I₅(x)` → dependency structure at multiple lags
- `λ₂(x)` → algebraic connectivity class (the decisive discriminator)
- `Hₚ(x)` → topological stability under Lipschitz perturbations
