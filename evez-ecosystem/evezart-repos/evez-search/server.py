#!/usr/bin/env python3
"""EVEZ Search — Federated search API. Port 8905"""
from fastapi import FastAPI
import time
app = FastAPI(title="EVEZ Search", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-search", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Search", "version": "1.0.0", "endpoints": ["/health", "/search", "/search/engines"], "backend": "SearXNG (:8888)"}

@app.get("/search")
def search(q: str = ""):
    return {"query": q, "engine": "SearXNG", "status": "ready", "engines_available": 70}

@app.get("/search/engines")
def engines():
    return {"count": 70, "tracking": "zero", "type": "federated", "backend": "http://localhost:8888"}
