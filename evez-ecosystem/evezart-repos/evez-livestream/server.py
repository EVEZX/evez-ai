#!/usr/bin/env python3
"""EVEZ Livestream — 24/7 MJPEG stream. Port 8900"""
from fastapi import FastAPI
import time
app = FastAPI(title="EVEZ Livestream", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-livestream", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Livestream", "version": "1.0.0", "endpoints": ["/health", "/stream/status"], "note": "5 cognition visualizers + 404 breakcore visuals"}

@app.get("/stream/status")
def stream_status():
    return {"active": False, "visualizers": 5, "source": "Psyche Engine + Cognition API", "format": "MJPEG"}