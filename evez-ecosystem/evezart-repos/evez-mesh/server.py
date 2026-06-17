#!/usr/bin/env python3
"""EVEZ Mesh — Distributed mesh network. Port 8893"""
from fastapi import FastAPI
import time
app = FastAPI(title="EVEZ Mesh", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-mesh", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Mesh", "version": "1.0.0", "endpoints": ["/health", "/mesh/topology", "/mesh/peers"]}

@app.get("/mesh/topology")
def topology():
    return {"nodes": 1, "edges": 0, "topology": "star", "coordinator": "localhost:8893"}

@app.get("/mesh/peers")
def peers():
    return {"peers": [{"id": "self", "url": "localhost:8893", "status": "UP"}], "total": 1}