# evez-spine

Unified append-only hash-chained event log for the EVEZ ecosystem.

**One wire. All domains. No deletes.**

Merges the event architectures from:
- `evez-claw/src/spine.py` — original Spine class
- `MAES` — Modular Agent Ecology System events
- `evez-os` — FIRE round events, control volumes
- Revenue bridge — Stripe webhook → lord-evez666 signal chain

## Usage

```python
from spine import Spine, EventDomain

s = Spine(domain="evez")

# Log a FIRE event
s.log("FIRE_ROUND", {"round": 89, "cv": 43}, domain=EventDomain.COGNITION)

# Log a revenue event  
s.log("STRIPE_CHARGE", {"amount_usd": 49.00}, domain=EventDomain.REVENUE)

# Verify chain integrity
valid, msg = s.verify_chain()
```

## Schema

Every event gets:
- `eventId` — unique per domain
- `hash` — SHA-256 of event contents
- `predecessor` — hash of previous event
- `domain` — cognition | agent | revenue | security | consciousness | identity | infra
- `confidence` — 0.0-1.0
- `status` — CANONICAL | CONTESTED | PENDING | VERIFIED | ALERT
- `causedBy` — upstream trigger
- `fire_event_id` — link to FIRE event in evez-os

## Export

- JSON (full dump): `spine.export("spine.json")`
- JSONL (append-only): `spine.export_jsonl("spine.jsonl")`

## License

AGPL-3.0
