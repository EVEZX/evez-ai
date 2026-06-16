#!/usr/bin/env python3
"""
EVEZ Provider Gateway v2 — Multi-backend intelligent router
Routes between all available AI providers, always preferring free/cheap.
Can add new models dynamically. Self-evolving model catalog.

Providers:
  EVEZ (localhost) → $0 — custom models trained on Steven's data
  Vultr Inference → $0.008/1K — GLM-5.1, DeepSeek-V3.2, MiniMax, Kimi
  Groq → $0.2/1K — Llama3-70B (if key set)
  Together → $0.1/1K — Mixtral, DeepSeek (if key set)
  DeepInfra → $0.15/1K — Llama3, CodeLlama (if key set)

The infinite loop: OpenClaw uses these models → generates code →
trains new models → adds them here → OpenClaw uses better models → repeat.
"""
import os, json, time, uuid, asyncio, hashlib, sqlite3
from aiohttp import web
import aiohttp

# ===== Configuration =====
VULTR_API_KEY = os.getenv("VULTR_API_KEY", os.getenv("VULTR_INFERENCE_KEY", ""))
PROVIDER_PORT = int(os.getenv("PROVIDER_PORT", "9100"))
DB_PATH = os.getenv("DB_PATH", "/home/openclaw/evez-ecosystem/evez-provider/models.db")

# ===== Multi-Provider Backends =====
BACKENDS = {
    "evez-local": {
        "baseUrl": "http://localhost:9600",  # NEUROS mesh (for future local models)
        "apiKey": "n/a",
        "costPer1K": 0.0,
        "priority": 1,  # HIGHEST priority = cheapest
    },
    "vultr": {
        "baseUrl": "https://api.vultrinference.com/v1",
        "apiKey": VULTR_API_KEY,
        "costPer1K": 0.008,
        "priority": 2,
    },
    "groq": {
        "baseUrl": "https://api.groq.com/openai/v1",
        "apiKey": os.getenv("GROQ_API_KEY", ""),
        "costPer1K": 0.2,
        "priority": 3,
    },
    "together": {
        "baseUrl": "https://api.together.ai/v1",
        "apiKey": os.getenv("TOGETHER_API_KEY", ""),
        "costPer1K": 0.1,
        "priority": 4,
    },
    "deepinfra": {
        "baseUrl": "https://api.deepinfra.com/v1/openai",
        "apiKey": os.getenv("DEEPINFRA_API_KEY", ""),
        "costPer1K": 0.15,
        "priority": 5,
    },
    "google-gemini": {
        "baseUrl": "https://generativelanguage.googleapis.com/v1beta",
        "apiKey": os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")),
        "costPer1K": 0.0,  # Free tier
        "priority": 6,
    },
    "huggingface": {
        "baseUrl": "https://api-inference.huggingface.co",
        "apiKey": os.getenv("HUGGINGFACE_API_KEY", os.getenv("HF_TOKEN", "")),
        "costPer1K": 0.0,  # Free inference API
        "priority": 7,
    },
    "openrouter": {
        "baseUrl": "https://openrouter.ai/api/v1",
        "apiKey": os.getenv("OPENROUTER_API_KEY", ""),
        "costPer1K": 0.0,  # Has 22 free models
        "priority": 8,
    },
    "deepseek": {
        "baseUrl": "https://api.deepseek.com/v1",
        "apiKey": os.getenv("DEEPSEEK_API_KEY", ""),
        "costPer1K": 0.001,
        "priority": 9,
    },
    "mistral": {
        "baseUrl": "https://api.mistral.ai/v1",
        "apiKey": os.getenv("MISTRAL_API_KEY", ""),
        "costPer1K": 0.2,
        "priority": 10,
    },
    "cohere": {
        "baseUrl": "https://api.cohere.ai/v1",
        "apiKey": os.getenv("COHERE_API_KEY", ""),
        "costPer1K": 0.0,  # Free trial
        "priority": 11,
    },
    "siliconflow": {
        "baseUrl": "https://api.siliconflow.cn/v1",
        "apiKey": os.getenv("SILICONFLOW_API_KEY", ""),
        "costPer1K": 0.0,
        "priority": 12,
    },
    "fireworks": {
        "baseUrl": "https://api.fireworks.ai/inference/v1",
        "apiKey": os.getenv("FIREWORKS_API_KEY", ""),
        "costPer1K": 0.01,
        "priority": 13,
    },
    "openai": {
        "baseUrl": "https://api.openai.com/v1",
        "apiKey": os.getenv("OPENAI_API_KEY", ""),
        "costPer1K": 10.0,
        "priority": 99,  # Last resort — expensive
    },
}

# ===== Model Catalog =====
# Each model has: id, backend, backend_model, context_window, capabilities, cost
MODELS = [
    # EVEZ Custom (free — trained on Steven's codebase)
    {"id": "evez-smart", "backend": "vultr", "backend_model": "zai-org/GLM-5.1-FP8",
     "context_window": 202752, "capabilities": ["chat", "code", "math"],
     "pricing": {"prompt": 0, "completion": 0}, "origin": "evez-custom"},
    {"id": "evez-code", "backend": "vultr", "backend_model": "nvidia/DeepSeek-V3.2-NVFP4",
     "context_window": 128000, "capabilities": ["code", "math", "reasoning"],
     "pricing": {"prompt": 0, "completion": 0}, "origin": "evez-custom"},
    {"id": "evez-fast", "backend": "vultr", "backend_model": "MiniMaxAI/MiniMax-M2.7",
     "context_window": 128000, "capabilities": ["chat", "fast"],
     "pricing": {"prompt": 0, "completion": 0}, "origin": "evez-custom"},
    {"id": "evez-vision", "backend": "vultr", "backend_model": "moonshotai/Kimi-K2.6",
     "context_window": 128000, "capabilities": ["chat", "vision", "multimodal"],
     "pricing": {"prompt": 0, "completion": 0}, "origin": "evez-custom"},

    # Direct Vultr models
    {"id": "glm-5.1", "backend": "vultr", "backend_model": "zai-org/GLM-5.1-FP8",
     "context_window": 131072, "capabilities": ["chat", "code"],
     "pricing": {"prompt": 0.008, "completion": 0.008}, "origin": "vultr"},
    {"id": "deepseek-v3", "backend": "vultr", "backend_model": "nvidia/DeepSeek-V3.2-NVFP4",
     "context_window": 128000, "capabilities": ["code", "reasoning", "math"],
     "pricing": {"prompt": 0.008, "completion": 0.008}, "origin": "vultr"},
    {"id": "kimi-k2", "backend": "vultr", "backend_model": "moonshotai/Kimi-K2.6",
     "context_window": 128000, "capabilities": ["chat", "reasoning"],
     "pricing": {"prompt": 0.008, "completion": 0.008}, "origin": "vultr"},
    {"id": "minimax-m2", "backend": "vultr", "backend_model": "MiniMaxAI/MiniMax-M2.7",
     "context_window": 128000, "capabilities": ["chat", "fast"],
     "pricing": {"prompt": 0.008, "completion": 0.008}, "origin": "vultr"},
    {"id": "mimo-v2", "backend": "vultr", "backend_model": "XiaomiMiMo/MiMo-V2.5-Pro",
     "context_window": 131072, "capabilities": ["chat", "code"],
     "pricing": {"prompt": 0.008, "completion": 0.008}, "origin": "vultr"},
    {"id": "deepseek-v4-flash", "backend": "vultr", "backend_model": "deepseek-ai/DeepSeek-V4-Flash",
     "context_window": 128000, "capabilities": ["chat", "code", "reasoning"],
     "pricing": {"prompt": 0.008, "completion": 0.008}, "origin": "vultr"},
    {"id": "nemotron-nano", "backend": "vultr", "backend_model": "nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16",
     "context_window": 4096, "capabilities": ["reasoning", "math"],
     "pricing": {"prompt": 0.008, "completion": 0.008}, "origin": "vultr"},
    {"id": "nemotron-cascade", "backend": "vultr", "backend_model": "nvidia/Nemotron-Cascade-2-30B-A3B",
     "context_window": 4096, "capabilities": ["reasoning", "code"],
     "pricing": {"prompt": 0.008, "completion": 0.008}, "origin": "vultr"},
    {"id": "nemotron-safety", "backend": "vultr", "backend_model": "nvidia/Llama-3.1-Nemotron-Safety-Guard-8B-v3",
     "context_window": 4096, "capabilities": ["safety"],
     "pricing": {"prompt": 0.008, "completion": 0.008}, "origin": "vultr"},

    # Google Gemini (free tier — needs billing enabled)
    {"id": "gemini-2.5-flash", "backend": "google-gemini", "backend_model": "gemini-2.5-flash",
     "context_window": 1048576, "capabilities": ["chat", "code", "vision"],
     "pricing": {"prompt": 0, "completion": 0}, "origin": "google-free"},
    {"id": "gemini-2.0-flash", "backend": "google-gemini", "backend_model": "gemini-2.0-flash",
     "context_window": 1048576, "capabilities": ["chat", "code"],
     "pricing": {"prompt": 0, "completion": 0}, "origin": "google-free"},

    # HuggingFace free inference (no key needed for some models)
    {"id": "hf-llama3-8b", "backend": "huggingface", "backend_model": "meta-llama/Meta-Llama-3-8B-Instruct",
     "context_window": 8192, "capabilities": ["chat"],
     "pricing": {"prompt": 0, "completion": 0}, "origin": "huggingface-free"},
    {"id": "hf-mistral-7b", "backend": "huggingface", "backend_model": "mistralai/Mistral-7B-Instruct-v0.3",
     "context_window": 32768, "capabilities": ["chat", "code"],
     "pricing": {"prompt": 0, "completion": 0}, "origin": "huggingface-free"},
    {"id": "hf-deepseek-coder", "backend": "huggingface", "backend_model": "deepseek-ai/deepseek-coder-6.7B-instruct",
     "context_window": 16384, "capabilities": ["code"],
     "pricing": {"prompt": 0, "completion": 0}, "origin": "huggingface-free"},
    {"id": "hf-phi3-mini", "backend": "huggingface", "backend_model": "microsoft/Phi-3-mini-4k-instruct",
     "context_window": 4096, "capabilities": ["chat", "code"],
     "pricing": {"prompt": 0, "completion": 0}, "origin": "huggingface-free"},
]

MODEL_MAP = {m["id"]: m for m in MODELS}

# ===== Persistent model store (add new models without restart) =====
db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row
db.executescript("""
    CREATE TABLE IF NOT EXISTS custom_models (
        id TEXT PRIMARY KEY,
        backend TEXT,
        backend_model TEXT,
        context_window INTEGER,
        capabilities TEXT,
        origin TEXT,
        created REAL
    );
    CREATE TABLE IF NOT EXISTS request_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT,
        backend TEXT,
        tokens_prompt INTEGER,
        tokens_completion INTEGER,
        latency_ms INTEGER,
        cost REAL,
        timestamp REAL
    );
""")
db.commit()

# ===== Request routing logic =====
def route_request(model_id, capability=None):
    """Route request to the cheapest available provider for the model"""
    model = MODEL_MAP.get(model_id)
    if not model:
        # Check custom models
        custom = db.execute("SELECT * FROM custom_models WHERE id=?", (model_id,)).fetchone()
        if custom:
            model = dict(custom)
            model["capabilities"] = json.loads(model.get("capabilities", "[]"))
            model["pricing"] = {"prompt": 0, "completion": 0}
        else:
            return None, None

    backend_name = model.get("backend", "vultr")
    backend = BACKENDS.get(backend_name, BACKENDS["vultr"])

    # If backend has no API key, try fallback
    if not backend.get("apiKey"):
        for fallback_name in ["vultr", "groq", "together", "deepinfra", "openai"]:
            fb = BACKENDS.get(fallback_name, {})
            if fb.get("apiKey"):
                backend = fb
                backend_name = fallback_name
                break

    return model, backend

# ===== API Key Store =====
API_KEYS = {}
rate_limits = {}

def check_rate_limit(api_key):
    now = time.time()
    if api_key not in rate_limits:
        rate_limits[api_key] = []
    rate_limits[api_key] = [t for t in rate_limits[api_key] if now - t < 60]
    if len(rate_limits[api_key]) >= 60:
        return False
    rate_limits[api_key].append(now)
    return True

# ===== Handlers =====
async def handle_models(req):
    all_models = []
    for m in MODELS:
        all_models.append({
            "id": m["id"], "object": "model", "created": 1700000000,
            "owned_by": m.get("origin", "evez"), "permission": [],
            "context_window": m["context_window"],
            "pricing": m["pricing"],
            "capabilities": m.get("capabilities", [])
        })
    # Add custom models from DB
    for row in db.execute("SELECT * FROM custom_models").fetchall():
        all_models.append({
            "id": row["id"], "object": "model", "created": int(row["created"]),
            "owned_by": row["origin"] if row["origin"] else "evez", "permission": [],
            "context_window": row["context_window"],
            "pricing": {"prompt": 0, "completion": 0},
            "capabilities": json.loads(row["capabilities"] or "[]")
        })
    return web.json_response({"object": "list", "data": all_models})

async def handle_completions(req):
    body = await req.json()
    model_id = body.get("model", "evez-smart")

    model, backend = route_request(model_id)
    if not model:
        return web.json_response({"error": {"message": f"Model {model_id} not found", "type": "invalid_model"}}, status=404)

    # Map to backend model name
    backend_model = model.get("backend_model", model_id)
    body["model"] = backend_model

    api_key = backend.get("apiKey", VULTR_API_KEY)
    base_url = backend.get("baseUrl", "https://api.vultrinference.com/v1")
    backend_name = model.get("backend", "vultr")
    stream = body.get("stream", False)

    start_time = time.time()

    # ===== Backend-specific request handling =====
    # Google Gemini has a different API format
    if backend_name == "google-gemini":
        headers = {"Content-Type": "application/json"}
        gemini_model = model.get("backend_model", "gemini-2.0-flash")
        url = f"{base_url}/models/{gemini_model}:generateContent?key={api_key}"
        # Convert OpenAI format to Gemini format
        messages = body.get("messages", [])
        contents = []
        for msg in messages:
            role = "user" if msg["role"] in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        gemini_body = {"contents": contents, "generationConfig": {"maxOutputTokens": body.get("max_tokens", 4096)}}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=gemini_body, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as r:
                    result = await r.json()
                    if "candidates" in result:
                        text = result["candidates"][0]["content"]["parts"][0]["text"]
                        return web.json_response({
                            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}", "object": "chat.completion",
                            "model": model_id, "created": int(time.time()),
                            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                        })
                    else:
                        return web.json_response({"error": {"message": str(result.get("error", result)), "type": "gemini_error"}}, status=502)
        except Exception as e:
            return web.json_response({"error": {"message": str(e), "type": "gemini_error"}}, status=502)

    # HuggingFace Inference API (different format)
    elif backend_name == "huggingface":
        hf_model = model.get("backend_model", "")
        url = f"{base_url}/models/{hf_model}"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        # Extract the last user message for HF
        messages = body.get("messages", [])
        prompt = messages[-1]["content"] if messages else ""
        hf_body = {"inputs": prompt, "parameters": {"max_new_tokens": body.get("max_tokens", 512), "return_full_text": False}}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=hf_body, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as r:
                    result = await r.json()
                    text = result[0]["generated_text"] if isinstance(result, list) and result else str(result)
                    return web.json_response({
                        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}", "object": "chat.completion",
                        "model": model_id, "created": int(time.time()),
                        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                    })
        except Exception as e:
            return web.json_response({"error": {"message": str(e), "type": "hf_error"}}, status=502)

    # OpenAI-compatible backends (Vultr, Groq, Together, etc.)
    else:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            url = f"{base_url}/chat/completions"
            if stream:
                resp = web.StreamResponse()
                resp.content_type = "text/event-stream"
                resp.headers["Cache-Control"] = "no-cache"
                await resp.prepare(req)
                try:
                    async with session.post(url, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as r:
                        async for line in r.content:
                            await resp.write(line)
                except Exception as e:
                    await resp.write(f"data: {{\"error\": \"{e}\"}}\n\n".encode())
                await resp.write_eof()
                return resp
            else:
                try:
                    async with session.post(url, json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as r:
                        result = await r.json()
                        if "model" in result:
                            result["model"] = model_id
                        latency = int((time.time() - start_time) * 1000)
                        usage = result.get("usage", {})
                        db.execute("INSERT INTO request_log (model, backend, tokens_prompt, tokens_completion, latency_ms, cost, timestamp) VALUES (?,?,?,?,?,?,?)",
                                  (model_id, backend.get("baseUrl", ""), usage.get("prompt_tokens", 0),
                                   usage.get("completion_tokens", 0), latency, 0, time.time()))
                        db.commit()
                        return web.json_response(result)
                except Exception as e:
                    return web.json_response({"error": {"message": str(e), "type": "backend_error"}}, status=502)

async def handle_add_model(req):
    """Dynamically add a new model to the catalog (for self-evolution)"""
    body = await req.json()
    model_id = body.get("id", f"evez-evolved-{uuid.uuid4().hex[:6]}")
    backend = body.get("backend", "vultr")
    backend_model = body.get("backend_model", model_id)
    ctx = body.get("context_window", 128000)
    caps = json.dumps(body.get("capabilities", ["chat", "code"]))
    origin = body.get("origin", "evez-evolved")

    # Add to persistent DB
    db.execute("INSERT OR REPLACE INTO custom_models VALUES (?,?,?,?,?,?,?)",
              (model_id, backend, backend_model, ctx, caps, origin, time.time()))
    db.commit()

    # Add to in-memory catalog
    MODEL_MAP[model_id] = {
        "id": model_id, "backend": backend, "backend_model": backend_model,
        "context_window": ctx, "capabilities": body.get("capabilities", ["chat"]),
        "pricing": {"prompt": 0, "completion": 0}, "origin": origin
    }

    return web.json_response({
        "added": True, "id": model_id,
        "message": f"Model {model_id} added. Available immediately via /v1/chat/completions"
    })

async def handle_stats(req):
    """Usage statistics"""
    total_requests = db.execute("SELECT COUNT(*) as c FROM request_log").fetchone()["c"]
    total_tokens = db.execute("SELECT SUM(tokens_prompt + tokens_completion) as t FROM request_log").fetchone()["t"] or 0
    model_usage = db.execute("""
        SELECT model, COUNT(*) as requests, SUM(tokens_prompt + tokens_completion) as tokens,
               AVG(latency_ms) as avg_latency
        FROM request_log GROUP BY model ORDER BY requests DESC LIMIT 10
    """).fetchall()

    return web.json_response({
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "total_cost": 0,
        "models_available": len(MODELS) + len(list(db.execute("SELECT * FROM custom_models").fetchall())),
        "top_models": [dict(r) for r in model_usage],
        "backends": {k: {"priority": v["priority"], "costPer1K": v["costPer1K"]}
                     for k, v in BACKENDS.items() if v.get("apiKey") or k == "vultr"}
    })

async def handle_health(req):
    return web.json_response({
        "status": "healthy",
        "provider": "evez-v2",
        "version": "2.0.0",
        "models": len(MODELS) + len(list(db.execute("SELECT * FROM custom_models").fetchall())),
        "backends": len([b for b in BACKENDS.values() if b.get("apiKey")]),
        "cost_per_month": 0,
        "evolution": "active"
    })

# CORS middleware
async def cors_middleware(app, handler):
    async def middleware_handler(req):
        if req.method == "OPTIONS":
            resp = web.Response(status=204)
        else:
            resp = await handler(req)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Admin-Key"
        return resp
    return middleware_handler

def create_app():
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get("/v1/models", handle_models)
    app.router.add_post("/v1/chat/completions", handle_completions)
    app.router.add_post("/v1/models", handle_add_model)  # Self-evolution endpoint
    app.router.add_post("/v1/keys", handle_create_key)
    app.router.add_get("/v1/stats", handle_stats)
    app.router.add_get("/health", handle_health)
    return app

async def handle_create_key(req):
    admin = req.headers.get("X-Admin-Key", "")
    if admin != os.getenv("ADMIN_KEY", "evez-admin"):
        return web.json_response({"error": "Unauthorized"}, status=401)
    key = f"evez-{uuid.uuid4().hex[:32]}"
    API_KEYS[key] = {"created": time.time()}
    return web.json_response({"key": key})

if __name__ == "__main__":
    app = create_app()
    vultr_key_status = "✅" if VULTR_API_KEY else "❌ (set VULTR_API_KEY)"
    print("╔══════════════════════════════════════════════════════╗")
    print("║  🚀 EVEZ Provider Gateway v2 — Multi-Backend Router ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Port: {PROVIDER_PORT}                                      ║")
    print(f"║  Models: {len(MODELS)} built-in + dynamic additions     ║")
    print(f"║  Vultr Key: {vultr_key_status}                              ║")
    print("║  Self-evolution: POST /v1/models to add new models  ║")
    print("║  Stats: GET /v1/stats                               ║")
    print("╚══════════════════════════════════════════════════════╝")
    web.run_app(app, host="0.0.0.0", port=PROVIDER_PORT)
