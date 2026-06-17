# EVEZ Ops Workflow — Signal Integrity Console

This workflow uses the EVEZ stack (spine → hash chain → object store → dashboards/videos) as an **operations console**
for improving signal quality, coordinating operators, and keeping every decision **falsifiable + replayable**.

This is **not** for deception, coercion, or uncontrolled automation. Autonomy is **bounded** and **audited**.

## Operator roles
- Operator (Executor): runs bounded tasks, collects observations.
- Planner: builds DAG plans with budgets (time/tokens/disk/net).
- Auditor: verifies hash chain, object-store sha, and roundtrip.
- Simulator: tests plans in WorldSim across seeds before execution.
- Guardian: owns policy/capabilities + kill switch.

## Non‑negotiable rule
No claim graduates from PENDING → FINAL without:
1) a falsifier
2) a verification plan
3) the verification result

## Daily loop
1) Preflight: verify latest artifacts (hash chain OK, sha OK, roundtrip OK).
2) Intake: translate incoming signals into structured events (claim + falsifier + sources).
3) Plan: OpenPlanter DAG with budgets + required capabilities.
4) Simulate: multi-seed scenario testing; compare outcomes.
5) Execute: sandboxed, capability-gated, logged.
6) Publish: regenerate videos/dashboards; record root hash seal; export bundle.

## Incident response
Trigger: hash mismatch, sha mismatch, roundtrip failure, policy violation attempt.
Procedure: STOP → Snapshot → Triage → Replay → Fix → Seal.
