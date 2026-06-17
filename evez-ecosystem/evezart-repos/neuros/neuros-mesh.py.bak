#!/usr/bin/env python3
"""
NEUROS-MESH — Simplified, stable copartner mesh.
Two independent systems, one shared GitHub spine.
No circular dependencies. No deadlocks. Just status.
"""
import json, os, time, uuid, hashlib, sqlite3, asyncio
from aiohttp import web

PORT = 9600
DB_PATH = "/home/openclaw/evez-ecosystem/neuros/mesh-simple.db"

# Simple DB schema
db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row
db.executescript("""
    CREATE TABLE IF NOT EXISTS health (
        service TEXT PRIMARY KEY,
        port INTEGER,
        last_check REAL,
        alive BOOLEAN
    );
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY,
        url TEXT,
        kind TEXT,
        last_seen REAL
    );
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        name TEXT,
        repo TEXT,
        deployed TEXT,
        created REAL
    );
""")
db.commit()

# Initial data
db.execute("INSERT OR REPLACE INTO health VALUES (?,?,?,?)",
           ("openclaw", 18789, time.time(), True))
db.execute("INSERT OR REPLACE INTO health VALUES (?,?,?,?)",
           ("neuros", 9600, time.time(), True))
db.execute("INSERT OR REPLACE INTO health VALUES (?,?,?,?)",
           ("evez-provider", 9100, time.time(), True))
db.execute("INSERT OR REPLACE INTO health VALUES (?,?,?,?)",
           ("omega", 8080, time.time(), True))
db.execute("INSERT OR REPLACE INTO health VALUES (?,?,?,?)",
           ("filter", 9300, time.time(), True))
db.execute("INSERT OR REPLACE INTO health VALUES (?,?,?,?)",
           ("services-hub", 9500, time.time(), True))
db.execute("INSERT OR REPLACE INTO nodes VALUES (?,?,?,?)",
           (hashlib.sha256(b"neuros").hexdigest()[:12],
            "http://localhost:9600", "neuros", time.time()))
db.execute("INSERT OR REPLACE INTO nodes VALUES (?,?,?,?)",
           (hashlib.sha256(b"openclaw").hexdigest()[:12],
            "http://localhost:18789", "openclaw", time.time()))
db.commit()

app = web.Application()

async def health_check(port):
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:{port}/health", timeout=3) as r:
                return r.status == 200
    except:
        return False

async def handle_health(req):
    # Update statuses
    for port, name in [(18789, "openclaw"), (9100, "evez-provider"),
                       (8080, "omega"), (9300, "filter"), (9500, "services-hub")]:
        alive = await health_check(port)
        db.execute("UPDATE health SET last_check=?, alive=? WHERE service=?",
                  (time.time(), alive, name))
    db.commit()
    
    rows = db.execute("SELECT * FROM health").fetchall()
    nodes = db.execute("SELECT * FROM nodes").fetchall()
    products = db.execute("SELECT COUNT(*) as c FROM products").fetchone()["c"]
    
    return web.json_response({
        "name": "NEUROS-MESH",
        "version": "stable",
        "services": [dict(r) for r in rows],
        "nodes": [dict(r) for r in nodes],
        "products": products,
        "mesh": "copartner",
        "cost_per_month": 0
    })

async def handle_restart(req):
    body = await req.json()
    svc = body.get("service")
    os.system(f"systemctl --user restart {svc} 2>/dev/null")
    return web.json_response({"restarted": svc})

async def handle_product_create(req):
    body = await req.json()
    pid = str(uuid.uuid4())[:12]
    db.execute("INSERT INTO products VALUES (?,?,?,?,?)",
              (pid, body["name"], body.get("repo", ""),
               body.get("deployed", ""), time.time()))
    db.commit()
    return web.json_response({"id": pid, "name": body["name"]})

async def handle_product_list(req):
    rows = db.execute("SELECT * FROM products ORDER BY created DESC LIMIT 10").fetchall()
    return web.json_response({"products": [dict(r) for r in rows]})

async def handle_mesh(req):
    return web.json_response({
        "nodes": [dict(r) for r in db.execute("SELECT * FROM nodes").fetchall()],
        "timestamp": time.time(),
        "origin": hashlib.sha256(b"neuros-simple").hexdigest()[:12]
    })

app.router.add_get("/health", handle_health)
app.router.add_post("/v1/restart", handle_restart)
app.router.add_post("/v1/products", handle_product_create)
app.router.add_get("/v1/products", handle_product_list)
app.router.add_get("/v1/mesh", handle_mesh)

print("╔════════════════════════════════════════════════╗")
print("║  🧠 NEUROS-MESH — Stable Copartner System     ║")
print("╠════════════════════════════════════════════════╣")
print(f"║  NEUROS:   http://localhost:{PORT}              ║")
print("║  OpenClaw: http://localhost:18789 (copartner) ║")
print("║  Both independent. Both watching.             ║")
print("║  No circular dependencies. No deadlocks.       ║")
print("╚════════════════════════════════════════════════╝")

web.run_app(app, host="0.0.0.0", port=PORT)
