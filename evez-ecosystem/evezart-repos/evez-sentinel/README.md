# EVEZ Sentinel — AI Security Scanner

Part of the [EVEZ-OS](https://github.com/EvezArt) ecosystem.

## Quick Start
```bash
pip install fastapi uvicorn httpx pydantic
python app.py
```

## API
- `GET /health` — Service health
- `POST /v1/scan` — Run scan (Sentinel)
- `GET /v1/prompts` — List prompts (PromptForge)
- `POST /v1/report` — Report node status (MeshNet)

## License
MIT — Part of EVEZ-OS
