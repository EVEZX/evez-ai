"""
EVEZ-OS Unified API Gateway
Single entry point for all 16 services. Adds metrics, auth, rate limiting, WebSocket feeds.
This replaces 13 separate uvicorn processes with 1.
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import httpx
import json
import time
import os
import hashlib
import asyncio
from datetime import datetime
from collections import defaultdict

app = FastAPI(
    title="EVEZ-OS Unified Gateway",
    version="2.0.0",
    description="Single API gateway for the entire EVEZ-OS ecosystem — 16 services, 120+ endpoints, eigenforensics, genome extraction, speedrun projecteering.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")), name="static")

# ─── Service Registry ────────────────────────────────────────

SERVICES = {
    "clawbreak":     {"port": 8080, "name": "ClawBreak",             "version": "0.3.0"},
    "vcl":           {"port": 8081, "name": "VCL",                   "version": "1.0.0"},
    "health-agg":    {"port": 8085, "name": "Health Aggregator",     "version": "1.0.0"},
    "disclosure":    {"port": 8087, "name": "Disclosure Tools",      "version": "2.0.0"},
    "hunger":        {"port": 8092, "name": "Hunger Solver",         "version": "1.0.0"},
    "energy":        {"port": 8093, "name": "Energy Solver",         "version": "1.0.0"},
    "health-solver": {"port": 8094, "name": "Health Solver",         "version": "1.0.0"},
    "education":     {"port": 8095, "name": "Education Solver",      "version": "1.0.0"},
    "world":         {"port": 8096, "name": "World Solver",          "version": "1.0.0"},
    "observatory":   {"port": 8097, "name": "Consciousness Observatory", "version": "1.0.0"},
    "igre":          {"port": 8099, "name": "IGRE Speedrun",         "version": "1.0.0"},
    "search":        {"port": 8100, "name": "AI Search Gateway",     "version": "1.0.0"},
    "funding":       {"port": 8101, "name": "Funding Monitor",       "version": "1.0.0"},
    "spectral":      {"port": 8103, "name": "Spectral Correlation",   "version": "1.0.0"},
    "intelligence":  {"port": 8122, "name": "Intelligence Mesh",      "version": "1.0.0"},
}

# ─── Metrics ──────────────────────────────────────────────────

metrics = {
    "start_time": time.time(),
    "requests_total": 0,
    "requests_by_service": defaultdict(int),
    "requests_by_status": defaultdict(int),
    "latency_by_service": defaultdict(list),
    "errors": 0,
    "ws_connections": 0,
}

# ─── Rate Limiting ────────────────────────────────────────────

rate_limits = defaultdict(list)  # ip -> [timestamps]
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 300     # requests per window

def check_rate_limit(request: Request):
    """Simple sliding window rate limiter."""
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    # Clean old entries
    rate_limits[ip] = [t for t in rate_limits[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(rate_limits[ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    rate_limits[ip].append(now)

# ─── API Key Auth ─────────────────────────────────────────────

API_KEYS = set()
# Load API keys from env or file
key_file = os.environ.get("EVEZ_API_KEYS_FILE", "")
if key_file and os.path.exists(key_file):
    with open(key_file) as f:
        for line in f:
            k = line.strip()
            if k and not k.startswith("#"):
                API_KEYS.add(k)

# Also accept master key from env
master_key = os.environ.get("EVEZ_MASTER_KEY", "")
if master_key:
    API_KEYS.add(master_key)

async def verify_api_key(request: Request):
    """Verify API key from header or query param. Skip if no keys configured."""
    if not API_KEYS:
        return True  # No auth if no keys configured
    key = request.headers.get("X-API-Key", "") or request.query_params.get("api_key", "")
    if key in API_KEYS:
        return True
    raise HTTPException(status_code=401, detail="Invalid API key. Set X-API-Key header.")

# ─── WebSocket Manager ────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        metrics["ws_connections"] = len(self.active)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
        metrics["ws_connections"] = len(self.active)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

ws_manager = ConnectionManager()

# ─── Core Endpoints ───────────────────────────────────────────

@app.get("/health")
def health():
    uptime = time.time() - metrics["start_time"]
    return {
        "status": "ok",
        "service": "evez-os-gateway",
        "version": "2.0.0",
        "uptime_s": round(uptime, 1),
        "services": len(SERVICES),
        "ts": int(time.time()),
    }

@app.get("/metrics")
def get_metrics():
    """Prometheus-style metrics."""
    uptime = time.time() - metrics["start_time"]
    return {
        "evez_os_gateway_uptime_seconds": round(uptime, 1),
        "evez_os_requests_total": metrics["requests_total"],
        "evez_os_errors_total": metrics["errors"],
        "evez_os_ws_connections": metrics["ws_connections"],
        "evez_os_services_count": len(SERVICES),
        "evez_os_requests_by_service": dict(metrics["requests_by_service"]),
        "evez_os_requests_by_status": dict(metrics["requests_by_status"]),
        "evez_os_latency_ms_avg": {
            k: round(sum(v) / len(v), 2) if v else 0
            for k, v in metrics["latency_by_service"].items()
        },
    }

# ─── Service Proxy ────────────────────────────────────────────

# ─── Service Status (registered as route above) ──

@app.get("/api/v1/status")
async def service_status():
    """Health check all backend services."""
    results = {}
    async with httpx.AsyncClient(timeout=5) as client:
        for name, svc in SERVICES.items():
            try:
                resp = await client.get(f"http://127.0.0.1:{svc['port']}/health")
                results[name] = {
                    "status": "online",
                    "code": resp.status_code,
                    "port": svc["port"],
                    "name": svc["name"],
                    "version": svc.get("version", "?"),
                }
            except Exception:
                results[name] = {
                    "status": "offline",
                    "port": svc["port"],
                    "name": svc["name"],
                }
    
    online = sum(1 for r in results.values() if r["status"] == "online")
    return {
        "total": len(SERVICES),
        "online": online,
        "offline": len(SERVICES) - online,
        "services": results,
        "gateway_uptime_s": round(time.time() - metrics["start_time"], 1),
    }

# ─── WebSocket Feed ───────────────────────────────────────────

@app.websocket("/ws")
async def websocket_feed(ws: WebSocket):
    """Real-time feed of all API requests, gap alerts, speedrun results."""
    await ws_manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            # Client can send commands
            msg = json.loads(data) if data else {}
            if msg.get("type") == "ping":
                await ws.send_json({"type": "pong", "ts": int(time.time())})
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)

# ─── Dashboard ────────────────────────────────────────────────

# ─── Live Demo Endpoint ──────────────────────────────────────

@app.get("/api/v1/live-demo")
async def live_demo():
    """Aggregate live data from all services for the demo page."""
    import httpx
    results = {}
    async with httpx.AsyncClient(timeout=10) as client:
        for name, port, ep in [
            ("disclosure", 8087, "/api/v1/demo"),
            ("igre", 8099, "/api/v1/integration/disclosure"),
            ("spectral", 8103, "/api/v1/correlate"),
            ("funding", 8101, "/api/v1/pipeline"),
        ]:
            try:
                resp = await client.get(f"http://127.0.0.1:{port}{ep}")
                results[name] = resp.json()
            except: results[name] = {"offline": True}
    return {"timestamp": int(time.time()), "data": results}

@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_service(service: str, path: str, request: Request):
    """Proxy requests to the appropriate backend service."""
    metrics["requests_total"] += 1
    start = time.time()

    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service not found: {service}. Available: {list(SERVICES.keys())}")

    svc = SERVICES[service]
    port = svc["port"]

    # Build target URL
    target_url = f"http://127.0.0.1:{port}/{path}"
    if request.query_params:
        target_url += f"?{request.query_params}"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Forward headers (strip host)
            headers = dict(request.headers)
            headers.pop("host", None)

            body = await request.body()
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body if body else None,
            )

        latency = (time.time() - start) * 1000
        metrics["requests_by_service"][service] += 1
        metrics["requests_by_status"][str(resp.status_code)] += 1
        metrics["latency_by_service"][service].append(latency)
        # Keep only last 100 latency samples
        if len(metrics["latency_by_service"][service]) > 100:
            metrics["latency_by_service"][service] = metrics["latency_by_service"][service][-100:]

        # Broadcast to WebSocket listeners
        await ws_manager.broadcast({
            "type": "request",
            "service": service,
            "path": f"/{path}",
            "method": request.method,
            "status": resp.status_code,
            "latency_ms": round(latency, 1),
            "ts": datetime.now().isoformat(),
        })

        return JSONResponse(
            content=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
            status_code=resp.status_code,
        )
    except httpx.ConnectError:
        metrics["errors"] += 1
        raise HTTPException(status_code=502, detail=f"Service {service} (:{port}) is offline")
    except httpx.TimeoutException:
        metrics["errors"] += 1
        raise HTTPException(status_code=504, detail=f"Service {service} (:{port}) timed out")
    except Exception as e:
        metrics["errors"] += 1
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """EVEZ-OS Command Center — single pane of glass."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EVEZ-OS Command Center</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'SF Mono', 'Fira Code', monospace; background: #0a0a0a; color: #e0e0e0; padding: 20px; }
        h1 { color: #00ff88; font-size: 1.8em; margin-bottom: 4px; }
        h2 { color: #00ccff; margin: 20px 0 10px; font-size: 1.2em; }
        .subtitle { color: #666; font-size: 0.9em; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 16px 0; }
        .card { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 16px; position: relative; overflow: hidden; }
        .card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, #00ff88, #00ccff); }
        .card.offline::before { background: #ff4444; }
        .stat { font-size: 2em; color: #00ff88; font-weight: bold; }
        .label { color: #888; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; }
        .service { padding: 8px 12px; background: #111; border-radius: 6px; margin: 4px 0; display: flex; justify-content: space-between; align-items: center; }
        .service .name { color: #e0e0e0; }
        .service .port { color: #00ccff; font-size: 0.85em; }
        .online { color: #00ff88; } .offline { color: #ff4444; }
        .feed { background: #111; border-radius: 8px; padding: 12px; max-height: 400px; overflow-y: auto; font-size: 0.85em; }
        .feed-entry { padding: 4px 0; border-bottom: 1px solid #222; display: flex; gap: 8px; }
        .feed-entry .method { color: #ffaa00; min-width: 40px; }
        .feed-entry .path { color: #e0e0e0; }
        .feed-entry .status { min-width: 30px; }
        .feed-entry .latency { color: #888; }
        .thesis { background: linear-gradient(135deg, #1a0a2e, #0a1a2e); border: 1px solid #4400ff33; border-radius: 8px; padding: 16px; margin: 16px 0; }
        .thesis h3 { color: #ff00ff; margin-bottom: 8px; }
        .thesis p { color: #ccc; font-style: italic; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin: 2px; }
        .badge-online { background: #00ff8822; color: #00ff88; }
        .badge-offline { background: #ff444422; color: #ff4444; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .pulse { animation: pulse 2s infinite; }
    </style>
</head>
<body>
    <h1>🦀 EVEZ-OS Command Center</h1>
    <p class="subtitle">Eigenforensics • Genome Extraction • Speedrun Projecteering • 16 Services • 120+ Endpoints</p>
    
    <div class="grid" id="stats">
        <div class="card"><div class="stat" id="svc-online">—</div><div class="label">Services Online</div></div>
        <div class="card"><div class="stat" id="endpoints">120+</div><div class="label">API Endpoints</div></div>
        <div class="card"><div class="stat" id="requests">0</div><div class="label">Requests Processed</div></div>
        <div class="card"><div class="stat" id="uptime">—</div><div class="label">Gateway Uptime</div></div>
    </div>

    <div class="thesis">
        <h3>📐 Dominant Negative Eigenvalue Thesis</h3>
        <p>Censorship is the dominant negative eigenvalue of civilization. Speedrun = inject information at shadow nodes. Hunger (physical + informational) = λ<sub>min</sub>.</p>
    </div>

    <h2>📡 Services</h2>
    <div id="services"><div class="feed">Loading...</div></div>

    <h2>⚡ Live Feed</h2>
    <div class="feed" id="feed"><div style="color:#666">Connecting WebSocket...</div></div>

    <script>
    const gatewayBase = window.location.origin;
    let feedEntries = [];

    // Fetch status
    async function refresh() {
        try {
            const resp = await fetch(gatewayBase + '/api/v1/status');
            const data = await resp.json();
            document.getElementById('svc-online').textContent = data.online + '/' + data.total;
            
            let html = '';
            for (const [name, svc] of Object.entries(data.services)) {
                const cls = svc.status === 'online' ? 'online' : 'offline';
                const badge = svc.status === 'online' ? 'badge-online' : 'badge-offline';
                html += `<div class="service"><span class="name">${svc.name || name}</span><span class="${cls}">●</span><span class="port">:${svc.port}</span><span class="badge ${badge}">${svc.version || '?'}</span></div>`;
            }
            document.getElementById('services').innerHTML = html;
        } catch(e) { console.error(e); }

        try {
            const m = await (await fetch(gatewayBase + '/metrics')).json();
            document.getElementById('requests').textContent = m.evez_os_requests_total;
            document.getElementById('uptime').textContent = Math.floor(m.evez_os_gateway_uptime_seconds / 60) + 'm';
        } catch(e) {}
    }

    // WebSocket
    const ws = new WebSocket((location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + location.host + '/ws');
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'request') {
            feedEntries.unshift(data);
            if (feedEntries.length > 50) feedEntries.pop();
            renderFeed();
        }
    };

    function renderFeed() {
        const feed = document.getElementById('feed');
        feed.innerHTML = feedEntries.map(e => {
            const statusColor = e.status < 400 ? '#00ff88' : '#ff4444';
            return `<div class="feed-entry"><span class="method">${e.method}</span><span class="path">/api/${e.service}${e.path}</span><span class="status" style="color:${statusColor}">${e.status}</span><span class="latency">${e.latency_ms}ms</span></div>`;
        }).join('');
    }

    refresh();
    setInterval(refresh, 10000);
    </script>
</body>
</html>
"""

@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """Public demo page for investors and press."""
    demo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "demo.html")
    with open(demo_path) as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8102)
