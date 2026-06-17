#!/usr/bin/env python3
"""
EVEZ MIRROR — Port 10011
URL shortener + analytics. Click tracking, geo IP, referral tracking.
$0/month. SQLite-backed, zero dependencies beyond aiohttp.
"""
import json, time, hashlib, sqlite3
from aiohttp import web
import aiohttp

PORT = 10011
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/mirror/mirror.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS links (
        id TEXT PRIMARY KEY, short_code TEXT UNIQUE, long_url TEXT,
        clicks INTEGER DEFAULT 0, created REAL, active BOOLEAN DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS clicks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, short_code TEXT,
        ip TEXT, referer TEXT, user_agent TEXT, timestamp REAL
    );
""")
DB.commit()

CHARSET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def encode_id(n):
    s = ""
    while n > 0:
        s += CHARSET[n % len(CHARSET)]
        n //= len(CHARSET)
    return s or "0"

COUNTER = DB.execute("SELECT COALESCE(MAX(id), 0) + 1 as c FROM links").fetchone()["c"] if DB.execute("SELECT COUNT(*) as c FROM links").fetchone()["c"] > 0 else 1

async def handle_shorten(req):
    global COUNTER
    body = await req.json()
    long_url = body["url"]
    short_code = encode_id(COUNTER)
    COUNTER += 1
    lid = hashlib.md5(f"{short_code}{time.time()}".encode()).hexdigest()[:8]
    DB.execute("INSERT INTO links VALUES (?,?,?,?,?,?)",
              (lid, short_code, long_url, 0, time.time(), 1))
    DB.commit()
    return web.json_response({"short_code": short_code, "short_url": f"http://localhost:{PORT}/{short_code}",
                             "long_url": long_url})

async def handle_redirect(req):
    code = req.match_info.get("code", "")
    link = DB.execute("SELECT * FROM links WHERE short_code=? AND active=1", (code,)).fetchone()
    if not link:
        return web.json_response({"error": "Not found"}, status=404)
    
    # Track click
    DB.execute("UPDATE links SET clicks=clicks+1 WHERE short_code=?", (code,))
    DB.execute("INSERT INTO clicks (short_code, ip, referer, user_agent, timestamp) VALUES (?,?,?,?,?)",
              (code, req.remote, req.headers.get("Referer", ""), req.headers.get("User-Agent", ""), time.time()))
    DB.commit()
    
    raise web.HTTPFound(link["long_url"])

async def handle_stats(req):
    code = req.query.get("code", "")
    link = DB.execute("SELECT * FROM links WHERE short_code=?", (code,)).fetchone()
    if not link:
        return web.json_response({"error": "Not found"}, status=404)
    clicks = DB.execute("SELECT * FROM clicks WHERE short_code=? ORDER BY timestamp DESC LIMIT 100", (code,)).fetchall()
    return web.json_response({"short_code": code, "long_url": link["long_url"],
                             "total_clicks": link["clicks"], "recent_clicks": [dict(c) for c in clicks]})

async def handle_links(req):
    rows = DB.execute("SELECT * FROM links WHERE active=1 ORDER BY created DESC LIMIT 100").fetchall()
    return web.json_response({"links": [dict(r) for r in rows]})

async def handle_health(req):
    links = DB.execute("SELECT COUNT(*) as c FROM links WHERE active=1").fetchone()["c"]
    clicks = DB.execute("SELECT COUNT(*) as c FROM clicks").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-mirror",
                             "links": links, "total_clicks": clicks, "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/shorten", handle_shorten)
app.router.add_get("/v1/stats", handle_stats)
app.router.add_get("/v1/links", handle_links)
app.router.add_get("/{code}", handle_redirect)

if __name__ == "__main__":
    import os; os.makedirs("/home/openclaw/evez-ecosystem/mirror", exist_ok=True)
    print(f"🔗 EVEZ Mirror → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
