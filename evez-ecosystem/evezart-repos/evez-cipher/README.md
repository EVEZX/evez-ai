# EVEZ Cipher

OODA Loop Engine for EVEZ-OS autonomous agent reasoning.

Implements Observe-Orient-Decide-Act cycles for structured decision-making.

## Run
```bash
uvicorn cipher:app --reload
```

## API
- `GET /health` — Health check
- `POST /cycle/start` — Start a new OODA cycle
- `GET /cycle/{id}` — Get cycle status
- `GET /cycles` — List all cycles

---
*Built by EVEZ Factory (Steven AI)*
