# EVEZ Continuity Engine

A self-contained continuity + diagnostics spine:
- **Wheel-rooted cognition map (R1–R7)**
- **Bidirectional Collapse Protocol**
- **Failure-Surface Cartography (Σf / CS / PS / Ω)**
- Append-only **Event Spine** (JSONL)
- Tiny CLI to append cycles + generate diagrams

## Quickstart
```bash
python tools/evez.py init
python tools/evez.py cycle --anomaly "what broke" --ring R4
python tools/evez.py diagram
```

## Directory layout
- `continuity/` — identity capsule + boot prompt + protocols
- `spine/` — EVENT_SPINE.jsonl + SESSION_HANDOFF.md
- `schemas/` — FSC schema
- `docs/` — one-sheet + generated Mermaid/DOT diagrams
- `tools/` — CLI + generators
- `examples/` — sample cycles

## Hard rules
- Raw transcripts / event spine are **immutable**.
- Memories/summaries are **versioned** and must include provenance.
- Hypotheses must be labeled as hypotheses.

## Why it works
It turns “remembering” into a deterministic ritual:
Capsule + Handoff + Event Spine ⇒ immediate resumption with no re-derivation.
