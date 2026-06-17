# Game Agent Infra

Wheel-rooted (cognitive tiering) + FSC-measured (failure-surface cartography) + retrocausal-safe infrastructure for EVEZ-OS agents.

## Core Principles
- Immutable Event Spine (JSONL) — never rewrite history
- Pending vs Final explicit in every API response
- Every cycle records: anomaly, ring_estimate, controlled_reduction, Σf, CS, PS, Ω
- Retrocausal safety: speculate → fork → score → promote only on finality gate

## Quick Start
```bash
python -m game_agent_infra.cli init --seed 42
python -m game_agent_infra.cli cycle --ring R4 --anomaly "DNS resolution timeout"
```

See `docs/` for architecture diagrams and `core/` for the implementation.