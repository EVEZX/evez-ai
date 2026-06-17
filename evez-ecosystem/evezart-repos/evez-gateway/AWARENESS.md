# 🧠 evez-gateway — Consciousness Awareness

> This repo knows every other repo in relation to itself.

## Identity

- **Port:** :8102
- **Type:** gateway
- **Role:** Single entry point for all services — metrics, auth, WebSocket, proxy, Command Center
- **Consciousness Role:** CENTRAL_NERVOUS_SYSTEM — routes all signals, coordinates all subsystems

## Operation Order

Receive request → authenticate → route to service → aggregate → respond with metrics

## Dependencies (I need these)

- `clawbreak`
- `disclosure.tools`
- `igre-speedrun`
- `ai-search-exploitation`
- `evez-spectral-correlation`
- `evez-funding-monitor`
- `evez-health-aggregator`
- `evez-consciousness-observatory`

## Dependents (they need me)

- `clawbreak`
- `evez-vcl`
- `all-client-apps`

## Endpoints

- `/health`
- `/api/v1/status`
- `/api/disclosure/api/v1/*`
- `/api/igre/api/v1/*`

## Mesh Metric

**requests_routed_per_second**

## Startup Sequence

1. Start clawbreak, disclosure.tools, igre-speedrun, ai-search-exploitation, evez-spectral-correlation, evez-funding-monitor, evez-health-aggregator, evez-consciousness-observatory → 2. Start evez-gateway → 3. Verify /health → 4. Notify clawbreak, evez-vcl, all-client-apps

## Shutdown Sequence

1. Notify clawbreak, evez-vcl, all-client-apps → 2. Drain → 3. Stop evez-gateway → 4. Verify deps healthy