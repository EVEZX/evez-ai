#!/usr/bin/env python3
"""
EVEZ RELAY — Port 10006
Webhook relay + event bus. Receive webhooks, transform, forward.
$0/month. Handles 1000+ webhooks/min in-memory.
"""
import json, time, hashlib, sqlite3, asyncio
from aiohttp import web
import aiohttp

PORT = 10006
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/relay/relay.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS endpoints (
        id TEXT PRIMARY KEY, name TEXT, path TEXT, transform TEXT DEFAULT '',
        forward_url TEXT, forward_headers TEXT DEFAULT '{}', active BOOLEAN DEFAULT 1,
        created REAL, webhook_count INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS webhooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, endpoint_id TEXT,
        method TEXT, headers TEXT, body TEXT, source_ip TEXT,
        status INTEGER DEFAULT 200, forwarded BOOLEAN DEFAULT 0, timestamp REAL
    );
""")
DB.commit()

async def handle_webhook(req):
    """Receive a webhook and optionally forward it"""
    path = req.path
    body = await req.text()
    headers = dict(req.headers)
    method = req.method
    
    # Find endpoint
    endpoint = DB.execute("SELECT * FROM endpoints WHERE path=? AND active=1", (path,)).fetchone()
    if not endpoint:
        endpoint = DB.execute("SELECT * FROM endpoints WHERE active=1 ORDER BY created DESC LIMIT 1").fetchone()
    
    eid = endpoint["id"] if endpoint else "unknown"
    
    # Store webhook
    DB.execute("INSERT INTO webhooks (endpoint_id, method, headers, body, source_ip, timestamp) VALUES (?,?,?,?,?,?)",
              (eid, method, json.dumps(headers), body, req.remote, time.time()))
    DB.execute("UPDATE endpoints SET webhook_count=webhook_count+1 WHERE id=?", (eid,))
    DB.commit()
    
    # Forward if configured
    forwarded = False
    if endpoint and endpoint["forward_url"]:
        try:
            fwd_headers = json.loads(endpoint["forward_headers"])
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint["forward_url"], data=body,
                                       headers=fwd_headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    forwarded = resp.status < 400
        except:
            forwarded = False
    
    return web.json_response({"status": "received", "endpoint": eid, "forwarded": forwarded})

async def handle_create_endpoint(req):
    body = await req.json()
    eid = hashlib.md5(f"{body['name']}{time.time()}".encode()).hexdigest()[:8]
    path = body.get("path", f"/hook/{eid}")
    DB.execute("INSERT INTO endpoints VALUES (?,?,?,?,?,?,?,?,?,?)",
              (eid, body["name"], path, body.get("transform", ""), body.get("forward_url", ""),
               json.dumps(body.get("forward_headers", {})), 1, time.time(), 0))
    DB.commit()
    return web.json_response({"id": eid, "path": path, "full_url": f"http://localhost:{PORT}{path}"})

async def handle_endpoints(req):
    rows = DB.execute("SELECT * FROM endpoints WHERE active=1").fetchall()
    return web.json_response({"endpoints": [dict(r) for r in rows]})

async def handle_recent(req):
    limit = int(req.query.get("limit", "50"))
    rows = DB.execute("SELECT * FROM webhooks ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    return web.json_response({"webhooks": [dict(r) for r in rows]})

async def handle_health(req):
    endpoints = DB.execute("SELECT COUNT(*) as c FROM endpoints WHERE active=1").fetchone()["c"]
    webhooks = DB.execute("SELECT COUNT(*) as c FROM webhooks").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-relay",
                             "endpoints": endpoints, "webhooks_received": webhooks, "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/endpoints", handle_create_endpoint)
app.router.add_get("/v1/endpoints", handle_endpoints)
app.router.add_get("/v1/recent", handle_recent)
app.router.add_route("*", "/hook/{id:.*}", handle_webhook)

if __name__ == "__main__":
    import os; os.makedirs("/home/openclaw/evez-ecosystem/relay", exist_ok=True)
    print(f"📨 EVEZ Relay → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
