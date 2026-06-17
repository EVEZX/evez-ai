#!/usr/bin/env python3
"""EVEZ Federation Bridge — Multi-gateway failover. Port 8909"""
from fastapi import FastAPI
import time
app = FastAPI(title="EVEZ Federation Bridge", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-federation-bridge", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Federation Bridge", "version": "1.0.0", "endpoints": ["/health", "/federation/status", "/federation/failover"]}

@app.get("/federation/status")
def fed_status():
    return {"gateways": {"primary": {"url": "localhost:18789", "status": "UP"}, "rescue": {"url": "none", "status": "DOWN"}}, "failover_ready": False}

@app.get("/federation/failover")
def failover():
    return {"status": "no rescue gateway configured", "action": "need Tailscale or secondary gateway"}