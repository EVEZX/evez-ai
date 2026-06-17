# Retrocausal-Safe Patterns for Game Agent Infra

You cannot send information to the past, but you *can* make later facts rewrite earlier **views**.

## Max-RI loop for multiplayer
Client prediction -> Server authoritative -> Rollback & re-sim

Key rule: **pending vs final** is explicit, and all rewrites carry provenance.

See: `docs/ASCII_MEGA_MAP.txt` and `docs/chart_object.json`.
