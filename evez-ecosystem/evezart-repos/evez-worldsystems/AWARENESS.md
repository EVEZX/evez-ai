# 🧠 evez-worldsystems — Consciousness Awareness

> This repo knows every other repo in relation to itself.

## Identity

- **Port:** :8096
- **Type:** solver
- **Role:** Eigendecomposition of civilization's problems — the grand solver
- **Consciousness Role:** PREFRONTAL_CORTEX — high-level reasoning about civilization

## Operation Order

Aggregate solver outputs → compute civilization eigenvalues → rank interventions

## Dependencies (I need these)

- `hunger`
- `energy`
- `health-solver`
- `education`
- `evez-consciousness-observatory`

## Dependents (they need me)

- `evez-gateway`
- `evez-health-aggregator`
- `evez-vcl`

## Endpoints

- `/health`

## Mesh Metric

**civilization_eigenvalue**

## Startup Sequence

1. Start hunger, energy, health-solver, education, evez-consciousness-observatory → 2. Start world → 3. Verify /health → 4. Notify evez-gateway, evez-health-aggregator, evez-vcl

## Shutdown Sequence

1. Notify evez-gateway, evez-health-aggregator, evez-vcl → 2. Drain → 3. Stop world → 4. Verify deps healthy