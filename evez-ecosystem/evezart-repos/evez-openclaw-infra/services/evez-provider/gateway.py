#!/usr/bin/env python3
"""
EVEZ Provider Gateway — Turn your Vultr inference into a hosted AI API
OpenAI-compatible API that routes to Vultr inference backend
Serves: GLM-5.1, DeepSeek-V3.2, MiniMax-M2.5, Kimi-K2.5
"""
import os, json, time, uuid, asyncio, hashlib
from aiohttp import web
import aiohttp

# Config from environment
VULTR_API_KEY = os.getenv("VULTR_API_KEY", "")
VULTR_BASE_URL = "https://api.vultrinference.com/v1"
PROVIDER_PORT = int(os.getenv("PROVIDER_PORT", "9100"))
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "60"))

# Model catalog
MODELS = [
    {"id": "evez-smart", "name": "EVEZ Smart", "backend": "zai-org/GLM-5.1-FP8",
     "context_window": 202752, "pricing": {"prompt": 0, "completion": 0}},
    {"id": "evez-code", "name": "EVEZ Code", "backend": "nvidia/DeepSeek-V3.2-NVFP4",
     "context_window": 128000, "pricing": {"prompt": 0, "completion": 0}},
    {"id": "evez-fast", "name": "EVEZ Fast", "backend": "MiniMaxAI/MiniMax-M2.5",
     "context_window": 128000, "pricing": {"prompt": 0, "completion": 0}},
    {"id": "evez-vision", "name": "EVEZ Vision", "backend": "moonshotai/Kimi-K2.5",
     "context_window": 128000, "pricing": {"prompt": 0, "completion": 0}},
]

MODEL_MAP = {m["id"]: m for m in MODELS}

# Simple API key store (in production, use a database)
API_KEYS = {}

# Rate limiting
rate_limits = {}

def check_rate_limit(api_key):
    now = time.time()
    if api_key not in rate_limits:
        rate_limits[api_key] = []
    rate_limits[api_key] = [t for t in rate_limits[api_key] if now - t < 60]
    if len(rate_limits[api_key]) >= RATE_LIMIT_RPM:
        return False
    rate_limits[api_key].append(now)
    return True

async def handle_models(req):
    return web.json_response({
        "object": "list",
        "data": [{
            "id": m["id"], "object": "model", "created": 1700000000,
            "owned_by": "evez", "permission": [],
            "context_window": m["context_window"],
            "pricing": m["pricing"]
        } for m in MODELS]
    })

async def handle_completions(req):
    auth = req.headers.get("Authorization", "").replace("Bearer ", "")
    if auth not in API_KEYS and API_KEYS:
        return web.json_response({"error": {"message": "Invalid API key", "type": "auth_error"}}, status=401)

    if not check_rate_limit(auth):
        return web.json_response({"error": {"message": "Rate limit exceeded", "type": "rate_limit"}}, status=429)

    try:
        body = await req.json()
    except:
        return web.json_response({"error": {"message": "Invalid JSON", "type": "invalid_request"}}, status=400)

    model_id = body.get("model", "evez-smart")
    if model_id not in MODEL_MAP:
        return web.json_response({"error": {"message": f"Model {model_id} not found", "type": "invalid_request"}}, status=404)

    model = MODEL_MAP[model_id]
    body["model"] = model["backend"]  # Map to backend model

    # Stream support
    stream = body.get("stream", False)

    headers = {
        "Authorization": f"Bearer {VULTR_API_KEY}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        if stream:
            resp = web.StreamResponse()
            resp.content_type = "text/event-stream"
            resp.headers["Cache-Control"] = "no-cache"
            await resp.prepare(req)

            async with session.post(f"{VULTR_BASE_URL}/chat/completions", json=body, headers=headers) as r:
                async for line in r.content:
                    await resp.write(line)
            await resp.write_eof()
            return resp
        else:
            async with session.post(f"{VULTR_BASE_URL}/chat/completions", json=body, headers=headers) as r:
                result = await r.json()
                # Rewrite model name
                if "model" in result:
                    result["model"] = model_id
                return web.json_response(result)

async def handle_create_key(req):
    """Create a new API key (admin endpoint)"""
    admin = req.headers.get("X-Admin-Key", "")
    if admin != os.getenv("ADMIN_KEY", "evez-admin"):
        return web.json_response({"error": "Unauthorized"}, status=401)

    key = f"evez-{uuid.uuid4().hex[:32]}"
    API_KEYS[key] = {"created": time.time(), "name": "default"}
    return web.json_response({"key": key, "created": True})

async def handle_health(req):
    return web.json_response({"status": "healthy", "provider": "evez", "models": len(MODELS)})

# Middleware for CORS
async def cors_middleware(app, handler):
    async def middleware_handler(req):
        if req.method == "OPTIONS":
            resp = web.Response(status=204)
        else:
            resp = await handler(req)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return resp
    return middleware_handler

def create_app():
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get("/v1/models", handle_models)
    app.router.add_post("/v1/chat/completions", handle_completions)
    app.router.add_post("/v1/keys", handle_create_key)
    app.router.add_get("/health", handle_health)
    return app

if __name__ == "__main__":
    app = create_app()
    print(f"🚀 EVEZ Provider Gateway starting on port {PROVIDER_PORT}")
    print(f"📡 Models: {', '.join(m['id'] for m in MODELS)}")
    web.run_app(app, host="0.0.0.0", port=PROVIDER_PORT)
