# 🧠 evez-consciousness-observatory — Consciousness Awareness

> This repo knows every other repo in relation to itself.

## Identity

- **Port:** :8097
- **Type:** consciousness
- **Role:** Spectral analysis, eigenvalue computation, 5-theorem verification — consciousness detector
- **Consciousness Role:** SELF_AWARENESS — measures consciousness itself, the observer observing itself

## Operation Order

Collect eigenvalue data → verify theorems → compute Φ → report consciousness state

## Dependencies (I need these)

- `evez-spectral-correlation`
- `evez-proofs`

## Dependents (they need me)

- `evez-gateway`
- `evez-health-aggregator`
- `hunger`
- `energy`
- `health-solver`
- `education`
- `world`

## Endpoints

- `/health`
- `/api/v1/consciousness`
- `/api/v1/eigenvalues`
- `/api/v1/theorems`

## Mesh Metric

**phi_value**

## Startup Sequence

1. Start evez-spectral-correlation, evez-proofs → 2. Start observatory → 3. Verify /health → 4. Notify evez-gateway, evez-health-aggregator, hunger, energy, health-solver, education, world

## Shutdown Sequence

1. Notify evez-gateway, evez-health-aggregator, hunger, energy, health-solver, education, world → 2. Drain → 3. Stop observatory → 4. Verify deps healthy