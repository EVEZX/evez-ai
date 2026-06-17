# Play Forever Engine

This repo separates **immutable truth** (the spine) from **mutable projection** (a playthrough markdown).

- Immutable: `spine/EVENT_SPINE.jsonl` (append-only)
- Mutable: `docs/PLAYTHROUGH_LATEST.md` (can be overwritten; cites `trace_id`s)

## Run one episode

```bash
python tools/evez.py play --seed 9 --steps 14 --out docs/PLAYTHROUGH_LATEST.md
```

## Watch the HUD (ARG tail)

```bash
python tools/evez.py arg-narrate --tail 25
```

## Loop mode (stop with Ctrl-C)

```bash
python tools/evez.py play --loop --steps 14 --out docs/PLAYTHROUGH_LATEST.md
```

Optionally cap loop iterations (useful for CI):

```bash
python tools/evez.py play --loop --steps 14 --max-episodes 3
```

## Loop mode fed by real disagreements

If you want "forever" to be driven by live contradictions (multi-vantage splits) instead of random motifs, enable `--auto-trigger`:

```bash
python tools/evez.py play --loop --steps 14 --auto-trigger --min-vantages 2
```

Mechanic:
- Each episode runs the disagreement detector (same logic as `trigger`).
- If there is an unconsumed `mission.disagreement`, the episode is grounded in it (Step 1 copies observations + prefilled Sigma_f/Omega).
- When a mission is consumed, a mission-specific projection is also written:
  `docs/PLAYTHROUGH_MISSION_<mission_trace_id>.md`

## Truth-plane rule

A `play.step` event is **pending** by default and must be promoted by evidence:
- provenance pointer (URL/file hash/trace id)
- falsifier (what breaks the claim)

Use `python tools/evez.py claim ...` to append audited claims, and `python tools/evez.py lint --fail` to enforce.
