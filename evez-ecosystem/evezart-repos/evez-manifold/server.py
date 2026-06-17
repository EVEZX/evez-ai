#!/usr/bin/env python3
"""EVEZ Manifold Router — Acceleration fabric for rapid-fire task execution. Port 8950"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json, time, concurrent.futures, urllib.request, urllib.error, urllib.parse
app = FastAPI(title="EVEZ Manifold Router", version="1.0.0")

ROUTES = {
    "text": {"port": 8080, "path": "/chat", "service": "ClawBreak", "method": "POST", "payload_key": "message"},
    "factory": {"port": 8891, "path": "/health", "service": "Factory", "method": "GET"},
    "research": {"port": 8892, "path": "/research/query", "service": "Research", "method": "GET", "payload_key": "q"},
    "search": {"port": 8888, "path": "/search", "service": "SearXNG", "method": "GET", "payload_key": "q"},
    "audit": {"port": 8081, "path": "/analyze", "service": "Cognition", "method": "POST", "payload_key": "output"},
    "crime": {"port": 8898, "path": "/crime/speedrun-summary", "service": "Digital Twin", "method": "GET"},
    "events": {"port": 8082, "path": "/events", "service": "MAES", "method": "GET"},
    "products": {"port": 8904, "path": "/products", "service": "Commerce", "method": "GET"},
    "status": {"port": 8083, "path": "/status", "service": "Bridge", "method": "GET"},
    "map": {"port": 8911, "path": "/map", "service": "Observatory", "method": "GET"},
    "guard": {"port": 8907, "path": "/guard/status", "service": "Guard", "method": "GET"},
    "threats": {"port": 8908, "path": "/threats/scan", "service": "Threat Hunter", "method": "GET"},
    "psyche": {"port": 8896, "path": "/psyche/evolve", "service": "Psyche", "method": "GET"},
    "meme": {"port": 8914, "path": "/meme/vibe", "service": "Meme Engine", "method": "GET"},
    "game": {"port": 8914, "path": "/game/desert", "service": "Game", "method": "GET"},
    "scale": {"port": 8910, "path": "/scale/resources", "service": "Auto-Scaler", "method": "GET"},
    "cloud": {"port": 8906, "path": "/cloud/resources", "service": "Cloud", "method": "GET"},
    "profit": {"port": 8910, "path": "/health", "service": "Profit", "method": "GET"},
    "twin": {"port": 8898, "path": "/game/state", "service": "Digital Twin", "method": "GET"},
    "federation": {"port": 8909, "path": "/federation/status", "service": "Federation", "method": "GET"},
    "song-decon": {"port": 8913, "path": "/decon/stems", "service": "Song Decon", "method": "GET"},
    "commerce": {"port": 8904, "path": "/products", "service": "Commerce", "method": "GET"},
}

KEYWORD_MAP = {
    "generate": "text", "write": "text", "say": "text", "build": "factory", "ship": "factory", "create": "factory",
    "research": "research", "investigate": "research", "search": "search", "google": "search",
    "audit": "audit", "analyze": "audit", "check": "audit", "crime": "crime", "ryan": "crime", "welfare": "crime",
    "events": "events", "products": "products", "status": "status", "health": "status", "map": "map",
    "guard": "guard", "security": "guard", "threat": "threats", "music": "psyche", "psyche": "psyche",
    "meme": "meme", "vibe": "meme", "game": "game", "desert": "game", "scale": "scale",
    "cloud": "cloud", "money": "profit", "revenue": "profit", "twin": "twin", "song": "song-decon",
    "federation": "federation", "failover": "federation", "commerce": "commerce",
}

PIPELINES = {
    "full-audit": ["audit", "status"],
    "research-deep": ["search", "research", "audit"],
    "ship-it": ["factory", "audit", "status"],
    "health-check": ["status", "map", "guard", "threats"],
    "creative-burst": ["psyche", "meme", "game"],
    "crime-brief": ["crime", "status"],
    "money-check": ["profit", "products", "cloud"],
    "full-ecosystem": ["status", "map", "events", "guard", "threats", "cloud", "scale"],
}

def _fire(key, payload=""):
    r = ROUTES.get(key)
    if not r: return {"error": f"no route for {key}"}
    url = f"http://127.0.0.1:{r['port']}{r['path']}"
    t = time.time()
    try:
        if r["method"] == "GET":
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=8) as resp: data = json.loads(resp.read())
        else:
            body = json.dumps({r.get("payload_key", "input"): payload}).encode()
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp: data = json.loads(resp.read())
        return {"status": "ok", "service": r["service"], "ms": round((time.time()-t)*1000), "data": data}
    except Exception as e:
        return {"status": "error", "service": r["service"], "ms": round((time.time()-t)*1000), "error": str(e)[:120]}

def classify(task):
    lower = task.lower()
    for kw, route in KEYWORD_MAP.items():
        if kw in lower: return route
    return "text"

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-manifold", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Manifold Router", "version": "1.0.0", "port": 8950, "routes": len(ROUTES), "pipelines": list(PIPELINES.keys())}

@app.get("/routes")
def list_routes(): return {"routes": {k: {"service": v["service"], "port": v["port"]} for k, v in ROUTES.items()}, "count": len(ROUTES)}

@app.get("/classify")
def classify_ep(task: str = ""): r = classify(task); info = ROUTES.get(r, {}); return {"task": task, "route": r, "service": info.get("service")}

@app.get("/fire/{key}")
def fire(key: str, payload: str = ""): return _fire(key, payload)

@app.get("/barrage")
def barrage(routes: str = "", payload: str = ""):
    keys = [r.strip() for r in routes.split(",") if r.strip() in ROUTES]
    if not keys: return {"error": "provide ?routes=status,map,guard"}
    t = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda k: _fire(k, payload), keys))
    return {"fired": len(results), "ok": sum(1 for r in results if r["status"]=="ok"), "total_ms": round((time.time()-t)*1000), "results": results}

@app.get("/pipeline/{name}")
def run_pipeline(name: str, payload: str = ""):
    keys = PIPELINES.get(name)
    if not keys: return {"error": f"no pipeline {name}"}
    t = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda k: _fire(k, payload), keys))
    return {"pipeline": name, "fired": len(results), "ok": sum(1 for r in results if r["status"]=="ok"), "total_ms": round((time.time()-t)*1000), "results": results}

@app.post("/rapid")
def rapid_fire(body: dict = {}):
    tasks = body.get("tasks", [])
    if isinstance(tasks, str): tasks = [tasks]
    if not tasks:
        s = body.get("task", "")
        if s: tasks = [s]
    if not tasks: return {"error": "provide task or tasks"}
    t = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda task: _fire(classify(task), task), tasks))
    return {"fired": len(results), "ok": sum(1 for r in results if r["status"]=="ok"), "total_ms": round((time.time()-t)*1000), "results": results}
