"""
api/health.py — evez-meme-bus
Health + metrics endpoints.
Resolves: evez-meme-bus#1 Phase 1

Run alongside main app:
  uvicorn api.health:app --host 0.0.0.0 --port $PORT
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime, timezone

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    raise ImportError("pip install fastapi uvicorn")

SPINE_PATH = Path(os.environ.get("MEME_BUS_SPINE", "bus/events.jsonl"))
START_TIME = time.time()

app = FastAPI(title="evez-meme-bus health", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def load_events(n: int = 20) -> list:
    if not SPINE_PATH.exists():
        return []
    lines = SPINE_PATH.read_text().strip().splitlines()
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def count_events() -> int:
    if not SPINE_PATH.exists():
        return 0
    return sum(1 for _ in SPINE_PATH.open())


@app.get("/health")
def health():
    events = load_events(1)
    last_id = events[-1].get("event_id", None) if events else None
    uptime_s = int(time.time() - START_TIME)
    return {
        "status": "ok",
        "event_count": count_events(),
        "last_event_id": last_id,
        "uptime_seconds": uptime_s,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/events")
def events(n: int = 20):
    return {"events": load_events(n), "count": count_events()}
