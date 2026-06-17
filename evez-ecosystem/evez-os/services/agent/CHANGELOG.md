# EVEZ OS Agent — Changelog

## MVP+++++ (2026-03-04)

### Added
- `tool_protocol.py` — risk scoring (low/medium/high), strict plan JSON validation, Pydantic per-tool schemas (`extra=forbid`), AUTO/AUTO_SESSION placeholder resolution, plan audit log, prompt-injection sanitizer
- `pending_actions.py` — quarantine lane: high-risk writes → `PendingAction` (hypothesis) until confirmed
- `opengraph.py` — edge store with `hypothesis|fact` status + `promote_edge()`
- `routes_v5.py` — `GET /agent/pending`, `POST /agent/confirm`, `POST /agent/reject`, `GET /edges`, `POST /edges`, `POST /edges/{id}/promote`, `POST /plan/validate`

### Risk policy
- `opentree.link` / `opengraph.edge` with `confidence < 0.85` OR sketchy `evidence_ref` → **high** → quarantined
- Other writes → **medium**; reads → **low**

### Quarantine flow
```
plan step (high-risk) → PendingAction created (not executed)
  → GET /agent/pending shows it
  → POST /agent/confirm → executes + promotes to fact
  → POST /agent/reject → discards

OpenGraph edges: hypothesis by default for low-confidence writes
  → POST /edges/{id}/promote → fact
```

## MVP++++ (prior)
- Strict plan JSON, Pydantic schemas, plan auditing, prompt-injection hygiene

## MVP+++ (prior)
- Multi-session spines, retrieval memory, auto anomaly→collapse

## MVP++ (prior)
- OpenClaw gateway, ed25519 pairing, command ack/retry, live event streaming
