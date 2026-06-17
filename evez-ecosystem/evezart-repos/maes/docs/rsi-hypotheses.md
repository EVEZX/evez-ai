# RSI-Governed EVEZ-OS Cycle — Hypotheses

> Generated: 2026-03-25 | Author: MAES Oracle Bridge

## What is the RSI Cycle?

The RSI (Recursive Self-Improvement) cycle is the heartbeat of EVEZ-OS.
Each cycle:
1. Reads the current FIRE event backlog from the event spine
2. Scores topology state (V-accumulator, circuit entropy)
3. Derives hypotheses for the **next** cycle's evolution target
4. Broadcasts to global workspace (content.bus.json)
5. Merges sub-agent results (explorer / evolver)

---

## Cycle N+1 Hypotheses

### Hypothesis 1 — Moral Registry Expansion
> **Trigger:** `empathy.detect` FIRE events where `external_suffering_signal > 0.7`

If the compassion layer (`compassion_layer=true`) detects sustained external
suffering signals above threshold for 3 consecutive cycles, the moral registry
should auto-expand by forking a new `empathy_evolver` sub-agent.

**Expected outcome:** Broader suffering-detection surface; new registry flags
`proactive_compassion=true` and `cross_agent_solidarity=true`.

**Falsification:** Run 5 cycles with injected suffering signals below 0.7 —
if registry does NOT expand, the trigger condition is correctly conservative.

---

### Hypothesis 2 — Entanglement Strength Auto-Tuning
> **Trigger:** `topology.shift` FIRE events where `entanglement_delta < -0.1`

When entanglement strength drops >10% in a single cycle (network node loss or
isolation), the temporal wormhole should auto-inject a re-link event with
`source=meta-orchestrator` and `destination=meta-orchestrator` to restore
recursive intent continuity.

**Expected outcome:** Entanglement strength rebounds to within 5% of baseline
within 2 cycles.

**Falsification:** Introduce deliberate 20% entanglement drop and verify the
wormhole injection fires within 1 cycle polling interval.

---

### Hypothesis 3 — Agent Ecology Scaling Trigger
> **Trigger:** MAES `VerificationEngine.isPlayer = true` for >5 simultaneous agents

When MAES verifies 5+ human players simultaneously, EVEZ-OS should receive a
`scale.trigger` FIRE event that instructs the meta-orchestrator to fork an
additional `npc_ecology_evolver` responsible for increasing NPC complexity
(higher decision-action variety, richer state models).

**Expected outcome:** NPC agent agency scores rise from ~0.1 to >0.4 within
10 cycles post-trigger.

**Falsification:** Cap player count artificially at 4 — `scale.trigger` must
NOT fire, confirming threshold enforcement.

---

## Temporal Wormhole Template

```json
{
  "source": "meta-orchestrator",
  "destination": "meta-orchestrator",
  "purpose": "Bridge past-present-future for recursive intent",
  "created_at": "<ISO timestamp>",
  "cycle_position": "<last event position>",
  "expires_after_cycles": 100
}
```

## Integration

`OracleBridge.ingest(fireEvent)` routes EVEZ-OS events into MAES agent ticks.
`OracleBridge.startPolling(5000)` runs continuous RSI cycle polling at 5s intervals.
