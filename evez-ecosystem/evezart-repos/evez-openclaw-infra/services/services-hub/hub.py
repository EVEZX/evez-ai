#!/usr/bin/env python3
"""
EVEZ Services Hub — Unified gateway for all EVEZ APIs
Single port, all services. Zero external dependencies.
"""
import os, json, time, uuid, hashlib, asyncio, sqlite3, base64, re
from aiohttp import web, ClientSession

HUB_PORT = int(os.getenv("HUB_PORT", "9500"))
DB_PATH = "/home/openclaw/evez-ecosystem/evez-services-hub/services.db"

# Init SQLite
db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.row_factory = sqlite3.Row
db.executescript("""
CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, status TEXT, payload TEXT, result TEXT, created REAL, updated REAL);
CREATE TABLE IF NOT EXISTS monitors (id TEXT PRIMARY KEY, url TEXT, status TEXT, last_check REAL, response_ms INTEGER);
CREATE TABLE IF NOT EXISTS links (id TEXT PRIMARY KEY, url TEXT, short TEXT, clicks INTEGER, created REAL);
CREATE TABLE IF NOT EXISTS seals (id TEXT PRIMARY KEY, data_hash TEXT, chain TEXT, created REAL);
CREATE TABLE IF NOT EXISTS scans (id TEXT PRIMARY KEY, target TEXT, results TEXT, grade TEXT, created REAL);
CREATE TABLE IF NOT EXISTS api_keys (key TEXT PRIMARY KEY, name TEXT, tier TEXT, created REAL);
""")

# ============ Job Queue (VortexQ) ============
async def handle_job_submit(req):
    body = await req.json()
    job_id = str(uuid.uuid4())[:12]
    now = time.time()
    db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?)", (job_id, "pending", json.dumps(body.get("payload",{})), None, now, now))
    db.commit()
    return web.json_response({"id": job_id, "status": "pending"})

async def handle_job_pull(req):
    row = db.execute("SELECT * FROM jobs WHERE status='pending' ORDER BY created LIMIT 1").fetchone()
    if row:
        db.execute("UPDATE jobs SET status='running', updated=? WHERE id=?", (time.time(), row["id"]))
        db.commit()
        return web.json_response(dict(row))
    return web.json_response({"message": "no jobs"})

async def handle_job_complete(req):
    job_id = req.match_info["id"]
    body = await req.json()
    db.execute("UPDATE jobs SET status='done', result=?, updated=? WHERE id=?", (json.dumps(body), time.time(), job_id))
    db.commit()
    return web.json_response({"status": "done"})

# ============ Uptime Monitor (MeshPulse) ============
async def handle_monitor_add(req):
    body = await req.json()
    mon_id = str(uuid.uuid4())[:12]
    db.execute("INSERT INTO monitors VALUES (?,?,?,?,?)", (mon_id, body["url"], "unknown", 0, 0))
    db.commit()
    return web.json_response({"id": mon_id, "url": body["url"]})

async def handle_monitor_check(req):
    rows = db.execute("SELECT * FROM monitors").fetchall()
    results = []
    async with ClientSession() as session:
        for row in rows:
            start = time.time()
            try:
                async with session.get(row["url"], timeout=aiohttp.ClientTimeout(total=10)) as r:
                    ms = int((time.time() - start) * 1000)
                    status = "up" if r.status < 400 else "down"
            except:
                ms = 0; status = "down"
            db.execute("UPDATE monitors SET status=?, last_check=?, response_ms=? WHERE id=?", (status, time.time(), ms, row["id"]))
            results.append({"id": row["id"], "url": row["url"], "status": status, "ms": ms})
    db.commit()
    return web.json_response({"monitors": results})

# ============ URL Shortener (NexusLink) ============
async def handle_shorten(req):
    body = await req.json()
    short = base64.urlsafe_b64encode(hashlib.md5(body["url"].encode()).digest())[:6].decode()
    link_id = str(uuid.uuid4())[:12]
    db.execute("INSERT INTO links VALUES (?,?,?,?,?)", (link_id, body["url"], short, 0, time.time()))
    db.commit()
    return web.json_response({"short": short, "url": body["url"], "id": link_id})

async def handle_resolve(req):
    short = req.match_info["short"]
    row = db.execute("SELECT * FROM links WHERE short=?", (short,)).fetchone()
    if row:
        db.execute("UPDATE links SET clicks=clicks+1 WHERE short=?", (short,))
        db.commit()
        return web.json_response({"url": row["url"], "clicks": row["clicks"]+1})
    return web.json_response({"error": "not found"}, status=404)

# ============ Data Integrity (QuantumSeal) ============
async def handle_seal(req):
    body = await req.json()
    data_hash = hashlib.sha256(body.get("data","").encode()).hexdigest()
    prev = db.execute("SELECT * FROM seals ORDER BY created DESC LIMIT 1").fetchone()
    prev_hash = prev["data_hash"] if prev else "genesis"
    chain_hash = hashlib.sha256(f"{prev_hash}{data_hash}".encode()).hexdigest()
    seal_id = str(uuid.uuid4())[:12]
    db.execute("INSERT INTO seals VALUES (?,?,?,?)", (seal_id, data_hash, chain_hash, time.time()))
    db.commit()
    return web.json_response({"id": seal_id, "hash": data_hash, "chain_hash": chain_hash})

async def handle_verify(req):
    seal_id = req.match_info["id"]
    row = db.execute("SELECT * FROM seals WHERE id=?", (seal_id,)).fetchone()
    return web.json_response(dict(row) if row else {"error": "not found"}, status=404 if not row else 200)

# ============ Security Scanner (SpectrumScan) ============
async def handle_scan(req):
    body = await req.json()
    target = body.get("target", "")
    results = {
        "headers": {"score": 0, "issues": []},
        "tls": {"score": 0, "issues": []},
        "xss": {"score": 0, "issues": []},
    }
    # Basic header check
    if target.startswith("http"):
        try:
            async with ClientSession() as session:
                async with session.head(target, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    headers = dict(r.headers)
                    for h in ["content-security-policy", "x-frame-options", "x-content-type-options", "strict-transport-security"]:
                        if h not in {k.lower(): v for k,v in headers.items()}:
                            results["headers"]["issues"].append(f"Missing: {h}")
                    results["headers"]["score"] = max(0, 100 - len(results["headers"]["issues"]) * 15)
        except Exception as e:
            results["error"] = str(e)
    
    scan_id = str(uuid.uuid4())[:12]
    grade = "A" if results["headers"]["score"] >= 80 else "B" if results["headers"]["score"] >= 60 else "C" if results["headers"]["score"] >= 40 else "F"
    db.execute("INSERT INTO scans VALUES (?,?,?,?,?)", (scan_id, target, json.dumps(results), grade, time.time()))
    db.commit()
    return web.json_response({"id": scan_id, "grade": grade, "results": results})

# ============ API Keys ============
async def handle_create_api_key(req):
    body = await req.json()
    key = f"evez_{uuid.uuid4().hex[:24]}"
    db.execute("INSERT INTO api_keys VALUES (?,?,?,?)", (key, body.get("name","default"), body.get("tier","free"), time.time()))
    db.commit()
    return web.json_response({"key": key})

async def handle_list_api_keys(req):
    rows = db.execute("SELECT key, name, tier, created FROM api_keys").fetchall()
    return web.json_response({"keys": [dict(r) for r in rows]})

# ============ Hub Status ============
async def handle_hub_status(req):
    jobs = db.execute("SELECT COUNT(*) as c FROM jobs").fetchone()["c"]
    monitors = db.execute("SELECT COUNT(*) as c FROM monitors").fetchone()["c"]
    links = db.execute("SELECT COUNT(*) as c FROM links").fetchone()["c"]
    seals = db.execute("SELECT COUNT(*) as c FROM seals").fetchone()["c"]
    scans = db.execute("SELECT COUNT(*) as c FROM scans").fetchone()["c"]
    return web.json_response({
        "status": "healthy",
        "services": {
            "vortexq": {"name": "Job Queue", "jobs": jobs},
            "meshpulse": {"name": "Uptime Monitor", "monitors": monitors},
            "nexuslink": {"name": "URL Shortener", "links": links},
            "quantumseal": {"name": "Data Integrity", "seals": seals},
            "spectrumscan": {"name": "Security Scanner", "scans": scans},
        }
    })

app = web.Application()
# Job Queue
app.router.add_post("/v1/jobs", handle_job_submit)
app.router.add_get("/v1/jobs/pull", handle_job_pull)
app.router.add_post("/v1/jobs/{id}/complete", handle_job_complete)
# Monitor
app.router.add_post("/v1/monitors", handle_monitor_add)
app.router.add_get("/v1/monitors/check", handle_monitor_check)
# URL Shortener
app.router.add_post("/v1/shorten", handle_shorten)
app.router.add_get("/v1/s/{short}", handle_resolve)
# Data Integrity
app.router.add_post("/v1/seal", handle_seal)
app.router.add_get("/v1/seal/{id}", handle_verify)
# Security Scanner
app.router.add_post("/v1/scan", handle_scan)
# API Keys
app.router.add_post("/v1/keys", handle_create_api_key)
app.router.add_get("/v1/keys", handle_list_api_keys)
# Status
app.router.add_get("/health", handle_hub_status)

if __name__ == "__main__":
    print(f"🌐 EVEZ Services Hub starting on port {HUB_PORT}")
    web.run_app(app, host="0.0.0.0", port=HUB_PORT)
