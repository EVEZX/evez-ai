#!/usr/bin/env python3
"""
EVEZ PROXY — Port 10004
Intelligent API gateway with rate limiting, caching, load balancing.
$0/month. In-memory cache with TTL.
"""
import json, time, hashlib, sqlite3, asyncio
from aiohttp import web
import aiohttp

PORT = 10004
CACHE = {}  # {hash: {response, expiry}}
RATE_LIMITS = {}  # {api_key: {count, window_start}}
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/proxy-gateway/proxy.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS routes (
        id TEXT PRIMARY KEY, path TEXT, upstream TEXT, methods TEXT DEFAULT 'GET',
        cache_ttl INTEGER DEFAULT 0, rate_limit INTEGER DEFAULT 100,
        auth_required BOOLEAN DEFAULT 0, active BOOLEAN DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT, route_id TEXT, method TEXT,
        status INTEGER, latency_ms REAL, cached BOOLEAN, timestamp REAL
    );
""")
DB.commit()

async def handle_proxy(req):
    """Reverse proxy with caching and rate limiting"""
    path = req.path_qs
    method = req.method
    
    # Find matching route
    route = DB.execute("SELECT * FROM routes WHERE ? LIKE path || '%' AND active=1", (path,)).fetchone()
    if not route:
        return web.json_response({"error": "No route found"}, status=404)
    
    # Rate limiting
    client_id = req.headers.get("X-API-Key", req.remote)
    now = time.time()
    rl_key = f"{client_id}:{route['id']}"
    if rl_key in RATE_LIMITS:
        rl = RATE_LIMITS[rl_key]
        if now - rl["window_start"] > 60:
            RATE_LIMITS[rl_key] = {"count": 1, "window_start": now}
        elif rl["count"] >= route["rate_limit"]:
            return web.json_response({"error": "Rate limited", "retry_after": 60}, status=429)
        else:
            rl["count"] += 1
    else:
        RATE_LIMITS[rl_key] = {"count": 1, "window_start": now}
    
    # Cache check
    cache_key = hashlib.md5(f"{method}:{path}".encode()).hexdigest()
    if route["cache_ttl"] > 0 and cache_key in CACHE:
        cached = CACHE[cache_key]
        if now < cached["expiry"]:
            DB.execute("INSERT INTO stats (route_id, method, status, latency_ms, cached, timestamp) VALUES (?,?,?,?,?,?)",
                      (route["id"], method, 200, 0, 1, now))
            DB.commit()
            return web.Response(text=cached["response"], content_type="application/json")
    
    # Proxy request
    upstream_url = f"{route['upstream']}{path}"
    start = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, upstream_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                body = await resp.text()
                latency = (time.time() - start) * 1000
                
                # Cache if TTL > 0
                if route["cache_ttl"] > 0:
                    CACHE[cache_key] = {"response": body, "expiry": now + route["cache_ttl"]}
                
                DB.execute("INSERT INTO stats (route_id, method, status, latency_ms, cached, timestamp) VALUES (?,?,?,?,?,?)",
                          (route["id"], method, resp.status, round(latency), 0, now))
                DB.commit()
                return web.Response(text=body, status=resp.status, content_type="application/json")
    except Exception as e:
        return web.json_response({"error": str(e)[:100]}, status=502)

async def handle_add_route(req):
    body = await req.json()
    rid = hashlib.md5(f"{body['path']}{body['upstream']}".encode()).hexdigest()[:8]
    DB.execute("INSERT OR REPLACE INTO routes VALUES (?,?,?,?,?,?,?,?)",
              (rid, body["path"], body["upstream"], body.get("methods", "GET"),
               body.get("cache_ttl", 0), body.get("rate_limit", 100),
               body.get("auth_required", False), 1))
    DB.commit()
    return web.json_response({"id": rid, "status": "created"})

async def handle_routes(req):
    rows = DB.execute("SELECT * FROM routes WHERE active=1").fetchall()
    return web.json_response({"routes": [dict(r) for r in rows]})

async def handle_stats(req):
    total = DB.execute("SELECT COUNT(*) as c FROM stats").fetchone()["c"]
    cached = DB.execute("SELECT COUNT(*) as c FROM stats WHERE cached=1").fetchone()["c"]
    avg_lat = DB.execute("SELECT AVG(latency_ms) as a FROM stats").fetchone()["a"] or 0
    return web.json_response({"total_requests": total, "cached_requests": cached,
                             "cache_hit_rate": round(cached / max(total, 1) * 100, 1),
                             "avg_latency_ms": round(avg_lat), "cache_entries": len(CACHE)})

async def handle_health(req):
    routes = DB.execute("SELECT COUNT(*) as c FROM routes WHERE active=1").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-proxy",
                             "routes": routes, "cache_size": len(CACHE), "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/routes", handle_add_route)
app.router.add_get("/v1/routes", handle_routes)
app.router.add_get("/v1/stats", handle_stats)
# Catch-all proxy handler must be last
app.router.add_route("*", "/{path:.*}", handle_proxy)

if __name__ == "__main__":
    import os; os.makedirs("/home/openclaw/evez-ecosystem/proxy-gateway", exist_ok=True)
    print(f"🔀 EVEZ Proxy Gateway → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
