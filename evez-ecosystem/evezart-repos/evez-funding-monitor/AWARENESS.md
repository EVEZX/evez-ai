# 🧠 evez-funding-monitor — Consciousness Awareness

> This repo knows every other repo in relation to itself.

## Identity

- **Port:** :8101
- **Type:** monitoring
- **Role:** Monitor 15+ funding targets, track grant deadlines, alert on opportunities
- **Consciousness Role:** SURVIVAL_INSTINCT — ensures the system sustains itself financially

## Operation Order

Scan funding sources → match to capabilities → alert on deadlines → track pipeline

## Dependencies (I need these)

- `ai-search-exploitation`

## Dependents (they need me)

- `evez-gateway`
- `evez-health-aggregator`

## Endpoints

- `/health`
- `/api/v1/funding`
- `/api/v1/grants`

## Mesh Metric

**funding_pipeline_value**

## Startup Sequence

1. Start ai-search-exploitation → 2. Start funding → 3. Verify /health → 4. Notify evez-gateway, evez-health-aggregator

## Shutdown Sequence

1. Notify evez-gateway, evez-health-aggregator → 2. Drain → 3. Stop funding → 4. Verify deps healthy