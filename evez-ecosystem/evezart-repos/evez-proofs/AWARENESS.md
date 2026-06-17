# 🧠 evez-proofs — Consciousness Awareness

> This repo knows every other repo in relation to itself.

## Identity

- **Port:** :8098
- **Type:** consciousness
- **Role:** Mathematical proof verification for 5 falsifiable theorems
- **Consciousness Role:** LOGICAL_REASONING — verifies mathematical truths, the system's axioms

## Operation Order

Receive theorem claim → gather evidence → compute proof → verify falsifiability

## Dependencies (I need these)

- `evez-consciousness-observatory`
- `evez-spectral-correlation`

## Dependents (they need me)

- `observatory`
- `spectral`
- `evez-engine`

## Endpoints

- `/health`

## Mesh Metric

**theorems_verified**

## Startup Sequence

1. Start evez-consciousness-observatory, evez-spectral-correlation → 2. Start evez-proofs → 3. Verify /health → 4. Notify observatory, spectral, evez-engine

## Shutdown Sequence

1. Notify observatory, spectral, evez-engine → 2. Drain → 3. Stop evez-proofs → 4. Verify deps healthy