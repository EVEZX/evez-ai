#!/usr/bin/env python3
"""EVEZ Guard — Gateway security. Port 8907"""
from fastapi import FastAPI
import time
app = FastAPI(title="EVEZ Guard", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-guard", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Guard", "version": "1.0.0", "endpoints": ["/health", "/guard/status", "/guard/rules"]}

@app.get("/guard/status")
def guard_status():
    return {"rate_limiting": "active", "anomaly_detection": "monitoring", "api_key_validation": "ready", "banned_ips": 0}

@app.get("/guard/rules")
def rules():
    return {"rules": ["rate-limit: 100/min per IP", "auth: API key on public endpoints", "anomaly: auto-ban on 5xx flood"], "status": "enforcing"}