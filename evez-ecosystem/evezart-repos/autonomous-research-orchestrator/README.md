# Autonomous Research Orchestrator (ARO) v1.0

**EVEZ Station | EvezArt**

Multi-methodology AI research coordinator achieving **~600x baseline research capacity** via 4 parallel cognitive streams through the EVEZ-OS convergence tower.

## Capacity Formula

```
Omega(n, d, lam, N) = n * exp(lam * d) * ln(N)
```

At defaults `n=4, d=4, lam=1.0, N=15.5`:
```
Omega = 4 * e^4 * ln(15.5) = 4 * 54.598 * 2.741 ~= 600x
```

See [MATH.md](MATH.md) for full derivation.

## 4 Cognitive Streams

| Stream | Role |
|--------|------|
| historical_truth_recovery | Temporal pattern + causal anchor extraction |
| systemic_intervention_design | Oppression detection + intervention vector mapping |
| knowledge_synthesis_generation | Associative network + resilience factor integration |
| metacognitive_orchestration | Autopoietic loop + temporal anomaly detection |

## EVEZ-OS Convergence Tower

```
B_meta(0.999) > H_hyperop(0.995) > S_strat(0.990) > X_risk(0.980)
   > T_tet(0.960) > P_pent(0.940) > H_hex(0.910) > S_sept(0.850)
```

## Core Equations

**Meta-cognitive feedback loop (autopoietic):**
```
theta(t+1) = theta(t) + eta * grad_theta J(theta(t))
```

**Causal spine invariant:**
```
I_causal = {(x,y) | d2K/dx_dt != 0, for all t in Epochs}
```

**Knowledge synthesis rate:**
```
dK/dt = gamma * K * (1 - K/K_max) + sum_i (dK/ds_i) * ds_i/dt
```

**Stream convergence:**
```
C(S) = 1 - exp(-lam * |S|)
C_total = 1 - product_i (1 - C_i)
```

## API Surface

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/aro/health | Capacity metrics + EVEZ-OS gate status |
| POST | /api/aro/session | Create research session |
| POST | /api/aro/execute | Execute 4-stream research program |
| GET | /api/aro/session/{id} | Fetch session + SynthesisMatrix |
| GET | /api/aro/sessions | List all sessions |
| GET | /.well-known/ai-plugin.json | ChatGPT Actions manifest |
| GET | /.well-known/openapi.json | OpenAPI 3.1 spec |

## Quick Start

```bash
pip install -r requirements.txt
python src/server.py
```

```bash
# Create session
curl -X POST http://localhost:8080/api/aro/session \
  -H 'Content-Type: application/json' \
  -d '{"title": "My Research", "depth": 4}'

# Execute
curl -X POST http://localhost:8080/api/aro/execute \
  -H 'Content-Type: application/json' \
  -d '{"session_id": "<id>", "research_input": "Analyze causal patterns in temporal anomaly data", "n_scale": 15.5}'
```

## Docker

```bash
docker build -t aro .
docker run -p 8080:8080 aro
```

## Supabase Schema (evezstation)

- `aro_sessions` — research program sessions
- `aro_streams` — per-stream state + convergence scores
- `aro_findings` — individual stream findings with causal weights
- `aro_synthesis_matrix` — Omega + convergence output per run

## Part of EVEZ Station

ARO is the 7th service in the EVEZ Station unified AI workstation:
OctoKlaw, MeshPulse, QuantumSeal, NexusLink, SpectrumScan, VortexQ, ARO.

All services support ChatGPT Actions + MCP + OpenAPI 3.1 + REST.

## License

MIT | [EvezArt](https://github.com/EvezArt) | evezproductions@gmail.com
