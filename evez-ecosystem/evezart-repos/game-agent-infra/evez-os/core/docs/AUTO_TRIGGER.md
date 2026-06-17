# Auto-trigger missions from disagreements

The point of **trigger** is to turn *disagreement* into *work*.

When the same target is probed from multiple **vantages** (networks / resolvers / locations) and the
results conflict, the system appends a **mission** to the immutable spine instead of letting you
"win" by narrating.

## Quick start

1) Run the same probe from two vantages (tag them):

```bash
python tools/evez.py probe dns --name example.com --rrtype A --append-spine --vantage home_wifi
python tools/evez.py probe dns --name example.com --rrtype A --append-spine --vantage phone_lte
```

2) Generate missions:

```bash
python tools/evez.py trigger
```

3) Inspect what got appended:

```bash
grep '"kind":"mission.disagreement"' spine/EVENT_SPINE.jsonl | tail -n 5
```

## What gets emitted

Missions are appended as JSON objects:

* `kind = mission.disagreement`
* `trace_id = M...` (content-hash of the disagreement payload)
* `observations = [{vantage_id, ts, value}, ...]`
* `Sigma_f` + `Omega` suggestions
* `recommended_probe` next step

## Auto-spawn play episodes from new missions (last-level wiring)

If you want disagreement to *immediately* become a playable episode (projection) that stays tethered to the witness (spine), run:

```bash
python tools/evez.py trigger --spawn-play --steps 14
```

Outputs:

- Per-mission projection files: `docs/PLAYTHROUGH_MISSION_<mission_trace_id>.md`
- Updated pointer: `docs/PLAYTHROUGH_LATEST.md`

The first step of each spawned episode is grounded in the disagreement payload:

- lobby inferred from probe kind (DNS/TLS/CDN/BGP)
- `Sigma_f` and `Omega` pre-filled from the mission
- `evidence.observations` copied in so the step is falsifiable

## Sentinel mode (continuous)

To keep scanning and reacting (useful for long-running probes / watch loops):

```bash
python tools/evez.py sentinel --interval 15 --spawn-play --steps 14
```

Optional cap (so you don't run forever in CI):

```bash
python tools/evez.py sentinel --interval 15 --spawn-play --steps 14 --max-loops 10
```

## Why this matters

It enforces the rule:

> **Confidence without multi-vantage receipts is a failure surface (Σf), not a win.**
## Using auto-trigger inside play --loop

If you want the "play forever" loop to call the disagreement trigger each episode and consume missions automatically:

```bash
python tools/evez.py play --loop --steps 14 --auto-trigger --min-vantages 2
```

This is equivalent to running `trigger` repeatedly and then spawning episodes from the next unconsumed `mission.disagreement`.
