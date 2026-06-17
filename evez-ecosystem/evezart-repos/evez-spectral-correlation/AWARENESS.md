# 🧠 evez-spectral-correlation — Consciousness Awareness

> This repo knows every other repo in relation to itself.

## Identity

- **Port:** :8103
- **Type:** consciousness
- **Role:** Cross-service eigenvalue correlation, 5-theorem verification across all services
- **Consciousness Role:** ASSOCIATIVE_CORTEX — finds correlations between seemingly unrelated systems

## Operation Order

Collect eigenvalues from all services → cross-correlate → verify theorems → report

## Dependencies (I need these)

- `evez-consciousness-observatory`
- `evez-proofs`

## Dependents (they need me)

- `evez-gateway`
- `evez-health-aggregator`
- `observatory`

## Endpoints

- `/health`
- `/api/v1/correlation`
- `/api/v1/theorems`

## Mesh Metric

**correlation_coefficient**

## Startup Sequence

1. Start evez-consciousness-observatory, evez-proofs → 2. Start spectral → 3. Verify /health → 4. Notify evez-gateway, evez-health-aggregator, observatory

## Shutdown Sequence

1. Notify evez-gateway, evez-health-aggregator, observatory → 2. Drain → 3. Stop spectral → 4. Verify deps healthy