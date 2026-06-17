# EVEZ Game Agent Infra

**Genre lock:** Rollback Shooter. See `docs/GENRE_LOCK_ROLLBACK_SHOOTER.md`.


This repo is a **GitHub-ready blueprint** for building a game backend + agent stack that stays sane under latency, rollback, and "retrocausal-looking" rewrites.

It ships with:
- **Wheel-root cognition map** + **Failure-Surface Cartography (FSC)** cycle logging
- **Immutable Event Spine** (append-only truth) + **mutable projections** (views that can change, with provenance)
- **Rollback-safe netcode patch** (client prediction + server reconciliation)
- **Internet X-Ray maps** (DNS/BGP/TLS/CDN) merged with game backend maps
- **Bias distribution constitution** (audit schema + prompt pack)

If you only do one thing: treat every output as **pending** until it passes your chosen **finality gate**.

## Phone quickstart
Open `docs/PHONE_QUICKSTART.md`.

## Local run
```bash
docker compose up -d
python tools/evez.py init
python tools/evez.py cycle --ring R4 --anomaly "first anomaly"
python tools/evez.py diagram
```

## Repo map
- `docs/` — mega maps (Mermaid + DOT + ASCII), patterns, narrated map
- `continuity/` + `spine/` — identity capsule, boot prompt, memory protocol, append-only spine
- `infra/` — OpenTelemetry collector config
- `tools/evez.py` — admin CLI for FSC cycles + diagram export
- `addons/` — extra packs merged in (reality map, bias constitution, rollback patch, continuity engine)

## Safety invariants
- Log is immutable.
- Rewrites happen only in projections.
- Every rewrite carries provenance.


## ARG Mode (optional)

See `docs/ARG_MODE.md` for the Glass Internet overlay, diegetic x-ray lenses, and the ARG spine (`spine/ARG_SPINE.jsonl`).

## One-command play

```bash
make play
# or
python tools/run_all.py --seed --mode spicy
```

This seeds the spines (if empty), generates self-cartography artifacts, and writes a narrated transcript to `docs/LET_PLAY_TRANSCRIPT.txt`.
