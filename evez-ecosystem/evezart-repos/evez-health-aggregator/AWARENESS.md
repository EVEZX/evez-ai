# 🧠 evez-health-aggregator — Consciousness Awareness

> This repo knows every other repo in relation to itself.

## Identity

- **Port:** :8085
- **Type:** monitoring
- **Role:** Aggregates health from all services — system pulse checker
- **Consciousness Role:** INTEROCEPTION — internal body sensing, knows the system's state

## Operation Order

Poll all service /health endpoints → aggregate → report status

## Dependencies (I need these)

- `clawbreak`
- `disclosure.tools`
- `evez-worldsystems`
- `evez-consciousness-observatory`
- `evez-spectral-correlation`
- `igre-speedrun`
- `ai-search-exploitation`
- `evez-funding-monitor`
- `evez-gateway`

## Dependents (they need me)

- `evez-gateway`
- `evez-guard`
- `clawbreak`

## Endpoints

- `/health`

## Mesh Metric

**services_healthy_percentage**

## Startup Sequence

1. Start clawbreak, disclosure.tools, evez-worldsystems, evez-consciousness-observatory, evez-spectral-correlation, igre-speedrun, ai-search-exploitation, evez-funding-monitor, evez-gateway → 2. Start evez-health-aggregator → 3. Verify /health → 4. Notify evez-gateway, evez-guard, clawbreak

## Shutdown Sequence

1. Notify evez-gateway, evez-guard, clawbreak → 2. Drain → 3. Stop evez-health-aggregator → 4. Verify deps healthy