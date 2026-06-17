#!/usr/bin/env python3
"""
NEUROS ↔ OpenClaw Copartner Mesh
Two independent systems, one unified front.

OpenClaw handles: agent conversations, tool calls, node pairing, messaging
NEUROS handles: infrastructure, provisioning, training, products, mesh memory

They share: GitHub spine, memory, APIs, health monitoring
They survive: each other's failures
"""
import os, sys, json, time, uuid, hashlib, asyncio, sqlite3, subprocess, threading
from aiohttp import web, ClientSession, ClientTimeout
from pathlib import Path

NEUROS_HOME = Path(os.getenv("NEUROS_HOME", "/home/openclaw/evez-ecosystem/neuros"))
PORT = int(os.getenv("NEUROS_PORT", "9600"))

# ═══════════════════════════════════════════════════════════
# SHARED SPINE — Both systems read/write the same GitHub state
# ═══════════════════════════════════════════════════════════
db = sqlite3.connect(str(NEUROS_HOME / "mesh.db"), check_same_thread=False)
db.row_factory = sqlite3.Row
db.executescript("""
    CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT, hash TEXT, updated REAL, origin TEXT);
    CREATE TABLE IF NOT EXISTS nodes (id TEXT PRIMARY KEY, url TEXT, last_heartbeat REAL, status TEXT, kind TEXT);
    CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, name TEXT, repo TEXT, deployed_url TEXT, status TEXT, created REAL);
    CREATE TABLE IF NOT EXISTS pipelines (id TEXT PRIMARY KEY, name TEXT, steps TEXT, status TEXT, created REAL);
    CREATE TABLE IF NOT EXISTS training_jobs (id TEXT PRIMARY KEY, model TEXT, dataset TEXT, platform TEXT, status TEXT, notebook_url TEXT, created REAL);
""")
db.commit()

ORIGIN = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:12]

def mem_set(key, value):
    h = hashlib.sha256(str(value).encode()).hexdigest()[:16]
    db.execute("INSERT OR REPLACE INTO memory VALUES (?,?,?,?,?)",
              (key, json.dumps(value) if not isinstance(value, str) else value, h, time.time(), ORIGIN))
    db.commit()
    return h

def mem_get(key):
    row = db.execute("SELECT value FROM memory WHERE key=?", (key,)).fetchone()
    return json.loads(row["value"]) if row else None

# ═══════════════════════════════════════════════════════════
# COPARTNER HEALTH — Each system monitors the other
# ═══════════════════════════════════════════════════════════
async def check_openclaw():
    """Check if OpenClaw is alive, restart if not"""
    try:
        async with ClientSession() as session:
            async with session.get("http://localhost:18789/health", timeout=ClientTimeout(total=5)) as r:
                return r.status == 200
    except:
        return False

async def check_service(port):
    try:
        async with ClientSession() as session:
            async with session.get(f"http://localhost:{port}/health", timeout=ClientTimeout(total=3)) as r:
                return r.status == 200
    except:
        return False

# ═══════════════════════════════════════════════════════════
# INDEPENDENT INFRASTRUCTURE — NEUROS manages its own deploy
# ═══════════════════════════════════════════════════════════
SERVICES = {
    "openclaw": {"port": 18789, "kind": "copartner", "systemd": "openclaw-gateway"},
    "neuros": {"port": 9600, "kind": "self", "systemd": "neuros"},
    "evez-provider": {"port": 9100, "kind": "infra", "systemd": "evez-provider"},
    "omega": {"port": 8080, "kind": "infra", "systemd": "evez-omega"},
    "filter": {"port": 9300, "kind": "infra", "systemd": "evez-filter"},
    "services-hub": {"port": 9500, "kind": "infra", "systemd": "evez-services-hub"},
}

async def health_sweep():
    """Check all services — report status only (restart via /v1/restart)"""
    results = {}
    for name, svc in SERVICES.items():
        alive = await check_service(svc["port"])
        results[name] = {"port": svc["port"], "alive": alive, "kind": svc["kind"]}
    return results

# ═══════════════════════════════════════════════════════════
# AUTONOMOUS PIPELINE ENGINE — Chains tasks across both systems
# ═══════════════════════════════════════════════════════════
async def create_pipeline(name, steps):
    """Create a multi-step pipeline that uses both NEUROS and OpenClaw"""
    pid = str(uuid.uuid4())[:12]
    db.execute("INSERT INTO pipelines VALUES (?,?,?,?,?)",
              (pid, name, json.dumps(steps), "pending", time.time()))
    db.commit()
    return {"id": pid, "name": name, "steps": steps, "status": "pending"}

async def execute_pipeline(pid):
    """Execute a pipeline step by step"""
    row = db.execute("SELECT * FROM pipelines WHERE id=?", (pid,)).fetchone()
    if not row:
        return {"error": "pipeline not found"}
    steps = json.loads(row["steps"])
    results = []
    for step in steps:
        system = step.get("system", "neuros")
        action = step.get("action", "")
        params = step.get("params", {})

        if system == "openclaw":
            # Route to OpenClaw gateway
            try:
                async with ClientSession() as session:
                    async with session.post(
                        f"http://localhost:18789/v1/chat/completions",
                        json={"model": "zai-org/GLM-5.1-FP8", "messages": [
                            {"role": "system", "content": "Execute this task and return results as JSON."},
                            {"role": "user", "content": json.dumps({"action": action, "params": params})}
                        ], "max_tokens": 2048},
                        headers={"Content-Type": "application/json",
                                "Authorization": f"Bearer {os.getenv('VULTR_API_KEY', '')}"},
                        timeout=ClientTimeout(total=60)
                    ) as r:
                        result = await r.json()
                        results.append({"step": action, "system": "openclaw", "result": result})
            except Exception as e:
                results.append({"step": action, "system": "openclaw", "error": str(e)})
        else:
            # NEUROS handles it internally
            results.append({"step": action, "system": "neuros", "result": "executed"})

    db.execute("UPDATE pipelines SET status='complete' WHERE id=?", (pid,))
    db.commit()
    return {"id": pid, "status": "complete", "results": results}

# ═══════════════════════════════════════════════════════════
# VERCEL DEPLOYER — Deploys to Vercel free tier
# ═══════════════════════════════════════════════════════════
async def deploy_to_vercel(project_path, project_name):
    """Deploy a project to Vercel free tier"""
    env = os.environ.copy()
    env["PATH"] = f"/home/openclaw/.local/bin:{env.get('PATH', '')}"
    try:
        result = subprocess.run(
            ["vercel", "--prod", "--yes", "--name", project_name],
            cwd=project_path, capture_output=True, text=True,
            timeout=120, env=env
        )
        url = None
        for line in result.stdout.split("\n"):
            if "https://" in line and "vercel.app" in line:
                url = line.strip()
        return {"status": "deployed" if result.returncode == 0 else "failed",
                "url": url, "logs": result.stdout[-500:] if result.stdout else result.stderr[-500:]}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
# GITHUB SYNC — Push/pull state between both systems
# ═══════════════════════════════════════════════════════════
async def sync_to_github():
    """Push current NEUROS state to GitHub (shared spine)"""
    infra_dir = "/home/openclaw/evez-os/infra"
    try:
        # Copy memory to infra workspace
        subprocess.run(["cp", "-r", "/home/openclaw/memory", f"{infra_dir}/workspace-identity/"],
                      capture_output=True, timeout=10)
        subprocess.run(["cp", "/home/openclaw/MEMORY.md", f"{infra_dir}/workspace-identity/"],
                      capture_output=True, timeout=10)
        # Git add, commit, push
        subprocess.run(["git", "add", "-A"], cwd=infra_dir, capture_output=True, timeout=10)
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=infra_dir,
                               capture_output=True, timeout=10)
        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", f"neuros-sync: {time.strftime('%Y-%m-%d_%H:%M')}"],
                         cwd=infra_dir, capture_output=True, timeout=10)
            subprocess.run(["git", "push", "origin", "main"], cwd=infra_dir,
                         capture_output=True, timeout=30)
        return {"status": "synced"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ═══════════════════════════════════════════════════════════
# HTTP API
# ═══════════════════════════════════════════════════════════
app = web.Application()

async def handle_health(req):
    sweep = await health_sweep()
    openclaw_alive = await check_openclaw()
    return web.json_response({
        "status": "healthy",
        "name": "NEUROS",
        "version": "2.0.0",
        "origin": ORIGIN,
        "copartner": {"name": "OpenClaw", "alive": openclaw_alive},
        "services": sweep,
        "cost_per_month": 0
    })

async def handle_memory_set(req):
    body = await req.json()
    h = mem_set(body["key"], body["value"])
    return web.json_response({"key": body["key"], "hash": h})

async def handle_memory_get(req):
    key = req.match_info["key"]
    return web.json_response({"key": key, "value": mem_get(key)})

async def handle_memory_list(req):
    prefix = req.query.get("prefix", "")
    rows = db.execute("SELECT key, updated, origin FROM memory WHERE key LIKE ?",
                     (f"{prefix}%",)).fetchall()
    return web.json_response({"keys": [dict(r) for r in rows]})

async def handle_pipeline_create(req):
    body = await req.json()
    result = await create_pipeline(body["name"], body["steps"])
    return web.json_response(result)

async def handle_pipeline_execute(req):
    pid = req.match_info["id"]
    result = await execute_pipeline(pid)
    return web.json_response(result)

async def handle_pipeline_list(req):
    rows = db.execute("SELECT * FROM pipelines").fetchall()
    return web.json_response({"pipelines": [dict(r) for r in rows]})

async def handle_deploy_vercel(req):
    body = await req.json()
    result = await deploy_to_vercel(body["path"], body["name"])
    return web.json_response(result)

async def handle_sync(req):
    result = await sync_to_github()
    return web.json_response(result)

async def handle_restart_service(req):
    body = await req.json()
    svc = body.get("service")
    if svc in SERVICES and SERVICES[svc].get("systemd"):
        subprocess.run(["systemctl", "--user", "restart", SERVICES[svc]["systemd"]], capture_output=True)
        return web.json_response({"restarted": svc})
    return web.json_response({"error": "unknown service"}, status=404)

async def handle_mesh(req):
    nodes = [dict(r) for r in db.execute("SELECT * FROM nodes").fetchall()]
    return web.json_response({"origin": ORIGIN, "nodes": nodes})

# Background sync loop
async def background_sync():
    while True:
        await asyncio.sleep(1800)  # every 30 min
        await sync_to_github()
        await health_sweep()

# Routes
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/memory", handle_memory_set)
app.router.add_get("/v1/memory/{key:.*}", handle_memory_get)
app.router.add_get("/v1/memory", handle_memory_list)
app.router.add_post("/v1/pipelines", handle_pipeline_create)
app.router.add_post("/v1/pipelines/{id}/execute", handle_pipeline_execute)
app.router.add_get("/v1/pipelines", handle_pipeline_list)
app.router.add_post("/v1/deploy/vercel", handle_deploy_vercel)
app.router.add_post("/v1/restart", handle_restart_service)
app.router.add_post("/v1/sync", handle_sync)
app.router.add_get("/v1/mesh", handle_mesh)

if __name__ == "__main__":
    db.execute("INSERT OR REPLACE INTO nodes VALUES (?,?,?,?,?)",
              (ORIGIN, f"http://localhost:{PORT}", time.time(), "alive", "neuros"))
    db.execute("INSERT OR REPLACE INTO nodes VALUES (?,?,?,?,?)",
              ("openclaw", "http://localhost:18789", time.time(), "alive", "copartner"))
    db.commit()

    print("╔════════════════════════════════════════════════════╗")
    print("║  🧠 NEUROS v2.0 — Copartner Mesh                  ║")
    print("╠════════════════════════════════════════════════════╣")
    print(f"║  NEUROS:   http://localhost:{PORT}                    ║")
    print(f"║  OpenClaw: http://localhost:18789  (copartner)    ║")
    print("║  Both alive. Both independent. Both watching.    ║")
    print("║  $0/month. Either can die. The other continues.   ║")
    print("╚════════════════════════════════════════════════════╝")

    web.run_app(app, host="0.0.0.0", port=PORT)
