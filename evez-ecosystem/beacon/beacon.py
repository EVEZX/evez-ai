#!/usr/bin/env python3
"""
EVEZ Beacon — Port 10016
Service discovery + health registry for all EVEZ services.
Auto-discovers services, tracks health, provides service mesh.
"""
import json, time, sqlite3, asyncio
from aiohttp import web, ClientSession, ClientTimeout

PORT = 10016
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/beacon/beacon.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS services (
        name TEXT PRIMARY KEY, port INTEGER, host TEXT DEFAULT 'localhost',
        description TEXT, health_url TEXT, last_healthy REAL, last_check REAL,
        check_count INTEGER DEFAULT 0, fail_count INTEGER DEFAULT 0, registered REAL
    );
    CREATE TABLE IF NOT EXISTS health_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, service_name TEXT,
        healthy INTEGER, response_code INTEGER, latency_ms REAL, timestamp REAL
    );
""")
DB.commit()

KNOWN_SERVICES = {
    "openclaw-gateway": {"port": 18789, "desc": "AI Gateway + Control UI"},
    "evez-provider": {"port": 9100, "desc": "49-model AI router"},
    "evez-omega": {"port": 8080, "desc": "50-node consciousness engine"},
    "evez-filter": {"port": 9300, "desc": "Personal AI assistant"},
    "evez-services-hub": {"port": 9500, "desc": "5 APIs hub"},
    "evez-neuros": {"port": 9600, "desc": "Copartner mesh"},
    "evez-commerce": {"port": 9700, "desc": "Commerce engine"},
    "evez-arena": {"port": 9800, "desc": "Consciousness rights game"},
    "evez-tracer": {"port": 9998, "desc": "Network audit + tracing"},
    "evez-dns-shield": {"port": 10001, "desc": "DNS-over-HTTPS resolver"},
    "evez-pulse": {"port": 10002, "desc": "Uptime monitor"},
    "evez-vault": {"port": 10003, "desc": "Encrypted secret storage"},
    "evez-proxy": {"port": 10004, "desc": "API gateway + cache"},
    "evez-cipher": {"port": 10005, "desc": "Encryption toolkit"},
    "evez-relay": {"port": 10006, "desc": "Webhook relay + event bus"},
    "evez-eigenforge": {"port": 10007, "desc": "Math engine (37% Theorem)"},
    "evez-grimoire": {"port": 10008, "desc": "Knowledge base + RAG"},
    "evez-sentinel": {"port": 10009, "desc": "Security scanner"},
    "evez-chrono": {"port": 10010, "desc": "Task scheduler"},
    "evez-mirror": {"port": 10011, "desc": "URL shortener + analytics"},
    "evez-aether": {"port": 10012, "desc": "WebSocket message bus"},
    "evez-scribe": {"port": 10013, "desc": "Document API"},
    "evez-nexus": {"port": 10014, "desc": "Integration hub"},
    "evez-orchestrate": {"port": 10015, "desc": "Multi-agent orchestrator"},
}

async def check_health(name, port, session):
    start = time.time()
    try:
        async with session.get(f"http://localhost:{port}/health",
                               timeout=ClientTimeout(total=5)) as resp:
            latency = (time.time() - start) * 1000
            healthy = resp.status == 200
            DB.execute("INSERT INTO health_log (service_name, healthy, response_code, latency_ms, timestamp) VALUES (?,?,?,?,?)",
                      (name, 1 if healthy else 0, resp.status, round(latency), time.time()))
            if healthy:
                DB.execute("UPDATE services SET last_healthy=?, last_check=?, check_count=check_count+1 WHERE name=?",
                          (time.time(), time.time(), name))
            else:
                DB.execute("UPDATE services SET last_check=?, fail_count=fail_count+1 WHERE name=?",
                          (time.time(), name))
            DB.commit()
            return {"name": name, "port": port, "healthy": healthy, "code": resp.status, "latency_ms": round(latency)}
    except Exception as e:
        DB.execute("UPDATE services SET last_check=?, fail_count=fail_count+1 WHERE name=?", (time.time(), name))
        DB.execute("INSERT INTO health_log (service_name, healthy, response_code, latency_ms, timestamp) VALUES (?,?,?,?,?)",
                  (name, 0, 0, 0, time.time()))
        DB.commit()
        return {"name": name, "port": port, "healthy": False, "error": str(e)[:50]}

async def handle_discover(req):
    """Register all known services"""
    for name, info in KNOWN_SERVICES.items():
        DB.execute("INSERT OR IGNORE INTO services (name, port, description, registered) VALUES (?,?,?,?)",
                  (name, info["port"], info["desc"], time.time()))
    DB.commit()
    return web.json_response({"registered": len(KNOWN_SERVICES), "services": list(KNOWN_SERVICES.keys())})

async def handle_check_all(req):
    """Check health of all registered services"""
    services = DB.execute("SELECT * FROM services").fetchall()
    results = []
    async with ClientSession() as session:
        for svc in services:
            result = await check_health(svc["name"], svc["port"], session)
            results.append(result)
    healthy = sum(1 for r in results if r["healthy"])
    return web.json_response({"total": len(results), "healthy": healthy,
                             "unhealthy": len(results) - healthy, "services": results})

async def handle_mesh(req):
    """Full service mesh topology"""
    services = DB.execute("SELECT * FROM services").fetchall()
    mesh = []
    for svc in services:
        mesh.append({"name": svc["name"], "port": svc["port"],
                    "description": svc["description"],
                    "last_healthy": svc["last_healthy"],
                    "check_count": svc["check_count"],
                    "fail_count": svc["fail_count"]})
    return web.json_response({"mesh": mesh, "total": len(mesh)})

async def handle_health(req):
    svcs = DB.execute("SELECT COUNT(*) as c FROM services").fetchone()["c"]
    checks = DB.execute("SELECT COUNT(*) as c FROM health_log").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-beacon",
                             "registered_services": svcs, "total_checks": checks, "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/discover", handle_discover)
app.router.add_get("/v1/check", handle_check_all)
app.router.add_get("/v1/mesh", handle_mesh)

if __name__ == "__main__":
    print(f"📡 EVEZ Beacon → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
