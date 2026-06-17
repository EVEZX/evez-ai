# EVEZ-OS Topology Note

`evez-os` is the canonical **brand shell / public surface** for EVEZ.
It is the named product repo and the domain-facing surface attached to `evez.art`.

It is **not** the sole operator backend.
The live operator/API spine currently lives in a separate repo:

- Operator spine repo: `EvezArt/surething-offline`
- Logical role: `evez-operator-api`
- Live deployment name: `evez-operator`

## What belongs here

`evez-os` should own:
- public product identity
- visual cognition layer surfaces
- shell/dashboard experiences
- public-facing documentation for the EVEZ product surface
- embedded or proxied status views that consume operator truth

## What does not belong here

`evez-os` should not be treated as the sole system of record for:
- operator cycle control
- contradiction resolution state
- deploy status truth
- append-only operator ledger state
- API-level spine events used by the control plane

Those functions belong to the operator spine repo unless and until they are deliberately migrated.

## Relationship to the operator spine

The intended relationship is:

- `evez-os` = shell, brand, visual/public surface
- `surething-offline` = operator spine, API/control-plane surface
- `evez-sim` = simulation lane
- `agentvault` = registry / memory / audit layer

The immersive mobile operator console should target the operator spine for live status and event truth, then surface that state through the shell where appropriate.

## Practical rule

If a change is primarily about:
- public shell, product identity, visual cognition artifacts → `evez-os`
- operator truth, live API, contradictions, deploy status, event spine → operator spine (`surething-offline`)

Avoid collapsing those layers by naming instinct alone.
