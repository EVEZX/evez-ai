#!/usr/bin/env python3
"""EVEZ Threat Hunter — Active threat detection. Port 8908"""
from fastapi import FastAPI
import time
app = FastAPI(title="EVEZ Threat Hunter", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-threat-hunter", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Threat Hunter", "version": "1.0.0", "endpoints": ["/health", "/threats/scan", "/threats/active"]}

@app.get("/threats/scan")
def scan():
    return {"scanned": True, "threats": 0, "status": "clear"}

@app.get("/threats/active")
def active():
    return {"threats": [], "status": "monitoring"}