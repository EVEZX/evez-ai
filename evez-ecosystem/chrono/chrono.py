#!/usr/bin/env python3
"""
EVEZ CHRONO — Port 10010
Task scheduler + job queue. Cron-as-a-service. Delayed execution.
$0/month. SQLite-backed, persistent across restarts.
"""
import json, time, hashlib, sqlite3, asyncio, threading
from aiohttp import web

PORT = 10010
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/chrono/chrono.db", check_same_thread=False)
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, name TEXT, url TEXT, method TEXT DEFAULT 'POST',
        headers TEXT DEFAULT '{}', body TEXT DEFAULT '',
        schedule_type TEXT, schedule_value TEXT,
        next_run REAL, last_run REAL, run_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active', created REAL
    );
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT,
        status_code INTEGER, response TEXT, latency_ms REAL, error TEXT, timestamp REAL
    );
""")
DB.commit()

def get_next_run(schedule_type, schedule_value):
    now = time.time()
    if schedule_type == "delay":
        return now + float(schedule_value)
    elif schedule_type == "interval":
        return now + float(schedule_value)
    elif schedule_type == "cron":
        # Simple cron: every N seconds for now
        try:
            return now + float(schedule_value)
        except:
            return now + 60
    return now + 60

async def execute_job(job):
    """Execute a scheduled job"""
    try:
        async with aiohttp.ClientSession() as session:
            import aiohttp as aio
            start = time.time()
            method = job["method"]
            headers = json.loads(job["headers"]) if job["headers"] else {}
            async with session.request(method, job["url"], headers=headers,
                                       data=job["body"] if method == "POST" else None,
                                       timeout=aio.ClientTimeout(total=30)) as resp:
                body = await resp.text()
                latency = (time.time() - start) * 1000
                DB.execute("INSERT INTO runs (job_id, status_code, response, latency_ms, timestamp) VALUES (?,?,?,?,?)",
                          (job["id"], resp.status, body[:5000], round(latency), time.time()))
                DB.execute("UPDATE jobs SET last_run=?, run_count=run_count+1 WHERE id=?",
                          (time.time(), job["id"]))
                DB.commit()
                return {"status": "ok", "status_code": resp.status, "latency_ms": round(latency)}
    except Exception as e:
        DB.execute("INSERT INTO runs (job_id, status_code, error, timestamp) VALUES (?,?,?,?)",
                  (job["id"], 0, str(e)[:200], time.time()))
        DB.commit()
        return {"status": "error", "error": str(e)[:100]}

async def handle_create_job(req):
    body = await req.json()
    jid = hashlib.md5(f"{body.get('name','job')}{time.time()}".encode()).hexdigest()[:8]
    next_run = get_next_run(body.get("schedule_type", "delay"), body.get("schedule_value", "60"))
    DB.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (jid, body.get("name", "job"), body["url"], body.get("method", "POST"),
               json.dumps(body.get("headers", {})), body.get("body", ""),
               body.get("schedule_type", "delay"), str(body.get("schedule_value", "60")),
               next_run, None, 0, "active", time.time()))
    DB.commit()
    return web.json_response({"id": jid, "next_run": next_run, "status": "scheduled"})

async def handle_run_now(req):
    jid = req.query.get("id", "")
    job = DB.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
    if not job:
        return web.json_response({"error": "Job not found"}, status=404)
    result = await execute_job(dict(job))
    return web.json_response(result)

async def handle_jobs(req):
    rows = DB.execute("SELECT * FROM jobs ORDER BY next_run").fetchall()
    return web.json_response({"jobs": [dict(r) for r in rows]})

async def handle_delete_job(req):
    jid = req.query.get("id", "")
    DB.execute("UPDATE jobs SET status='deleted' WHERE id=?", (jid,))
    DB.commit()
    return web.json_response({"status": "deleted"})

async def handle_tick(req):
    """Process due jobs — call from cron every minute"""
    now = time.time()
    due = DB.execute("SELECT * FROM jobs WHERE status='active' AND next_run <= ?", (now,)).fetchall()
    results = []
    for job in due:
        result = await execute_job(dict(job))
        results.append({"job_id": job["id"], **result})
        # Reschedule if interval
        if job["schedule_type"] in ("interval", "cron"):
            try:
                interval = float(job["schedule_value"])
                DB.execute("UPDATE jobs SET next_run=? WHERE id=?", (now + interval, job["id"]))
            except:
                pass
        else:
            DB.execute("UPDATE jobs SET status='completed' WHERE id=?", (job["id"],))
    DB.commit()
    return web.json_response({"processed": len(results), "results": results})

async def handle_health(req):
    active = DB.execute("SELECT COUNT(*) as c FROM jobs WHERE status='active'").fetchone()["c"]
    total_runs = DB.execute("SELECT COUNT(*) as c FROM runs").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-chrono",
                             "active_jobs": active, "total_runs": total_runs, "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/jobs", handle_create_job)
app.router.add_get("/v1/jobs", handle_jobs)
app.router.add_delete("/v1/jobs", handle_delete_job)
app.router.add_post("/v1/run", handle_run_now)
app.router.add_post("/v1/tick", handle_tick)

if __name__ == "__main__":
    import os; os.makedirs("/home/openclaw/evez-ecosystem/chrono", exist_ok=True)
    print(f"⏰ EVEZ Chrono → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
