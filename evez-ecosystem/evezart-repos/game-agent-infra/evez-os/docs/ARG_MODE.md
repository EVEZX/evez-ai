# ARG Mode — Glass Internet Overlay

This repo ships as a rollback-shooter infrastructure **and** an optional Alternate Reality Game (ARG) overlay.

**Core idea:** every real engineering artifact (DNS/BGP/TLS/CDN, matchmaking/auth/state/WS, rollback, FSC) is also a *diegetic* in-game system.
Players do not read dashboards — they *wear* an X-Ray visor that renders **truth-planes**:

- **Pending (perception):** what the client sees now
- **Final (canon):** what the authoritative spine says after finality
- **Provenance:** *why* a rewrite occurred

ARG mode never fakes physics. It dramatizes the exact same mechanics:
append-only event spine, mutable projections, and explicit finality.

## What changes in ARG mode

- A second append-only log: `spine/ARG_SPINE.jsonl` (clue drops + diegetic messages)
- A schema: `schemas/arg_schema.json`
- A CLI extension: `python tools/evez.py arg-init`, `arg-drop`, `arg-narrate`
- A set of ready-to-use "Internet X-Ray" diegetic lenses in `arg/xray/`

## Safe constraints

This ARG overlay is for **your game world**. It is not a toolkit to manipulate real people.
All “psyop” energy is routed inward: it is used to catch **premature certainty** and force evidence.

## Quick start

1. Initialize spines:
   - `python tools/evez.py init`
   - `python tools/evez.py arg-init`

2. Emit a drop:
   - `python tools/evez.py arg-drop --lobby BGP --severity 3 --tag "route-ghost" --msg "The path you trusted is dead. Prove it."`

3. Render narrated output (diegetic):
   - `python tools/evez.py arg-narrate --tail 20`

See also: `docs/LETS_PLAY_ADMIN_NARRATION.md`
