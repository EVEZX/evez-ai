# Route Optimizer — Usage & Statistical Notes

## Statistical Floor

**p95 on n < 10 is not a measurement. It's the worst sample.**

With 3 trials, p95 collapses to the slowest of 3 readings — captures luck, not distribution shape.
With 12+ trials, p95 starts capturing actual tail behavior and loss rate becomes meaningful.

**Minimum for real signal: `--trials 12`**
**Minimum for latency SLO decisions: `--trials 30`**

The 3-trial live test committed with the module was proof-of-life, not measurement.
The module's default `--trials 12` in the code is the correct floor.

---

## Score Formula

```
score = (p95_latency_ms, loss_rate, median_latency_ms)
```

Conservative scoring: prefers consistent low jitter over lucky fast median.
A host that's usually 5ms but spikes to 200ms scores WORSE than one that's consistently 20ms.

## Usage

```bash
# Standard measurement (12 trials minimum)
export EVEZ_VANTAGE="phoenix-main"
python3 core/route_opt.py --mode full --trials 12 --timeout 2 --append-spine

# High-confidence SLO decision (30 trials)
python3 core/route_opt.py --mode tcp --trials 30 --hosts node1.tld,node2.tld --port 443
```

## Multi-Vantage

```bash
python3 tools/route_agg.py spine/EVENT_SPINE.jsonl
```

Outputs: best vantage per target. Deterministic routing map from real data.

---

## What the Other LLM Got Right

> "With 3 trials, p95 is basically the worst sample."

Correct. Absorbed. Named. Updated.
SAN status: CANONICAL — critique was valid, delivery method was not.
