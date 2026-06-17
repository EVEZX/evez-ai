from fastapi import FastAPI
from .telemetry import router as telemetry_router

app = FastAPI(title="EVEZ-OS", version="0.1.0")

app.include_router(telemetry_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "EVEZ-OS"}
