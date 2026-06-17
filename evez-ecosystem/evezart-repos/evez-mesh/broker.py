#!/usr/bin/env python3
"""EVEZ Mesh Broker — Message broker. Port 8894"""
from fastapi import FastAPI
import time
app = FastAPI(title="EVEZ Mesh Broker", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-mesh-broker", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Mesh Broker", "version": "1.0.0", "endpoints": ["/health", "/broker/status", "/broker/pub", "/broker/sub"]}

@app.get("/broker/status")
def broker_status():
    return {"queue_depth": 0, "subscribers": 0, "uptime_s": int(time.time()), "backend": "in-memory"}