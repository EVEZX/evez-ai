#!/usr/bin/python3
"""EVEZ Observatory — Real-time system mapper. Port 8911"""
from fastapi import FastAPI
import time, json, urllib.request
from datetime import datetime
app = FastAPI(title="EVEZ Observatory", version="1.0.0")
SERVICES = {"gateway": 18789, "clawbreak": 8080, "cognition": 8081, "maes": 8082, "bridge": 8083, "plugins": 8876, "factory": 8891, "research": 8892, "mesh-brain": 8893, "mesh-broker": 8894, "psyche": 8896, "twin-rom": 8898, "omega": 8875, "searxng": 8888}
def _get(url, timeout=3):
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as r: return json.loads(r.read())
    except: return None
@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-observatory", "ts": int(time.time())}
@app.get("/")
def root(): return {"service": "EVEZ Observatory", "version": "1.0.0", "endpoints": ["/health", "/map"]}
@app.get("/map")
def map_services():
    results = {}
    for name, port in SERVICES.items():
        h = _get(f"http://127.0.0.1:{port}/health")
        results[name] = {"port": port, "status": "UP" if h else "DOWN", "details": h or {}}
    up = sum(1 for v in results.values() if v["status"] == "UP")
    return {"ecosystem": "OPERATIONAL" if up == len(SERVICES) else "DEGRADED", "services_up": f"{up}/{len(SERVICES)}", "services": results, "ts": datetime.now().isoformat()}
