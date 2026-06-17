#!/usr/bin/env python3
"""EVEZ Device Portal — Single entry point for Steven's A16
All ecosystem access paths, live monitoring, node pairing. Port 8964"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json, time, urllib.request

app = FastAPI(title="EVEZ Device Portal", version="1.0.0")
HOST = "845b0d79-fb7b-4e96-87ae-73537a81fa75.vultropenclaw.com"
BASE = f"https://{HOST}"

def fetch(path, port=None):
    try:
        url = f"http://localhost:{port}{path}" if port else f"{BASE}{path}"
        req = urllib.request.Request(url, headers={"User-Agent": "evez-portal"})
        with urllib.request.urlopen(req, timeout=3) as r: return json.loads(r.read())
    except: return None

SERVICES = [
    ("ClawBreak AI", "/clawbreak/", 8080, "🤖"), ("Cognition API", "/cognition/", 8081, "🧠"),
    ("MAES Events", "/dashboard/", 8082, "📡"), ("Bridge", "/bridge/", 8083, "🌉"),
    ("Factory", "/factory/", 8891, "🏭"), ("Digital Twin 3D", "/twin3d/", 8899, "🗺️"),
    ("Terrain Engine", "/terrain/", 8897, "⛰️"), ("Neurologic Monitor", "/neuro/", 8963, "🧬"),
    ("Code Review", "/api/codereview/", 8960, "👀"), ("Sentiment API", "/api/sentiment/", 8961, "😊"),
    ("API Gateway", "/api/keys/", 8962, "🔑"), ("SearXNG", "/search/", 8888, "🔍"),
    ("Code-Server", "/code/", 6969, "💻"), ("Manifold Router", "/manifold/", 8950, "🔀"),
    ("Health Agg", "/health-agg/", 8951, "❤️"), ("Twin ROM", "/twin-rom/", 8958, "💾"),
]

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-device-portal", "ts": int(time.time())}

@app.get("/status")
def status():
    results = []
    for name, path, port, icon in SERVICES:
        d = fetch("/health", port)
        results.append({"name": name, "path": f"{BASE}{path}", "port": port, "icon": icon, "healthy": d is not None})
    up = sum(1 for r in results if r["healthy"])
    return {"total": len(results), "up": up, "services": results}

@app.get("/", response_class=HTMLResponse)
def portal(): return HTMLResponse("Portal HTML served from evez-device-portal on port 8964")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8964)
