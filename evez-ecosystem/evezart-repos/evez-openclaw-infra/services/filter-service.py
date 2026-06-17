#!/usr/bin/env python3
"""
Filter — Personal AI Assistant (The lobster way 🦞)
Lightweight, self-hosted, works everywhere.
Integrates with EVEZ Provider for LLM, ClawBreak for tools.
"""
import os, json, time, asyncio
from aiohttp import web, ClientSession

EVEZ_PROVIDER = os.getenv("EVEZ_PROVIDER_URL", "http://localhost:9100/v1")
FILTER_PORT = int(os.getenv("FILTER_PORT", "9300"))

async def handle_chat(req):
    body = await req.json()
    message = body.get("message", "")
    history = body.get("history", [])

    messages = [
        {"role": "system", "content": "You are Filter, a personal AI assistant. You are direct, helpful, and have personality. The lobster way. You help with anything — coding, research, planning, life. Be concise but thorough."}
    ] + history + [{"role": "user", "content": message}]

    async with ClientSession() as session:
        async with session.post(
            f"{EVEZ_PROVIDER}/chat/completions",
            json={"model": "evez-smart", "messages": messages, "max_tokens": 2048},
            headers={"Content-Type": "application/json"}
        ) as r:
            result = await r.json()
            reply = ""
            if result.get("choices"):
                reply = result["choices"][0].get("message", {}).get("content", "")
            return web.json_response({"reply": reply, "model": "evez-smart"})

async def handle_health(req):
    return web.json_response({"status": "healthy", "service": "filter", "version": "1.0.0"})

app = web.Application()
app.router.add_post("/chat", handle_chat)
app.router.add_get("/health", handle_health)

if __name__ == "__main__":
    print(f"🦞 Filter starting on port {FILTER_PORT}")
    web.run_app(app, host="0.0.0.0", port=FILTER_PORT)
