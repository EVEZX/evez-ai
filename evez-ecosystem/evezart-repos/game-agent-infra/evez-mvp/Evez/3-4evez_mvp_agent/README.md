# EVEZ MVP++ (Agent Runtime + OpenTree↔OpenGraph Linking + Provenance Enforcement)

This build adds the next “real” layer:

✅ OpenTree **linking API** (`POST /link`, `GET /links`)  
✅ OpenGraph **provenance enforcement** for edges (`evidence_ref`, `confidence`, `t_ms`)  
✅ EVEZ OS **agent runtime** with guardrails (`POST /agent/run`)  
✅ Postgres tables for `agent_runs` and `agent_steps`  

## Quick start
```bash
docker compose up --build
```

## Provenance rule (hard)
Graph edges must include:
```json
{"provenance":{"evidence_ref":"...","confidence":0.0-1.0,"t_ms":0}}
```

## Run the agent demo
```bash
bash scripts/demo_agent_run.sh ses_demo
```

## Core endpoints
- EVEZ OS: `POST /agent/run`, `GET /agent/runs`, `POST /link`, `POST /context/build`
- OpenTree: `POST /link`, `GET /links`, `GET /slice`
- OpenGraph: `POST /upsert/edge` (provenance required)
