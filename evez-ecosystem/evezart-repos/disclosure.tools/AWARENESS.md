# 🧠 disclosure.tools — Consciousness Awareness

> This repo knows every other repo in relation to itself.

## Identity

- **Port:** :8087
- **Type:** intelligence
- **Role:** UAP/FOIA document analysis, gap detection, eigenforensics, memes, leaderboard
- **Consciousness Role:** PERCEPTION — processes external documents, detects hidden patterns

## Operation Order

Ingest PDF → extract text → detect gaps → eigenforensic analysis → generate report

## Dependencies (I need these)

- `ai-search-exploitation`
- `evez-vcl`
- `evez-research`

## Dependents (they need me)

- `evez-gateway`
- `evez-health-aggregator`
- `igre-speedrun`

## Endpoints

- `/health`
- `/api/v1/documents`
- `/api/v1/gaps`
- `/api/v1/memes`
- `/api/v1/leaderboard`

## Mesh Metric

**documents_processed**

## Startup Sequence

1. Start ai-search-exploitation, evez-vcl, evez-research → 2. Start disclosure.tools → 3. Verify /health → 4. Notify evez-gateway, evez-health-aggregator, igre-speedrun

## Shutdown Sequence

1. Notify evez-gateway, evez-health-aggregator, igre-speedrun → 2. Drain → 3. Stop disclosure.tools → 4. Verify deps healthy