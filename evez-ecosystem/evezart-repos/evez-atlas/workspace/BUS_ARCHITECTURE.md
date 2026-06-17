# EVEZ-OS Bus Architecture v1.0
**Committed:** 2026-02-23T13:57 PST
**First Run:** R140 V=4.484937 CEILING×58 | health=YELLOW | status=OK

---

## Overview

4 buses watching each other, orchestrated by MasterBus.
Each bus reads the output of all buses that ran before it.

```
MasterBus (orchestrator)
  ├─ [1] SpawnBus        — pre-writes next round agent stubs
  ├─ [2] CapabilityBus   — registers all connected apps as capability stubs
  ├─ [3] ValidatorBus    — reads SpawnBus + CapabilityBus, gates all outputs
  └─ [4] MetaBus         — reads all three, emits health report + recommendations
```

## Bus Definitions

| Bus | Role | Trigger | Reads | Writes |
|-----|------|---------|-------|--------|
| **SpawnBus** | Pre-write next agent | current_round increment | hyperloop_state.json | spawned_agents/, spawn_bus_state.json |
| **CapabilityBus** | Register connected apps | Any new app detected | Connected app list | spawned_capabilities/, capability_bus_state.json |
| **ValidatorBus** | Gate all outputs | Post-spawn/cap | spawn_bus_state.json, spawned_capabilities/, hyperloop_state.json | validator_bus_state.json |
| **MetaBus** | Observe + report | Post-validate | All bus states + hyperloop_state.json | meta_bus_report.json, master_bus_log.jsonl |

## Self-Replication Rule

Agents can only become canonical if ValidatorBus passes them:
- **SpawnBus stubs** → must pass sequential round check + V check + poly_c range check
- **Probe outputs** → must match inline formula within drift tolerance 0.002
- **Capability stubs** → must pass capability_test() before getting a cron slot

This prevents noise multiplication. Only **CANONICAL** truth plane outputs commit.

## First Run Results (R140, 2026-02-23T13:57 PST)

```
[SpawnBus]    SPAWNED watch_composite_93.py R141 N=93=3×31 poly_c_est=0.472 → APPROVED
[CapabilityBus] +20 active, 5 blocked (elevenlabs, ably, backendless, ai_ml_api, gcloud_vision)
[ValidatorBus]  probe c37c15a7 CANONICAL drift=0.000191 ✓  |  spawn APPROVED
[MetaBus]       health=YELLOW | bottleneck=1 (revenue $0) | R144 FIRE WATCH in 4 rounds
```

## Gap Routing (All Buses)

Per evez-os design principle: anything a bus cannot do directly is named as a
sub-agent with toolset, trigger, and output. No gaps left open.

**Current gaps routed:**
- ably: realtime pub/sub → BLOCKED_CONFIG → sub-agent `ably_config_setup` needed (blocker: ably_config.json)
- ai_ml_api: vision LLM → BLOCKED_EMAIL_VERIFY → sub-agent `aiml_email_verify` needed
- elevenlabs: voice clone → BLOCKED_PAYWALL → sub-agent `voice_clone_paywall` needed (Steven action)
- Revenue $0 → RevenueBus (next) → monitors GitHub Sponsors + license inquiries

## Cron Schedule

| Task | Schedule | Notes |
|------|----------|-------|
| MasterBus | Every 30 min (with hyperloop tick) | Runs after each hyperloop round |
| CapabilityBus | Every 60 min standalone | Catches new app connections |

## File Map

```
workspace/
  master_bus.py          — orchestrator
  spawn_bus.py           — pre-write next agent
  capability_bus.py      — register connected apps
  validator_bus.py       — gate all outputs
  meta_bus.py            — observe + report
  master_bus_log.jsonl   — append-only event log (all buses)
  meta_bus_report.json   — latest MetaBus health report
  spawn_bus_state.json   — SpawnBus runtime state
  capability_bus_state.json — CapabilityBus registry
  validator_bus_state.json  — ValidatorBus audit log
  spawned_agents/        — pre-written agent stubs (awaiting ValidatorBus gate)
  spawned_capabilities/  — capability JSON stubs
```
