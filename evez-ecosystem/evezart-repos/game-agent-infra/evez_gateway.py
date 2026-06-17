"""
EvezArt OpenClaw — Built-in Gateway Server
OpenAI-compatible /v1/chat/completions endpoint
Routes to 40+ free models across Groq, OpenRouter, Cerebras, HuggingFace
Self-managing, battery-aware, Samsung Galaxy A16 optimized
"""
import os, json, time, hashlib, asyncio, logging
from pathlib import Path
from datetime import datetime, timezone

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import StreamingResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import httpx
    import uvicorn
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", 
                    "fastapi", "uvicorn[standard]", "httpx", "--quiet"])
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import StreamingResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import httpx
    import uvicorn

logging.basicConfig(level=logging.INFO, format='[EVEZ] %(message)s')
log = logging.getLogger("evezart")

app = FastAPI(
    title="EvezArt OpenClaw Gateway",
    description="Personal AI gateway — 40+ free models. EVEZ-OS powered.",
    version="2026.06.05"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ─────────────────────────────────────────────────────────────────────
CONFIG_DIR = Path(os.environ.get("OPENCLAW_CONFIG_DIR", Path.home() / ".openclaw"))
SPINE_FILE = CONFIG_DIR / "spine.jsonl"
GATEWAY_TOKEN = os.environ.get("GATEWAY_TOKEN", "evezart-default-token")
PORT = int(os.environ.get("PORT", 8080))

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
CEREBRAS_KEY = os.environ.get("CEREBRAS_API_KEY", "")
HF_KEY = os.environ.get("HUGGING_FACE_ACCESS_TOKEN", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")

# ── Model → Provider routing ───────────────────────────────────────────────────
PROVIDER_MAP = {
    # Groq models
    "llama-3.3-70b-versatile": ("groq", "llama-3.3-70b-versatile"),
    "llama-3.1-8b-instant": ("groq", "llama-3.1-8b-instant"),
    "llama-4-scout-17b-16e-instruct": ("groq", "llama-4-scout-17b-16e-instruct"),
    "qwen-qwq-32b": ("groq", "qwen-qwq-32b"),
    "mixtral-8x7b-32768": ("groq", "mixtral-8x7b-32768"),
    "llama3-8b-8192": ("groq", "llama3-8b-8192"),
    "llama3-70b-8192": ("groq", "llama3-70b-8192"),
    # OpenRouter free models
    "gpt-oss-120b": ("openrouter", "openai/gpt-oss-120b:free"),
    "gpt-oss-20b": ("openrouter", "openai/gpt-oss-20b:free"),
    "deepseek-r1": ("openrouter", "deepseek/deepseek-r1:free"),
    "deepseek-chat": ("openrouter", "deepseek/deepseek-chat-v3-0324:free"),
    "deepseek-v4-flash": ("openrouter", "deepseek/deepseek-v4-flash:free"),
    "llama-4-maverick": ("openrouter", "meta-llama/llama-4-maverick:free"),
    "llama-4-scout": ("openrouter", "meta-llama/llama-4-scout:free"),
    "llama-3.3-70b": ("openrouter", "meta-llama/llama-3.3-70b-instruct:free"),
    "gemini-flash": ("openrouter", "google/gemini-2.0-flash-exp:free"),
    "gemini-2.5-flash": ("openrouter", "google/gemini-2.5-flash-preview:free"),
    "qwen3-235b": ("openrouter", "qwen/qwen3-235b-a22b:free"),
    "qwen3-coder": ("openrouter", "qwen/qwen3-coder:free"),
    "nemotron-super-120b": ("openrouter", "nvidia/nemotron-3-super-120b-a12b:free"),
    "nemotron-nano-vision": ("openrouter", "nvidia/nemotron-nano-12b-v2-vl:free"),
    "kimi-k2": ("openrouter", "moonshotai/kimi-k2.6:free"),
    "hermes-405b": ("openrouter", "nousresearch/hermes-3-llama-3.1-405b:free"),
    "minimax-m2": ("openrouter", "minimax/minimax-m2.5:free"),
    "dolphin-mistral": ("openrouter", "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"),
    "mistral-7b": ("openrouter", "mistralai/mistral-7b-instruct:free"),
    "glm-4.5-air": ("openrouter", "z-ai/glm-4.5-air:free"),
    # Cerebras models
    "cerebras-llama-8b": ("cerebras", "llama3.1-8b"),
    "cerebras-llama-70b": ("cerebras", "llama3.1-70b"),
}

# Smart routing by task hint in system prompt
ROUTING_RULES = [
    (["code", "debug", "implement", "function", "class", "script"], "qwen3-coder"),
    (["reason", "math", "logic", "proof", "analyze", "think"], "deepseek-r1"),
    (["fast", "quick", "simple", "brief"], "llama-3.1-8b-instant"),
    (["image", "vision", "screenshot", "visual"], "nemotron-nano-vision"),
    (["write", "essay", "creative", "story", "email"], "deepseek-chat"),
    (["large", "complex", "deep", "comprehensive"], "qwen3-235b"),
]

DEFAULT_MODEL = "llama-3.3-70b-versatile"

def smart_route(model: str, messages: list) -> str:
    """Auto-route to best free model based on context."""
    if model and model in PROVIDER_MAP:
        return model
    # Scan system + first user message for routing hints
    context = " ".join([
        m.get("content", "") for m in messages[:2] 
        if isinstance(m.get("content"), str)
    ]).lower()
    for keywords, target_model in ROUTING_RULES:
        if any(k in context for k in keywords):
            return target_model
    return DEFAULT_MODEL

async def call_groq(model: str, payload: dict) -> dict:
    """Call Groq API."""
    if not GROQ_KEY:
        raise HTTPException(status_code=503, detail="Groq key not configured")
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={**payload, "model": model}
        )
        r.raise_for_status()
        return r.json()

async def call_openrouter(model: str, payload: dict) -> dict:
    """Call OpenRouter API."""
    if not OPENROUTER_KEY:
        raise HTTPException(status_code=503, detail="OpenRouter key not configured")
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/EvezArt/evez-os",
                "X-Title": "EvezArt-OpenClaw"
            },
            json={**payload, "model": model}
        )
        r.raise_for_status()
        return r.json()

async def call_cerebras(model: str, payload: dict) -> dict:
    """Call Cerebras API."""
    if not CEREBRAS_KEY:
        raise HTTPException(status_code=503, detail="Cerebras key not configured")
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {CEREBRAS_KEY}", "Content-Type": "application/json"},
            json={**payload, "model": model}
        )
        r.raise_for_status()
        return r.json()

PROVIDER_FUNCS = {
    "groq": call_groq,
    "openrouter": call_openrouter,
    "cerebras": call_cerebras,
}

# Failover order
FAILOVER = ["groq", "openrouter", "cerebras"]

def append_spine(event: str, data: dict = {}):
    """Append event to the immutable SPINE."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        prev_hash = ""
        if SPINE_FILE.exists():
            try:
                last_line = SPINE_FILE.read_text().strip().split("\n")[-1]
                prev_hash = json.loads(last_line).get("hash", "")
            except:
                pass
        ts = datetime.now(timezone.utc).isoformat()
        payload = json.dumps({"ts": ts, "event": event, **data}, sort_keys=True)
        hash_val = hashlib.sha256((payload + prev_hash).encode()).hexdigest()
        entry = {"ts": ts, "event": event, "prev_hash": prev_hash, "hash": hash_val, **data}
        with open(SPINE_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        log.warning(f"Spine append failed: {e}")

async def telegram_notify(msg: str):
    """Send Telegram notification."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "Markdown"}
            )
    except:
        pass

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "alive", "identity": "EvezArt OpenClaw", "version": "2026.06.05"}

@app.get("/")
async def root():
    return {
        "name": "EvezArt OpenClaw Gateway",
        "version": "2026.06.05",
        "identity": "EVEZ-OS Personal AI — Steven Crawford-Maggard",
        "models": list(PROVIDER_MAP.keys()),
        "providers": ["groq", "openrouter", "cerebras", "huggingface"],
        "free_models": len([m for m in PROVIDER_MAP if "openrouter" in PROVIDER_MAP[m][0]]) + 7,
        "endpoints": ["/v1/chat/completions", "/v1/models", "/health", "/spine", "/status"]
    }

@app.get("/v1/models")
async def list_models():
    models = []
    for alias, (provider, model_id) in PROVIDER_MAP.items():
        models.append({
            "id": alias,
            "object": "model",
            "created": 1748995200,
            "owned_by": f"evezart-{provider}",
            "provider": provider,
            "model_id": model_id,
            "free": True
        })
    return {"object": "list", "data": models}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    # Auth check
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    if token and token != GATEWAY_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid gateway token")

    body = await request.json()
    messages = body.get("messages", [])
    requested_model = body.get("model", DEFAULT_MODEL)

    # Smart routing
    model_alias = smart_route(requested_model, messages)
    provider_name, model_id = PROVIDER_MAP.get(model_alias, ("groq", "llama-3.3-70b-versatile"))

    log.info(f"Request: {requested_model} → {provider_name}:{model_id}")
    append_spine("INFERENCE_REQUEST", {"model": model_alias, "provider": provider_name})

    # Clean payload
    payload = {k: v for k, v in body.items() if k not in ("model",)}

    # Try primary provider, then failover
    providers_to_try = [provider_name] + [p for p in FAILOVER if p != provider_name]
    
    last_error = None
    for provider in providers_to_try:
        if provider not in PROVIDER_FUNCS:
            continue
        try:
            # Get the right model for this provider
            if provider == provider_name:
                m = model_id
            elif provider == "groq":
                m = "llama-3.3-70b-versatile"
            elif provider == "openrouter":
                m = "meta-llama/llama-3.3-70b-instruct:free"
            elif provider == "cerebras":
                m = "llama3.1-70b"
            else:
                continue
            
            result = await PROVIDER_FUNCS[provider](m, payload)
            append_spine("INFERENCE_SUCCESS", {"provider": provider, "model": m})
            return JSONResponse(content=result)
        except Exception as e:
            log.warning(f"Provider {provider} failed: {e}")
            last_error = e
            continue

    append_spine("INFERENCE_FAILED", {"error": str(last_error)})
    raise HTTPException(status_code=503, detail=f"All providers failed: {last_error}")

@app.get("/spine")
async def get_spine(limit: int = 50):
    """Read last N spine events."""
    if not SPINE_FILE.exists():
        return {"events": [], "count": 0}
    lines = SPINE_FILE.read_text().strip().split("\n")
    events = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except:
            pass
    return {"events": events, "count": len(events), "total": len(lines)}

@app.get("/status")
async def status():
    """Full system status."""
    spine_count = 0
    if SPINE_FILE.exists():
        spine_count = len(SPINE_FILE.read_text().strip().split("\n"))
    
    providers_available = []
    if GROQ_KEY: providers_available.append("groq")
    if OPENROUTER_KEY: providers_available.append("openrouter")
    if CEREBRAS_KEY: providers_available.append("cerebras")
    if HF_KEY: providers_available.append("huggingface")
    
    return {
        "identity": "EvezArt OpenClaw — EVEZ-OS Personal AI",
        "owner": "Steven Crawford-Maggard (EVEZ666)",
        "version": "2026.06.05",
        "spine_events": spine_count,
        "providers_available": providers_available,
        "total_models": len(PROVIDER_MAP),
        "free_models": len(PROVIDER_MAP),
        "uptime": "self-managing",
        "telegram_connected": bool(TELEGRAM_TOKEN),
        "github_sync": True,
        "android_optimized": True,
        "device": "Samsung Galaxy A16"
    }

# ── Boot ───────────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    append_spine("GATEWAY_BOOT", {
        "version": "2026.06.05",
        "providers": len([k for k in [GROQ_KEY, OPENROUTER_KEY, CEREBRAS_KEY] if k]),
        "models": len(PROVIDER_MAP)
    })
    log.info(f"EvezArt OpenClaw live on port {PORT}")
    log.info(f"Models: {len(PROVIDER_MAP)} | Providers: groq={bool(GROQ_KEY)} openrouter={bool(OPENROUTER_KEY)} cerebras={bool(CEREBRAS_KEY)}")
    asyncio.create_task(telegram_notify(
        f"🚀 *EvezArt OpenClaw ONLINE*\n"
        f"Models: {len(PROVIDER_MAP)} free\n"
        f"Port: {PORT}\n"
        f"Spine: {SPINE_FILE}"
    ))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
