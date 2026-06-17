#!/usr/bin/env python3
"""
EVEZ PULSE — Port 10002
Uptime monitor + incident response. Checks any URL every 60s.
$0/month. Runs on cron, stores in SQLite.
"""
import json, time, sqlite3, asyncio, hashlib
from aiohttp import web
import aiohttp

PORT = 10002
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/pulse/pulse.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS monitors (
        id TEXT PRIMARY KEY, url TEXT, name TEXT, interval INTEGER DEFAULT 60,
        timeout INTEGER DEFAULT 10, expected_status INTEGER DEFAULT 200,
        active BOOLEAN DEFAULT 1, created REAL
    );
    CREATE TABLE IF NOT EXISTS checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, monitor_id TEXT, status_code INTEGER,
        latency_ms REAL, up BOOLEAN, error TEXT, timestamp REAL
    );
    CREATE TABLE IF NOT EXISTS incidents (
        id TEXT PRIMARY KEY, monitor_id TEXT, started REAL, ended REAL,
        duration_s REAL, status TEXT DEFAULT 'open'
    );
""")
DB.commit()

async def check_url(url, timeout=10, expected=200):
    """Check a URL and return status"""
    try:
        start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout),
                                   ssl=False) as resp:
                latency = (time.time() - start) * 1000
                up = resp.status == expected
                return {"status_code": resp.status, "latency_ms": round(latency), "up": up, "error": None}
    except Exception as e:
        return {"status_code": 0, "latency_ms": 0, "up": False, "error": str(e)[:100]}

async def handle_add_monitor(req):
    body = await req.json()
    mid = hashlib.md5(f"{body['url']}{time.time()}".encode()).hexdigest()[:10]
    DB.execute("INSERT INTO monitors VALUES (?,?,?,?,?,?,?,?)",
              (mid, body["url"], body.get("name", body["url"]), body.get("interval", 60),
               body.get("timeout", 10), body.get("expected_status", 200), 1, time.time()))
    DB.commit()
    return web.json_response({"id": mid, "url": body["url"], "status": "monitoring"})

async def handle_check_now(req):
    url = req.query.get("url", "")
    timeout = int(req.query.get("timeout", "10"))
    if not url:
        return web.json_response({"error": "url required"}, status=400)
    result = await check_url(url, timeout)
    return web.json_response({"url": url, **result})

async def handle_monitors(req):
    rows = DB.execute("SELECT * FROM monitors WHERE active=1").fetchall()
    return web.json_response({"monitors": [dict(r) for r in rows]})

async def handle_history(req):
    mid = req.query.get("monitor_id", "")
    limit = int(req.query.get("limit", "100"))
    rows = DB.execute("SELECT * FROM checks WHERE monitor_id=? ORDER BY timestamp DESC LIMIT ?",
                      (mid, limit)).fetchall()
    return web.json_response({"checks": [dict(r) for r in rows]})

async def handle_uptime(req):
    mid = req.query.get("monitor_id", "")
    checks = DB.execute("SELECT COUNT(*) as total, SUM(CASE WHEN up=1 THEN 1 ELSE 0 END) as up_count FROM checks WHERE monitor_id=?", (mid,)).fetchone()
    uptime_pct = (checks["up_count"] / max(checks["total"], 1)) * 100
    avg_latency = DB.execute("SELECT AVG(latency_ms) as a FROM checks WHERE monitor_id=?", (mid,)).fetchone()["a"] or 0
    return web.json_response({"monitor_id": mid, "uptime_pct": round(uptime_pct, 2),
                             "avg_latency_ms": round(avg_latency), "total_checks": checks["total"]})

async def handle_health(req):
    monitors = DB.execute("SELECT COUNT(*) as c FROM monitors WHERE active=1").fetchone()["c"]
    checks = DB.execute("SELECT COUNT(*) as c FROM checks").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-pulse",
                             "monitors": monitors, "total_checks": checks, "port": PORT})

async def handle_check_all(req):
    """Run all active monitors"""
    monitors = DB.execute("SELECT * FROM monitors WHERE active=1").fetchall()
    results = []
    for m in monitors:
        result = await check_url(m["url"], m["timeout"], m["expected_status"])
        DB.execute("INSERT INTO checks (monitor_id, status_code, latency_ms, up, error, timestamp) VALUES (?,?,?,?,?,?)",
                  (m["id"], result["status_code"], result["latency_ms"], result["up"], result["error"], time.time()))
        if not result["up"]:
            iid = hashlib.md5(f"{m['id']}{time.time()}".encode()).hexdigest()[:10]
            DB.execute("INSERT OR IGNORE INTO incidents (id, monitor_id, started, status) VALUES (?,?,?,?)",
                      (iid, m["id"], time.time(), "open"))
        results.append({"monitor": m["name"], "up": result["up"], "latency_ms": result["latency_ms"]})
    DB.commit()
    return web.json_response({"checked": len(results), "results": results})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/monitors", handle_add_monitor)
app.router.add_get("/v1/monitors", handle_monitors)
app.router.add_get("/v1/check", handle_check_now)
app.router.add_get("/v1/check-all", handle_check_all)
app.router.add_get("/v1/history", handle_history)
app.router.add_get("/v1/uptime", handle_uptime)

if __name__ == "__main__":
    import os; os.makedirs("/home/openclaw/evez-ecosystem/pulse", exist_ok=True)
    print(f"💚 EVEZ Pulse → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
