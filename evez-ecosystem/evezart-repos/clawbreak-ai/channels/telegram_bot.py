"""Standalone Telegram bot for ClawBreak.
Run: python3 channels/telegram_bot.py
"""
import os
import sys
import json
import httpx
import asyncio

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import Config
from memory import Memory
from llm import LLMClient
from mcp import BuiltInTools

config = Config()
memory = Memory(config.get("memory", "db_path"))
llm = LLMClient(config)
builtin = BuiltInTools(config)

TELEGRAM_TOKEN = config.data.get("channels", {}).get("telegram", {}).get("token", "")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

async def send_message(chat_id, text):
    async with httpx.AsyncClient(timeout=10) as client:
        # Split long messages
        for i in range(0, len(text), 4096):
            await client.post(f"{BASE_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": text[i:i+4096],
                "parse_mode": "Markdown",
            })

async def process_telegram():
    offset = 0
    sessions = {}
    
    print(f"Telegram bot starting... (token: {TELEGRAM_TOKEN[:10]}...)")
    
    while True:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(f"{BASE_URL}/getUpdates", json={
                    "offset": offset,
                    "timeout": 25,
                    "allowed_updates": ["message"],
                })
                data = resp.json()
            
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "")
                
                if not text:
                    continue
                
                if text == "/start":
                    await send_message(chat_id, "⚡ *ClawBreak* is online. Send me anything.")
                    continue
                
                if text == "/status":
                    health = {"model": config.get("llm", "model"), "providers": len(llm.providers)}
                    await send_message(chat_id, f"⚡ *ClawBreak Status*\nModel: {health['model']}\nProviders: {health['providers']}")
                    continue
                
                # Process through AI
                session_id = sessions.get(chat_id, f"tg_{chat_id}")
                sessions[chat_id] = session_id
                
                # Build messages
                history = memory.get_messages(session_id, limit=10)
                messages = [{"role": "system", "content": config.get("system_prompt")}]
                messages.extend(history)
                messages.append({"role": "user", "content": text})
                
                result = await llm.chat(messages)
                
                if "error" in result:
                    await send_message(chat_id, f"❌ Error: {result['error'][:200]}")
                else:
                    try:
                        reply = result["choices"][0]["message"]["content"]
                        memory.store_message("user", text, session_id)
                        memory.store_message("assistant", reply, session_id)
                        await send_message(chat_id, reply[:4096])
                    except Exception as e:
                        await send_message(chat_id, f"❌ Parse error: {e}")
        
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        print("Set channels.telegram.token in config.yaml")
        print("Get a token from @BotFather on Telegram")
        sys.exit(1)
    asyncio.run(process_telegram())
