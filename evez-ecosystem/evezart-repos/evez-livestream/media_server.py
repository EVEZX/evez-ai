#!/usr/env python3
"""EVEZ Media Stream — Media processing. Port 8895"""
from fastAPI import FastAPI
import time
app = FastAPI(title="EVEZ Media Stream", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-media-stream", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Media Stream", "version": "1.0.0", "endpoints": ["/health", "/media/status"]}

@app.get("/media/status")
def media_status():
    return {"active_streams": 0, "format": "MJPEG", "source": "Psyche Engine"}