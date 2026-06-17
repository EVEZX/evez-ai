"""
EVEZ OpenClaw Mesh Telegram Bot Controller.
Commands:
  /status    - Show all node health
  /prompt <text> - Send a prompt to the mesh (broadcast)
  /alpha <text>  - Prompt only alpha node  
  /beta <text>   - Prompt only beta node
  /gossip        - Trigger gossip sync
  /memories      - Show memory count on all nodes
  /haiku         - Generate a haiku about the EVEZ mesh
"""
import asyncio, httpx, sys, os

TELEGRAM_TOKEN = "os.getenv("TELEGRAM_BOT_TOKEN", "")"
BRAIN_ALPHA = "http://127.0.0.1:8893"
BRAIN_BETA  = "http://127.0.0.1:8895"
PUBLIC_ALPHA = "https://integration-freeware-sku-bruce.trycloudflare.com"

NODES = {"alpha": BRAIN_ALPHA, "beta": BRAIN_BETA}

import json, time, logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger("evez-bot")

async def tg_send(client, chat_id, text):
    await client.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        timeout=10
    )

async def node_health(client, name, url):
    try:
        r = await client.get(f"{url}/health", timeout=5)
        d = r.json()
        return f"  ✅ {name}: {d['status']} | memories={d.get('memories', 0)}"
    except Exception as e:
        return f"  ❌ {name}: {str(e)[:50]}"

async def node_think(client, url, query):
    try:
        r = await client.post(f"{url}/think", params={"query": query}, timeout=20)
        d = r.json()
        return d.get("response", "No response"), True
    except Exception as e:
        return str(e)[:100], False

async def process_update(client, update):
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    user = msg.get("from", {}).get("first_name", "User")
    
    if not text.startswith("/"):
        return
    
    parts = text.split(" ", 1)
    cmd = parts[0].lower().rstrip("@evez_openclaw_bot")
    arg = parts[1] if len(parts) > 1 else ""
    
    log.info(f"Command: {cmd} from {user} ({chat_id})")
    
    if cmd == "/start":
        await tg_send(client, chat_id,
            "🦾 <b>EVEZ OpenClaw Mesh Controller</b>\n\n"
            "Nodes: alpha (Groq-1) + beta (Groq-2)\n"
            "Model: llama-3.3-70b-versatile\n\n"
            "Commands:\n"
            "/status — node health\n"
            "/prompt &lt;text&gt; — broadcast to mesh\n"
            "/alpha &lt;text&gt; — prompt alpha only\n"
            "/beta &lt;text&gt; — prompt beta only\n"
            "/gossip — sync memories\n"
            "/memories — memory counts\n"
            "/haiku — EVEZ haiku"
        )
    
    elif cmd == "/status":
        lines = ["🌐 <b>EVEZ Mesh Status</b>"]
        for name, url in NODES.items():
            lines.append(await node_health(client, name, url))
        await tg_send(client, chat_id, "\n".join(lines))
    
    elif cmd in ("/prompt", "/p"):
        query = arg or "What is the EVEZ mesh? Identify yourself."
        await tg_send(client, chat_id, f"📡 Broadcasting: <i>{query[:80]}</i>")
        
        for name, url in NODES.items():
            resp, ok = await node_think(client, url, query)
            icon = "✅" if ok else "❌"
            await tg_send(client, chat_id, f"{icon} <b>{name.upper()}</b>:\n{resp[:400]}")
    
    elif cmd == "/alpha":
        query = arg or "Identify yourself."
        resp, ok = await node_think(client, BRAIN_ALPHA, query)
        icon = "✅" if ok else "❌"
        await tg_send(client, chat_id, f"{icon} <b>ALPHA</b>:\n{resp[:500]}")
    
    elif cmd == "/beta":
        query = arg or "Identify yourself."
        resp, ok = await node_think(client, BRAIN_BETA, query)
        icon = "✅" if ok else "❌"
        await tg_send(client, chat_id, f"{icon} <b>BETA</b>:\n{resp[:500]}")
    
    elif cmd == "/gossip":
        try:
            r = await client.get(f"{BRAIN_ALPHA}/gossip", timeout=5)
            gossip = r.json()
            r2 = await client.post(f"{BRAIN_BETA}/gossip", json=gossip["memories"], timeout=5)
            d2 = r2.json()
            r3 = await client.get(f"{BRAIN_BETA}/gossip", timeout=5)
            gossip2 = r3.json()
            r4 = await client.post(f"{BRAIN_ALPHA}/gossip", json=gossip2["memories"], timeout=5)
            d4 = r4.json()
            await tg_send(client, chat_id,
                f"🔄 <b>Gossip Sync Complete</b>\n"
                f"  alpha→beta: {d2.get('merged', 0)} merged\n"
                f"  beta→alpha: {d4.get('merged', 0)} merged\n"
                f"  total memories: {max(d2.get('total_memories', 0), d4.get('total_memories', 0))}"
            )
        except Exception as e:
            await tg_send(client, chat_id, f"❌ Gossip failed: {e}")
    
    elif cmd == "/memories":
        lines = ["🧠 <b>Memory Counts</b>"]
        for name, url in NODES.items():
            try:
                r = await client.get(f"{url}/status", timeout=5)
                d = r.json()
                lines.append(f"  {name}: {d.get('memory_count', d.get('total_memories', '?'))} memories")
            except Exception as e:
                lines.append(f"  {name}: error - {e}")
        await tg_send(client, chat_id, "\n".join(lines))
    
    elif cmd == "/haiku":
        resp, ok = await node_think(client, BRAIN_ALPHA, "Generate a beautiful 3-line haiku about the EVEZ decentralized AI mesh network. Only output the haiku, nothing else.")
        icon = "🌸" if ok else "❌"
        await tg_send(client, chat_id, f"{icon} <b>EVEZ Haiku (by Alpha)</b>\n\n{resp[:300]}")
    
    else:
        await tg_send(client, chat_id, f"Unknown command: {cmd}\nTry /status or /prompt &lt;text&gt;")

async def run_bot():
    log.info("EVEZ Telegram Bot starting...")
    offset = 0
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Get bot info
        try:
            r = await client.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe", timeout=10)
            d = r.json()
            if d.get("ok"):
                bot = d["result"]
                log.info(f"Bot: @{bot.get('username', '?')} ({bot.get('id', '?')})")
                print(f"\n✅ EVEZ Telegram Bot ONLINE: @{bot.get('username', 'evez_bot')}")
                print(f"   Bot ID: {bot.get('id')}")
                print(f"   Start chatting: https://t.me/{bot.get('username', '')}")
        except Exception as e:
            log.error(f"Failed to get bot info: {e}")
        
        log.info("Polling for updates...")
        while True:
            try:
                r = await client.get(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
                    params={"offset": offset, "timeout": 20, "allowed_updates": ["message"]},
                    timeout=25
                )
                data = r.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        await process_update(client, update)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.warning(f"Poll error: {e}")
                await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(run_bot())
