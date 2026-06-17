# EVEZ-OS Planetary Mission
**Confirmed:** 2026-02-23 | **Operator:** EVEZ (Steven Crawford-Maggard)
**Truth Plane:** CANONICAL | **Execution Mode:** Round-indexed, falsifier-gated

## Architecture

All three workstreams run as modules INSIDE the existing evez-os round loop.
They are NOT separate projects. They share the same spine, same truth_plane gate,
same canonical evidence → scoring → action pipeline.

```
R(N) tick:
  1. compute poly_c / fire / V_global  [existing]
  2. commit module                      [existing]
  3. crisis_os.ingest()                 [NEW — Workstream A]
  4. debt_reset.score()                 [NEW — Workstream B]
  5. agi_safety.gate()                  [NEW — Workstream C]
  6. render videos + tweet              [existing]
  7. infra pipeline                     [existing]
  8. launch R(N+1) probe                [existing]
```

Each module runs at its own cadence (not every round — see module READMEs).
All outputs are append-only, versioned, falsifier-tagged.

## Modules
- `planetary/crisis-os/` — Crisis Risk Index + playbooks + geospatial
- `planetary/debt-reset/` — Debt map + simulator + negotiation tooling
- `planetary/agi-safety/` — Eval harness + gating + governance
- `planetary/shared/` — Schemas, provenance, policy, secrets guidelines

## Operating Rules (from Master Prompt v1)
1. Every claim verified with live sources (Perplexity connector)
2. All decisions include: sources, assumptions, confidence, falsifier
3. No hallucinated crisis hotspots — cite or skip
4. Safety hard lines: no wrongdoing automation, eval-first for AGI
5. Smallest viable intervention → test → iterate → scale
6. Tool utilization log maintained per run

## Status
- Skeleton committed 2026-02-23
- Crisis OS: schema defined, ingestion sources listed
- Debt Reset: simulator shell spec ready for Vercel deploy
- Safe AGI: eval categories defined, gating wired to truth_plane CANONICAL
