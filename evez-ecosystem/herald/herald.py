#!/usr/bin/env python3
"""
EVEZ Herald — Port 10017
Notification dispatch engine. Telegram, webhook, email templates.
Routes alerts to the right channel at the right time.
"""
import json, time, hashlib, sqlite3
from aiohttp import web, ClientSession, ClientTimeout

PORT = 10017
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/herald/herald.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS channels (
        name TEXT PRIMARY KEY, type TEXT, config TEXT,
        enabled INTEGER DEFAULT 1, last_sent REAL, created REAL
    );
    CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY, channel TEXT, subject TEXT, body TEXT,
        priority TEXT DEFAULT 'normal', status TEXT DEFAULT 'pending',
        sent_at REAL, created REAL
    );
    CREATE TABLE IF NOT EXISTS templates (
        name TEXT PRIMARY KEY, subject TEXT, body TEXT, channel TEXT, created REAL
    );
""")
DB.commit()

TELEGRAM_CHAT_ID = "7453631330"
TELEGRAM_BOT_TOKEN = ""  # Needs new token from Steven

async def send_telegram(text, session):
    """Send Telegram notification"""
    if not TELEGRAM_BOT_TOKEN:
        return {"status": "skipped", "reason": "No Telegram bot token"}
    try:
        async with session.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=ClientTimeout(total=10)
        ) as resp:
            return {"status": "ok" if resp.status == 200 else "error", "code": resp.status}
    except Exception as e:
        return {"status": "error", "error": str(e)[:50]}

async def send_webhook(url, payload, session):
    """Send webhook notification"""
    try:
        async with session.post(url, json=payload, timeout=ClientTimeout(total=10)) as resp:
            return {"status": "ok" if resp.status < 400 else "error", "code": resp.status}
    except Exception as e:
        return {"status": "error", "error": str(e)[:50]}

async def handle_notify(req):
    """Send a notification to a channel"""
    body = await req.json()
    channel = body.get("channel", "telegram")
    nid = hashlib.md5(f"{channel}{time.time()}".encode()).hexdigest()[:8]
    
    async with ClientSession() as session:
        if channel == "telegram":
            result = await send_telegram(body.get("body", ""), session)
        elif channel == "webhook":
            result = await send_webhook(body.get("url", ""), body.get("payload", {}), session)
        elif channel == "log":
            result = {"status": "logged"}
        else:
            result = {"status": "unknown_channel"}
    
    DB.execute("INSERT INTO notifications VALUES (?,?,?,?,?,?,?,?)",
              (nid, channel, body.get("subject",""), body.get("body",""),
               body.get("priority","normal"), result.get("status","pending"),
               time.time(), time.time()))
    DB.commit()
    
    return web.json_response({"id": nid, "channel": channel, **result})

async def handle_register_channel(req):
    body = await req.json()
    DB.execute("INSERT OR REPLACE INTO channels VALUES (?,?,?,?,?,?)",
              (body["name"], body.get("type","webhook"), json.dumps(body.get("config",{})),
               1, None, time.time()))
    DB.commit()
    return web.json_response({"name": body["name"], "status": "registered"})

async def handle_channels(req):
    rows = DB.execute("SELECT name, type, enabled, last_sent FROM channels").fetchall()
    return web.json_response({"channels": [dict(r) for r in rows]})

async def handle_history(req):
    rows = DB.execute("SELECT * FROM notifications ORDER BY created DESC LIMIT 50").fetchall()
    return web.json_response({"notifications": [dict(r) for r in rows]})

async def handle_templates(req):
    if req.method == "POST":
        body = await req.json()
        DB.execute("INSERT OR REPLACE INTO templates VALUES (?,?,?,?,?)",
                  (body["name"], body.get("subject",""), body.get("body",""),
                   body.get("channel","telegram"), time.time()))
        DB.commit()
        return web.json_response({"name": body["name"], "status": "saved"})
    rows = DB.execute("SELECT * FROM templates").fetchall()
    return web.json_response({"templates": [dict(r) for r in rows]})

async def handle_health(req):
    channels = DB.execute("SELECT COUNT(*) as c FROM channels").fetchone()["c"]
    sent = DB.execute("SELECT COUNT(*) as c FROM notifications WHERE status='ok'").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-herald",
                             "channels": channels, "notifications_sent": sent, "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/notify", handle_notify)
app.router.add_post("/v1/channels", handle_register_channel)
app.router.add_get("/v1/channels", handle_channels)
app.router.add_get("/v1/history", handle_history)
app.router.add_post("/v1/templates", handle_templates)
app.router.add_get("/v1/templates", handle_templates)

if __name__ == "__main__":
    print(f"📯 EVEZ Herald → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
