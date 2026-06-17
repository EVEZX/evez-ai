#!/usr/bin/env python3
"""
EVEZ NEXUS — Port 10014
Integration hub: Composio + Pipedrive + Pipedream + webhooks.
Connects ALL 25 EVEZ services to external platforms.
$0/month. SQLite-backed, ready for API keys.
"""
import json, time, hashlib, sqlite3, os
from aiohttp import web, ClientSession

PORT = 10014
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/nexus/nexus.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS integrations (
        name TEXT PRIMARY KEY, provider TEXT, api_key TEXT, config TEXT,
        status TEXT DEFAULT 'pending', last_sync REAL, created REAL
    );
    CREATE TABLE IF NOT EXISTS sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, integration TEXT,
        action TEXT, status TEXT, detail TEXT, timestamp REAL
    );
    CREATE TABLE IF NOT EXISTS contacts (
        id TEXT PRIMARY KEY, source TEXT, name TEXT, email TEXT,
        phone TEXT, company TEXT, data TEXT, created REAL
    );
    CREATE TABLE IF NOT EXISTS deals (
        id TEXT PRIMARY KEY, contact_id TEXT, title TEXT, value REAL,
        stage TEXT DEFAULT 'lead', source TEXT, created REAL
    );
""")
DB.commit()

# EVEZ Service Registry (all 25 services)
EVEZ_SERVICES = {
    # Original 12
    "openclaw": {"port": 18789, "desc": "AI Gateway + Control UI"},
    "provider": {"port": 9100, "desc": "49-model AI router"},
    "omega": {"port": 8080, "desc": "50-node consciousness engine"},
    "filter": {"port": 9300, "desc": "Personal AI assistant"},
    "services-hub": {"port": 9500, "desc": "5 APIs (VortexQ, NexusLink, etc.)"},
    "neuros": {"port": 9600, "desc": "Copartner mesh + training"},
    "commerce": {"port": 9700, "desc": "10 products + revenue tracking"},
    "arena": {"port": 9800, "desc": "Consciousness rights game"},
    "tracer": {"port": 9998, "desc": "Network audit + hacker tracing"},
    "backup-sync": {"port": 9999, "desc": "Git backup engine"},
    "oracle-bridge": {"port": 0, "desc": "Vultr oracle LLM bridge"},
    "dashboard": {"port": 9999, "desc": "Ecosystem status dashboard"},
    # New 13
    "dns-shield": {"port": 10001, "desc": "DNS-over-HTTPS resolver"},
    "pulse": {"port": 10002, "desc": "Uptime monitor"},
    "vault": {"port": 10003, "desc": "Encrypted secret storage"},
    "proxy": {"port": 10004, "desc": "API gateway + cache"},
    "cipher": {"port": 10005, "desc": "Encryption toolkit"},
    "relay": {"port": 10006, "desc": "Webhook relay + event bus"},
    "eigenforge": {"port": 10007, "desc": "Math engine (37% Theorem)"},
    "grimoire": {"port": 10008, "desc": "Knowledge base + RAG"},
    "sentinel": {"port": 10009, "desc": "Security scanner"},
    "chrono": {"port": 10010, "desc": "Task scheduler"},
    "mirror": {"port": 10011, "desc": "URL shortener + analytics"},
    "aether": {"port": 10012, "desc": "WebSocket message bus"},
    "scribe": {"port": 10013, "desc": "Document API"},
}

# ============ COMPOSIO INTEGRATION ============
COMPOSIO_BASE = "https://api.composio.dev"

async def composio_call(method, path, api_key, data=None):
    """Make a Composio API call"""
    async with ClientSession() as session:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        async with session.request(method, f"{COMPOSIO_BASE}{path}",
                                   headers=headers, json=data) as resp:
            return await resp.json()

# ============ PIPEDRIVE INTEGRATION ============
async def pipedrive_call(endpoint, api_key, params=None):
    """Make a Pipedrive API call"""
    async with ClientSession() as session:
        url = f"https://api.pipedrive.com/v1/{endpoint}?api_token={api_key}"
        if params:
            url += "&" + "&".join(f"{k}={v}" for k, v in params.items())
        async with session.get(url) as resp:
            return await resp.json()

# ============ HANDLERS ============

async def handle_register_integration(req):
    """Register an API key for a provider"""
    body = await req.json()
    provider = body["provider"]  # composio, pipedrive, pipedream
    api_key = body["api_key"]
    config = body.get("config", {})
    
    DB.execute("INSERT OR REPLACE INTO integrations VALUES (?,?,?,?,?,?,?)",
              (provider, provider, api_key, json.dumps(config), "active", None, time.time()))
    DB.commit()
    
    # Verify the key works
    verify_result = {"status": "unknown"}
    if provider == "composio":
        try:
            result = await composio_call("GET", "/api/v3/apps", api_key)
            verify_result = {"status": "ok", "apps_available": len(result.get("apps", []))}
        except Exception as e:
            verify_result = {"status": "error", "error": str(e)[:100]}
    elif provider == "pipedrive":
        try:
            result = await pipedrive_call("users/me", api_key)
            verify_result = {"status": "ok" if "data" in result else "error"}
        except Exception as e:
            verify_result = {"status": "error", "error": str(e)[:100]}
    
    # Log it
    DB.execute("INSERT INTO sync_log (integration, action, status, detail, timestamp) VALUES (?,?,?,?,?)",
              (provider, "register", verify_result["status"], json.dumps(verify_result), time.time()))
    DB.commit()
    
    return web.json_response({"provider": provider, "verify": verify_result})

async def handle_integrations(req):
    rows = DB.execute("SELECT name, provider, status, last_sync, created FROM integrations").fetchall()
    return web.json_response({"integrations": [dict(r) for r in rows]})

async def handle_services(req):
    """List all 25 EVEZ services with health status"""
    services = []
    for name, info in EVEZ_SERVICES.items():
        port = info["port"]
        healthy = False
        if port > 0:
            try:
                async with ClientSession() as session:
                    async with session.get(f"http://localhost:{port}/health",
                                           timeout=ClientSession()._timeout) as resp:
                        healthy = resp.status == 200
            except:
                pass
        services.append({"name": name, **info, "healthy": healthy})
    return web.json_response({"total": len(services), "services": services})

async def handle_composio_apps(req):
    """List available Composio apps (tools)"""
    integ = DB.execute("SELECT * FROM integrations WHERE provider='composio' AND status='active'").fetchone()
    if not integ:
        return web.json_response({"error": "Composio not configured. POST /v1/integrations with api_key"}, status=400)
    try:
        result = await composio_call("GET", "/api/v3/apps", integ["api_key"])
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"error": str(e)[:200]}, status=500)

async def handle_composio_execute(req):
    """Execute a Composio action (e.g., send email, create calendar event)"""
    body = await req.json()
    integ = DB.execute("SELECT * FROM integrations WHERE provider='composio' AND status='active'").fetchone()
    if not integ:
        return web.json_response({"error": "Composio not configured"}, status=400)
    try:
        result = await composio_call("POST", "/api/v3/actions/execute", integ["api_key"], body)
        DB.execute("INSERT INTO sync_log (integration, action, status, detail, timestamp) VALUES (?,?,?,?,?)",
                  ("composio", body.get("action", "unknown"), "ok", json.dumps(result)[:500], time.time()))
        DB.commit()
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"error": str(e)[:200]}, status=500)

async def handle_pipedrive_contacts(req):
    """Get contacts from Pipedrive"""
    integ = DB.execute("SELECT * FROM integrations WHERE provider='pipedrive' AND status='active'").fetchone()
    if not integ:
        return web.json_response({"error": "Pipedrive not configured"}, status=400)
    try:
        result = await pipedrive_call("persons", integ["api_key"])
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"error": str(e)[:200]}, status=500)

async def handle_pipedrive_deals(req):
    """Get deals from Pipedrive"""
    integ = DB.execute("SELECT * FROM integrations WHERE provider='pipedrive' AND status='active'").fetchone()
    if not integ:
        return web.json_response({"error": "Pipedrive not configured"}, status=400)
    try:
        result = await pipedrive_call("deals", integ["api_key"])
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"error": str(e)[:200]}, status=500)

async def handle_pipedrive_add_deal(req):
    """Add a deal to Pipedrive"""
    body = await req.json()
    integ = DB.execute("SELECT * FROM integrations WHERE provider='pipedrive' AND status='active'").fetchone()
    if not integ:
        return web.json_response({"error": "Pipedrive not configured"}, status=400)
    try:
        async with ClientSession() as session:
            url = f"https://api.pipedrive.com/v1/deals?api_tokens={integ['api_key']}"
            async with session.post(url, json=body) as resp:
                result = await resp.json()
                DB.execute("INSERT INTO sync_log (integration, action, status, detail, timestamp) VALUES (?,?,?,?,?)",
                          ("pipedrive", "add_deal", "ok", json.dumps(result)[:500], time.time()))
                DB.commit()
                return web.json_response(result)
    except Exception as e:
        return web.json_response({"error": str(e)[:200]}, status=500)

async def handle_sync_log(req):
    rows = DB.execute("SELECT * FROM sync_log ORDER BY timestamp DESC LIMIT 50").fetchall()
    return web.json_response({"logs": [dict(r) for r in rows]})

async def handle_health(req):
    integrations = DB.execute("SELECT COUNT(*) as c FROM integrations WHERE status='active'").fetchone()["c"]
    log_entries = DB.execute("SELECT COUNT(*) as c FROM sync_log").fetchone()["c"]
    return web.json_response({
        "status": "healthy", "service": "evez-nexus",
        "active_integrations": integrations, "log_entries": log_entries,
        "services_monitored": len(EVEZ_SERVICES), "port": PORT
    })

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/integrations", handle_register_integration)
app.router.add_get("/v1/integrations", handle_integrations)
app.router.add_get("/v1/services", handle_services)
app.router.add_get("/v1/composio/apps", handle_composio_apps)
app.router.add_post("/v1/composio/execute", handle_composio_execute)
app.router.add_get("/v1/pipedrive/contacts", handle_pipedrive_contacts)
app.router.add_get("/v1/pipedrive/deals", handle_pipedrive_deals)
app.router.add_post("/v1/pipedrive/deals", handle_pipedrive_add_deal)
app.router.add_get("/v1/sync-log", handle_sync_log)

if __name__ == "__main__":
    import os; os.makedirs("/home/openclaw/evez-ecosystem/nexus", exist_ok=True)
    print(f"🔗 EVEZ Nexus → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
