#!/usr/bin/env python3
"""
EVEZ AETHER — Port 10012
Real-time WebSocket message bus. Pub/sub channels, presence, history.
$0/month. In-memory with SQLite persistence.
"""
import json, time, hashlib, sqlite3, asyncio
from aiohttp import web
import aiohttp

PORT = 10012
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/aether/aether.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS channels (
        name TEXT PRIMARY KEY, created REAL, message_count INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT, sender TEXT,
        content TEXT, timestamp REAL
    );
""")
DB.commit()

# Active WebSocket connections: {channel: [ws, ...]}
CONNECTIONS = {}

async def handle_ws(req):
    """WebSocket endpoint for real-time messaging"""
    ws = web.WebSocketResponse()
    await ws.prepare(req)
    
    channel = req.query.get("channel", "general")
    sender = req.query.get("sender", "anonymous")
    
    if channel not in CONNECTIONS:
        CONNECTIONS[channel] = []
    CONNECTIONS[channel].append(ws)
    
    # Send history
    history = DB.execute("SELECT * FROM messages WHERE channel=? ORDER BY timestamp DESC LIMIT 50",
                        (channel,)).fetchall()
    for msg in reversed(history):
        await ws.send_json({"channel": msg["channel"], "sender": msg["sender"],
                            "content": msg["content"], "timestamp": msg["timestamp"]})
    
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                content = data.get("content", "")
                
                # Store message
                DB.execute("INSERT INTO messages (channel, sender, content, timestamp) VALUES (?,?,?,?)",
                          (channel, data.get("sender", sender), content, time.time()))
                DB.execute("UPDATE channels SET message_count=message_count+1 WHERE name=?", (channel,))
                DB.commit()
                
                # Broadcast to channel
                broadcast = json.dumps({"channel": channel, "sender": data.get("sender", sender),
                                       "content": content, "timestamp": time.time()})
                dead = []
                for i, conn in enumerate(CONNECTIONS.get(channel, [])):
                    try:
                        await conn.send_str(broadcast)
                    except:
                        dead.append(i)
                for i in reversed(dead):
                    CONNECTIONS[channel].pop(i)
                    
    except:
        pass
    finally:
        if channel in CONNECTIONS and ws in CONNECTIONS[channel]:
            CONNECTIONS[channel].remove(ws)
    
    return ws

async def handle_post_message(req):
    """REST API to post a message to a channel"""
    body = await req.json()
    channel = body.get("channel", "general")
    DB.execute("INSERT INTO messages (channel, sender, content, timestamp) VALUES (?,?,?,?)",
              (channel, body.get("sender", "api"), body["content"], time.time()))
    DB.execute("INSERT OR IGNORE INTO channels (name, created, message_count) VALUES (?,?,?)",
              (channel, time.time(), 0))
    DB.execute("UPDATE channels SET message_count=message_count+1 WHERE name=?", (channel,))
    DB.commit()
    
    # Broadcast to connected WebSockets
    broadcast = json.dumps({"channel": channel, "sender": body.get("sender", "api"),
                           "content": body["content"], "timestamp": time.time()})
    for conn in CONNECTIONS.get(channel, []):
        try:
            await conn.send_str(broadcast)
        except:
            pass
    
    return web.json_response({"status": "sent", "channel": channel})

async def handle_channels(req):
    rows = DB.execute("SELECT * FROM channels ORDER BY message_count DESC").fetchall()
    return web.json_response({"channels": [dict(r) for r in rows]})

async def handle_history(req):
    channel = req.query.get("channel", "general")
    limit = int(req.query.get("limit", "100"))
    rows = DB.execute("SELECT * FROM messages WHERE channel=? ORDER BY timestamp DESC LIMIT ?",
                      (channel, limit)).fetchall()
    return web.json_response({"messages": [dict(r) for r in reversed(rows)]})

async def handle_health(req):
    channels = DB.execute("SELECT COUNT(*) as c FROM channels").fetchone()["c"]
    messages = DB.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-aether",
                             "channels": channels, "messages": messages,
                             "active_connections": sum(len(c) for c in CONNECTIONS.values()), "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_get("/ws", handle_ws)
app.router.add_post("/v1/post", handle_post_message)
app.router.add_get("/v1/channels", handle_channels)
app.router.add_get("/v1/history", handle_history)

if __name__ == "__main__":
    import os; os.makedirs("/home/openclaw/evez-ecosystem/aether", exist_ok=True)
    print(f"📡 EVEZ Aether → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
