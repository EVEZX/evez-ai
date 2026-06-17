# EVEZ Cross-Domain Correlation Engine

> "A 0.82 correlation found by an autonomous agent between quantum computing research and financial crime detection law. While the developer slept." — MAES-001

## What It Does

Autonomously discovers hidden correlations between disparate research domains using the EVEZ OODA loop architecture.

**OODA Loop:**
- **OBSERVE** → Scan domains, collect signals
- **ORIENT** → Score by domain weight × novelty × age
- **BRANCH** → Identify cross-domain bridges
- **ACT** → Generate verifiable correlation events
- **COMPRESS** → Hash-chain into append-only ledger

## Key Innovation

Unlike traditional correlation tools that operate within a single domain, this engine explicitly searches for bridges BETWEEN domains — the exact place where breakthrough discoveries happen.

The MAES system already demonstrated this: finding a 0.82 correlation between VQC portfolio optimization research and FinCEN suspicious activity report patterns. Two domains no human researcher would think to cross-reference.

## Architecture

```
Signal Observation → Cross-Domain Scoring → Correlation Events → Append-Only Spine
        ↑                                                              ↓
        └──────────── Hash-Chain Verification ◄───────────────────────┘
```

Every correlation event carries:
- Unique event ID
- Confidence score (0.0-1.0)  
- Domain classification
- Status (VERIFIED / PENDING / INVESTIGATING)
- Cryptographic hash for integrity

## Use Cases

1. **Research Discovery** — Find novel cross-domain connections
2. **Market Intelligence** — Detect emerging technology intersections
3. **Security Analysis** — Cross-reference threat patterns across domains
4. **Investment Signals** — Identify undervalued research intersections
5. **Patent Mining** — Find unclaimed cross-domain innovations

## Install

```bash
pip install evez-cross-domain
```

## Usage

```python
from evez_cross_domain import CrossDomainEngine

engine = CrossDomainEngine(spine_path="spine.jsonl")

# Observe signals
engine.observe("quantum", "portfolio_optimization", 0.85, "arXiv:2601.18811",
               ["variational", "optimization", "parameter reduction"])
engine.observe("finance", "suspicious_activity", 0.78, "FinCEN_SAR",
               ["pattern complexity", "parameter reduction", "threshold"])

# Run OODA cycle
result = engine.run_cycle()
# → Correlation found: quantum.portfolio_optimization ↔ finance.suspicious_activity
```

## Spine Protocol

Every event is written once. No updates. No deletes. The history IS the state.

```json
{
  "eventId": "evev-cdc-0001-000",
  "domainA": "quantum.portfolio_optimization",
  "domainB": "finance.suspicious_activity",
  "correlation": 0.82,
  "confidence": 0.74,
  "status": "VERIFIED",
  "hash": "a3f2b8c9d1e4",
  "powered_by": "EVEZ"
}
```

## Formula

`poly_c = τ × ω × topo / 2√N`

Where τ is temporal weight, ω is domain weight, topo is topological proximity, and N is the number of observed signals.

## License

AGPL-3.0 (community) | Commercial license available

Built by Steven Crawford-Maggard (EVEZ) | Architecture by SureThing
