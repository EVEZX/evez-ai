# EVEZ Biosafety Control Plane

Defensive, consent-based bio-cyber control plane.

## Architecture

```
Phone + BAN + Network + RF
        ↓
  Atomic Witness Record (hash-chained)
        ↓
  Latent State Engine
        ↓
  Referee (cross-modal consistency)
        ↓
  Defensive Policy Engine
        ↓
  ALERT / LOG / RECOMMEND only
```

## Canonical Law

> Nothing becomes truth in the system until it has an event_id, provenance, and a valid chain hash.

## Files

- `guardian/policy/guardian_policy.yaml` — Machine-readable DEFENSIVE policy
- `schemas/care_spine_event.json` — JSON Schema for all Care Spine events
- `spine/genesis_root.json` — Root hash anchor

## Run

```bash
pip install fastapi uvicorn pyyaml pydantic
python guardian/main.py
```

## What This Is NOT

- Not a surveillance system
- Not a targeting system
- Not a medical diagnosis system
- Not autonomous — human confirmation required for all disruptive actions
