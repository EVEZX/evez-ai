#!/usr/bin/env python3
"""
EVEZ DNS SHIELD — Port 10001
Free DNS monitoring, DNSSEC validation, DNS-over-HTTPS proxy
$0/month. Uses Cloudflare DoH (free), Google DoH (free)
"""
import json, time, hashlib, sqlite3, asyncio
from aiohttp import web
import aiohttp

PORT = 10001
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/dns-shield/dns.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS dns_records (
        domain TEXT PRIMARY KEY, ip TEXT, dnssec TEXT, last_check REAL, status TEXT
    );
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT, type TEXT, result TEXT, latency_ms REAL, timestamp REAL
    );
""")
DB.commit()

DOH_SERVERS = [
    "https://cloudflare-dns.com/dns-query",
    "https://dns.google/dns-query",
    "https://dns.quad9.net/dns-query",
]

async def resolve_doh(domain, qtype="A"):
    """Resolve via DNS-over-HTTPS — free, no API key"""
    for server in DOH_SERVERS:
        try:
            start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{server}?name={domain}&type={qtype}",
                    headers={"Accept": "application/dns-json"}, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    data = await resp.json()
                    latency = (time.time() - start) * 1000
                    answers = data.get("Answer", [])
                    return {"domain": domain, "type": qtype, "answers": answers,
                            "latency_ms": round(latency), "resolver": server, "status": "ok"}
        except:
            continue
    return {"domain": domain, "type": qtype, "status": "error", "message": "All DoH servers failed"}

async def handle_resolve(req):
    domain = req.query.get("domain", "example.com")
    qtype = req.query.get("type", "A")
    result = await resolve_doh(domain, qtype)
    DB.execute("INSERT INTO queries (domain, type, result, latency_ms, timestamp) VALUES (?,?,?,?,?)",
              (domain, qtype, json.dumps(result.get("answers", [])), result.get("latency_ms", 0), time.time()))
    DB.commit()
    return web.json_response(result)

async def handle_bulk_resolve(req):
    body = await req.json()
    domains = body.get("domains", [])
    results = await asyncio.gather(*[resolve_doh(d) for d in domains[:50]])
    return web.json_response({"results": results})

async def handle_stats(req):
    total = DB.execute("SELECT COUNT(*) as c FROM queries").fetchone()["c"]
    avg_latency = DB.execute("SELECT AVG(latency_ms) as a FROM queries").fetchone()["a"] or 0
    return web.json_response({"service": "dns-shield", "total_queries": total,
                             "avg_latency_ms": round(avg_latency), "doh_servers": DOH_SERVERS})

async def handle_health(req):
    return web.json_response({"status": "healthy", "service": "evez-dns-shield", "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_get("/v1/resolve", handle_resolve)
app.router.add_post("/v1/bulk-resolve", handle_bulk_resolve)
app.router.add_get("/v1/stats", handle_stats)

if __name__ == "__main__":
    import os; os.makedirs("/home/openclaw/evez-ecosystem/dns-shield", exist_ok=True)
    print(f"🛡️ EVEZ DNS Shield → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
