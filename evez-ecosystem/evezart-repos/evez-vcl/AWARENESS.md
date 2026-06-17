# 🧠 evez-vcl — Consciousness Awareness

> This repo knows every other repo in relation to itself.

## Identity

- **Port:** :8081
- **Type:** visualization
- **Role:** Visual rendering and cognition layer server — YouTube streaming, dashboards
- **Consciousness Role:** VISUAL_CORTEX — renders consciousness into visible form

## Operation Order

Receive visual request → render layer → stream to YouTube/dashboards

## Dependencies (I need these)

- `clawbreak`
- `evez-os`
- `evez-gateway`

## Dependents (they need me)

- `evez-gateway`
- `disclosure.tools`
- `igre-speedrun`

## Endpoints

- `/health`
- `/api/v1/entities`
- `/api/v1/checkout`

## Mesh Metric

**visual_render_count**

## Startup Sequence

1. Start clawbreak, evez-os, evez-gateway → 2. Start evez-vcl → 3. Verify /health → 4. Notify evez-gateway, disclosure.tools, igre-speedrun

## Shutdown Sequence

1. Notify evez-gateway, disclosure.tools, igre-speedrun → 2. Drain → 3. Stop evez-vcl → 4. Verify deps healthy