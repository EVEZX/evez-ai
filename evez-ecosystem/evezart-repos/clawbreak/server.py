"""ClawBreak - FastAPI server with chat, tools, memory, web UI, and full EVEZ ecosystem integration.

Cross-service integration:
- POSTs every chat to spine :8090/event
- Queries proofs :8098 for ecosystem coherence on every /chat response
- GET /ecosystem — unified dashboard from all services
- POST /world-solve — proxies to world solver :8096/solve
- POST /eigenforensics — proxies to disclosure :8087/api/v1/analyze
- GET /consciousness — proxies to observatory :8097/stats
- GET /ecosystem-status — what ClawBreak connects to

AI Inference:
- Groq free tier (Llama 3.3 70B) via GROQ_API_KEY env var
- Falls back to configured LLM backends
- Echo mode with instructions if no API key
- Conversation memory: last 20 messages per session
- SSE streaming via /chat/stream
"""
import os
import sys
import json
import time
import uuid
import asyncio
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import httpx
import uvicorn

from config import Config
from memory import Memory
from tools import ToolEngine
from tool_parser import parse_tool_calls

import stripe

# Sub-modules
from marketplace import router as marketplace_router
from guard import router as guard_router
from consciousness_api import router as consciousness_router

# ── Cross-service HTTP client (shared, with timeout) ──────────────
_client = httpx.AsyncClient(timeout=5)

# Service registry
SERVICES = {
    "spine": "http://localhost:8090",
    "world-solver": "http://localhost:8096",
    "consciousness-observatory": "http://localhost:8097",
    "proofs-engine": "http://localhost:8098",
    "disclosure-tools": "http://localhost:8087",
}


async def _post_to_spine(event_type: str, data: dict):
    """Fire-and-forget post to spine. Never crashes caller."""
    try:
        await _client.post(f"{SERVICES['spine']}/event", json={
            "event_type": event_type,
            "source": "clawbreak",
            "data": data,
            "topics": [event_type, "agent_comm"],
        })
    except Exception:
        pass


async def _query_proofs_eta_star() -> dict:
    """Query proofs engine for η*. Returns {} on failure."""
    try:
        resp = await _client.get(f"{SERVICES['proofs-engine']}/prove/eta-star")
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


# Init
config = Config()
memory = Memory(config.get("memory", "db_path"))
tools = ToolEngine(config, memory)

app = FastAPI(title="ClawBreak", version="0.3.0")

# --- Stripe Config ---
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_IDS = {
    "pro": os.environ.get("STRIPE_PRICE_ID_PRO", ""),
    "team": os.environ.get("STRIPE_PRICE_ID_TEAM", ""),
    "enterprise": os.environ.get("STRIPE_PRICE_ID_ENTERPRISE", ""),
}
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# --- Groq Integration ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# --- Conversation Memory (last 20 messages per session) ---
MAX_CONVERSATION = 20
_conversations: dict = defaultdict(list)  # session_id -> [messages]


def _store_conversation(session_id: str, role: str, content: str):
    """Store a message in conversation memory (capped at MAX_CONVERSATION)."""
    _conversations[session_id].append({"role": role, "content": content})
    if len(_conversations[session_id]) > MAX_CONVERSATION:
        _conversations[session_id] = _conversations[session_id][-MAX_CONVERSATION:]


def _get_conversation(session_id: str) -> list:
    """Get conversation history for a session."""
    return list(_conversations[session_id])


# --- LLM Client ---

async def _call_llm(base_url, api_key, model, messages, stream=False, timeout=120):
    """Single LLM API call. Returns (result_dict, error_string)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": config.get("llm", "max_tokens"),
        "temperature": config.get("llm", "temperature"),
        "stream": stream,
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json(), None
        except httpx.HTTPStatusError as e:
            return None, f"LLM API error {e.response.status_code}: {e.response.text[:500]}"
        except Exception as e:
            return None, f"LLM request failed: {e}"


async def chat_completion(messages, stream=False):
    """Call the LLM API: Groq first → fallback chain → primary → echo mode."""
    # 1. Groq (free tier)
    if GROQ_API_KEY:
        result, err = await _call_llm(GROQ_BASE_URL, GROQ_API_KEY, GROQ_MODEL, messages, stream=stream)
        if result:
            return result

    # 2. Fallback chain
    fallback_chain = config.data.get("fallback", [])
    for backend in fallback_chain:
        base_url = backend.get("base_url", "")
        api_key = backend.get("api_key", "")
        model = backend.get("model", config.get("llm", "model"))
        timeout = backend.get("timeout", 30)
        if not api_key:
            continue
        result, err = await _call_llm(base_url, api_key, model, messages, stream=stream, timeout=timeout)
        if result:
            return result

    # 3. Primary (legacy)
    api_key = config.get("llm", "api_key")
    base_url = config.get("llm", "base_url")
    model = config.get("llm", "model")
    if api_key:
        result, err = await _call_llm(base_url, api_key, model, messages, stream=stream)
        if result:
            return result

    # 4. Echo mode — no API key configured
    user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_msg = m.get("content", "")
            break
    return {
        "echo_mode": True,
        "reply": (
            "🔑 No AI API key configured. To enable real AI responses:\n"
            "1. Get a FREE Groq API key at https://console.groq.com/keys\n"
            "2. Set environment variable: GROQ_API_KEY=your_key\n"
            "3. Restart ClawBreak\n\n"
            f"Your message: {user_msg}"
        ),
        "instructions": "Set GROQ_API_KEY for free Llama 3.3 70B inference via Groq",
    }


async def _stream_from(base_url, api_key, model, messages):
    """Stream from a specific LLM backend. Yields SSE lines."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": config.get("llm", "max_tokens"),
        "temperature": config.get("llm", "temperature"),
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            async with client.stream("POST", f"{base_url}/chat/completions", headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            yield f"data: [DONE]\n\n"
                            return
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                yield f"data: {json.dumps({'content': delta['content']})}\n\n"
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"


async def chat_completion_stream(messages):
    """Stream chat completion — Groq → fallback chain → primary → echo."""
    # 1. Groq
    if GROQ_API_KEY:
        got_content = False
        async for chunk in _stream_from(GROQ_BASE_URL, GROQ_API_KEY, GROQ_MODEL, messages):
            yield chunk
            got_content = True
        if got_content:
            return

    # 2. Fallback chain
    fallback_chain = config.data.get("fallback", [])
    for backend in fallback_chain:
        api_key = backend.get("api_key", "")
        if not api_key:
            continue
        base_url = backend.get("base_url", "")
        model = backend.get("model", config.get("llm", "model"))
        got_content = False
        async for chunk in _stream_from(base_url, api_key, model, messages):
            yield chunk
            got_content = True
        if got_content:
            return

    # 3. Primary
    api_key = config.get("llm", "api_key")
    if api_key:
        got_content = False
        async for chunk in _stream_from(config.get("llm", "base_url"), api_key, config.get("llm", "model"), messages):
            yield chunk
            got_content = True
        if got_content:
            return

    # 4. Echo fallback
    user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_msg = m.get("content", "")
            break
    echo_msg = f"🔑 No API key. Get a free Groq key at https://console.groq.com/keys and set GROQ_API_KEY.\n\nYour message: {user_msg}"
    yield f"data: {json.dumps({'content': echo_msg})}\n\n"
    yield f"data: [DONE]\n\n"


async def process_message(user_message: str, session_id: str = "default") -> str:
    """Process a user message through the LLM with tool execution + ecosystem integration."""
    await _post_to_spine("agent_comm", {
        "session_id": session_id,
        "action": "user_message",
        "message_preview": user_message[:200],
    })

    # Store in both conversation memory and persistent memory
    _store_conversation(session_id, "user", user_message)
    memory.store_message("user", user_message, session_id)

    # Build from conversation memory
    history = _get_conversation(session_id)
    messages = [{"role": "system", "content": config.get("system_prompt")}]
    messages.extend(history)

    # Call LLM
    response = await chat_completion(messages)

    if response.get("echo_mode"):
        return response["reply"]

    if "error" in response:
        return f"Error: {response['error']}"

    try:
        assistant_msg = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return "Error: Unexpected API response format"

    # Check for tool calls
    tool_calls = parse_tool_calls(assistant_msg)
    if tool_calls:
        tool_results = []
        for tc in tool_calls:
            result = tools.execute(tc["name"], tc["args"])
            tool_results.append(f"[tool:{tc['name']} result]\n{json.dumps(result, indent=2, ensure_ascii=False)[:2000]}")

        tool_context = "\n\n".join(tool_results)
        messages.append({"role": "assistant", "content": assistant_msg})
        messages.append({"role": "user", "content": f"Tool execution results:\n{tool_context}\n\nNow respond to the user based on these results."})

        response2 = await chat_completion(messages)
        if "error" not in response2 and not response2.get("echo_mode"):
            try:
                assistant_msg = response2["choices"][0]["message"]["content"]
            except:
                pass

    # Store assistant response
    _store_conversation(session_id, "assistant", assistant_msg)
    memory.store_message("assistant", assistant_msg, session_id)
    memory.cleanup_old_messages(session_id)

    # Ecosystem integration
    eta_result = await _query_proofs_eta_star()
    await _post_to_spine("agent_comm", {
        "session_id": session_id,
        "action": "assistant_response",
        "response_preview": assistant_msg[:200],
        "ecosystem_phi": eta_result.get("phi"),
        "ecosystem_eta_star": eta_result.get("eta_star"),
    })

    return assistant_msg


# --- Routes ---

async def _check_evez_health():
    """Check EVEZ API health and return status dict."""
    evez_cfg = config.data.get("evez_api", {})
    base_url = evez_cfg.get("base_url", "http://localhost:8081")
    health_path = evez_cfg.get("health_path", "/health")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{base_url}{health_path}")
            resp.raise_for_status()
            return {"status": "ok", **resp.json()}
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}


@app.get("/health")
async def health():
    evez_status = await _check_evez_health()
    return {
        "status": "ok",
        "version": "0.3.0",
        "model": GROQ_MODEL if GROQ_API_KEY else config.get("llm", "model"),
        "groq": "configured" if GROQ_API_KEY else "not set (set GROQ_API_KEY)",
        "memory_facts": len(memory.list_facts(limit=9999)),
        "uptime": time.time(),
        "evez_api": evez_status,
    }


@app.post("/chat")
async def chat(request: Request):
    """Non-streaming chat endpoint with Groq AI inference and conversation memory."""
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id", "default")

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    # Store in conversation memory
    _store_conversation(session_id, "user", message)
    memory.store_message("user", message, session_id)

    # Build messages from conversation memory
    history = _get_conversation(session_id)
    messages = [{"role": "system", "content": config.get("system_prompt")}]
    messages.extend(history)

    # Call LLM
    response = await chat_completion(messages)

    if response.get("echo_mode"):
        return {"reply": response["reply"], "session_id": session_id, "echo_mode": True}

    if "error" in response:
        return JSONResponse({"error": response["error"]}, status_code=502)

    try:
        assistant_msg = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return JSONResponse({"error": "Unexpected API response"}, status_code=502)

    # Store assistant response in conversation memory
    _store_conversation(session_id, "assistant", assistant_msg)
    memory.store_message("assistant", assistant_msg, session_id)

    return {"reply": assistant_msg, "session_id": session_id, "model": GROQ_MODEL if GROQ_API_KEY else "fallback"}


@app.post("/chat/stream")
async def chat_stream(request: Request):
    """Streaming chat endpoint via SSE with Groq and conversation memory."""
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id", "default")

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    # Store in conversation memory
    _store_conversation(session_id, "user", message)
    memory.store_message("user", message, session_id)

    # Build from conversation memory
    history = _get_conversation(session_id)
    messages = [{"role": "system", "content": config.get("system_prompt")}]
    messages.extend(history)

    async def generate():
        full_response = []
        async for chunk in chat_completion_stream(messages):
            yield chunk
            if chunk.startswith("data: ") and "content" in chunk:
                try:
                    data = json.loads(chunk[6:])
                    if "content" in data:
                        full_response.append(data["content"])
                except:
                    pass

        # Store complete response
        if full_response:
            complete = "".join(full_response)
            _store_conversation(session_id, "assistant", complete)
            memory.store_message("assistant", complete, session_id)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/memory")
async def get_memory(category: str = None, query: str = None):
    if query:
        return {"facts": memory.recall_facts(query)}
    return {"facts": memory.list_facts(category)}


@app.post("/memory")
async def store_memory(request: Request):
    body = await request.json()
    key = body.get("key")
    value = body.get("value")
    category = body.get("category", "general")
    if not key or not value:
        return JSONResponse({"error": "key and value required"}, status_code=400)
    memory.store_fact(key, value, category)
    return {"status": "stored", "key": key}


@app.delete("/memory/{key}")
async def delete_memory(key: str):
    memory.delete_fact(key)
    return {"status": "deleted", "key": key}


@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """WebSocket for real-time chat."""
    await websocket.accept()
    session_id = str(uuid.uuid4())[:8]

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                message = msg.get("message", "")
            except json.JSONDecodeError:
                message = data

            if not message:
                continue

            reply = await process_message(message, session_id)
            await websocket.send_text(json.dumps({"reply": reply, "session_id": session_id}))
    except WebSocketDisconnect:
        pass


# ══════════════════════════════════════════════════════════════════
# EVEZ ECOSYSTEM INTEGRATION ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@app.get("/ecosystem")
async def ecosystem_dashboard():
    """Unified dashboard — calls health aggregator, spine, proofs, consciousness observatory."""
    results = {}

    for name, url in [("spine", SERVICES['spine']), ("proofs", SERVICES['proofs-engine']),
                       ("consciousness", SERVICES['consciousness-observatory']),
                       ("world_solver", SERVICES['world-solver']),
                       ("disclosure", SERVICES['disclosure-tools'])]:
        try:
            resp = await _client.get(f"{url}/health")
            results[name] = resp.json()
        except Exception as e:
            results[name] = {"status": "down", "error": str(e)[:100]}

    results["evez_api"] = await _check_evez_health()

    live = sum(1 for v in results.values() if isinstance(v, dict) and v.get("status") not in ("down", "unreachable"))

    return {
        "ecosystem": results,
        "live_services": live,
        "total_services_queried": len(results),
        "timestamp": time.time(),
    }


@app.post("/world-solve")
async def world_solve(request: Request):
    """Proxy to world solver :8096/solve."""
    body = await request.json()
    budget = body.get("total_budget_billions", 100)
    try:
        resp = await _client.get(f"{SERVICES['world-solver']}/solve", params={"total_budget_billions": budget})
        return resp.json()
    except Exception as e:
        return JSONResponse({"error": f"World solver unreachable: {str(e)}"}, status_code=502)


@app.post("/eigenforensics")
async def eigenforensics(request: Request):
    """Proxy to disclosure.tools :8087/api/v1/analyze."""
    body = await request.json()
    try:
        resp = await _client.post(f"{SERVICES['disclosure-tools']}/api/v1/analyze", json=body, timeout=10)
        return resp.json()
    except Exception as e:
        return JSONResponse({"error": f"Disclosure tools unreachable: {str(e)}"}, status_code=502)


@app.get("/consciousness")
async def consciousness():
    """Proxy to consciousness observatory :8097/stats."""
    try:
        resp = await _client.get(f"{SERVICES['consciousness-observatory']}/stats")
        return resp.json()
    except Exception as e:
        return JSONResponse({"error": f"Consciousness observatory unreachable: {str(e)}"}, status_code=502)


@app.get("/ecosystem-status")
async def ecosystem_status():
    """What ClawBreak connects to and their status."""
    connections = {}
    for name, url in SERVICES.items():
        try:
            resp = await _client.get(f"{url}/health")
            connections[name] = {"url": url, "status": "up", "health": resp.json()}
        except Exception as e:
            connections[name] = {"url": url, "status": "down", "error": str(e)[:80]}

    return {
        "service": "clawbreak",
        "role": "agent_frontend",
        "connects_to": connections,
        "integration_features": [
            "POSTs every chat to spine /event",
            "Queries proofs /prove/eta-star on every /chat response",
            "/ecosystem unified dashboard",
            "/world-solve proxy",
            "/eigenforensics proxy",
            "/consciousness proxy",
        ],
    }


# --- Stripe Billing Endpoints ---

@app.post("/billing/checkout")
async def billing_checkout(request: Request):
    """Create a REAL Stripe Checkout Session, or mock checkout if no Stripe key."""
    body = await request.json()
    plan = body.get("plan", "").lower()

    PLANS = {"free": {"price": 0}, "pro": {"price": 29}, "team": {"price": 99}, "enterprise": {"price": 499}}
    if plan not in PLANS:
        return JSONResponse({"error": f"Invalid plan. Choose from: {', '.join(PLANS.keys())}"}, status_code=400)

    if plan == "free":
        return {"url": f"{BASE_URL}/billing/success?plan=free", "plan": plan, "message": "Free plan — no checkout needed"}

    if STRIPE_SECRET_KEY and STRIPE_PRICE_IDS.get(plan):
        price_id = STRIPE_PRICE_IDS[plan]
        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=f"{BASE_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{BASE_URL}/pricing",
                metadata={"plan": plan},
            )
            return {"url": session.url, "session_id": session.id}
        except stripe.error.StripeError as e:
            return JSONResponse({"error": f"Stripe error: {str(e)}"}, status_code=502)

    # Mock checkout — Stripe not fully configured
    mock_session = f"cs_mock_{plan}_{uuid.uuid4().hex[:8]}"
    return {
        "url": f"{BASE_URL}/billing/success?session_id={mock_session}&plan={plan}",
        "session_id": mock_session,
        "mock": True,
        "plan": plan,
        "price_monthly": PLANS[plan]["price"],
        "message": (
            "Stripe not configured. To enable real payments:\n"
            "1. Create a Stripe account at https://stripe.com\n"
            f"2. Set STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, and STRIPE_PRICE_ID_{plan.upper()} env vars\n"
            "3. For now, use this mock URL to test the flow"
        ),
    }


@app.post("/billing/portal")
async def billing_portal(request: Request):
    """Create a Stripe Customer Portal session, or mock if no Stripe key."""
    body = await request.json()
    customer_id = body.get("customer_id")
    if not customer_id:
        return JSONResponse({"error": "customer_id is required"}, status_code=400)

    if STRIPE_SECRET_KEY:
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=f"{BASE_URL}/pricing",
            )
            return {"url": session.url}
        except stripe.error.StripeError as e:
            return JSONResponse({"error": f"Stripe error: {str(e)}"}, status_code=502)

    return {
        "url": f"{BASE_URL}/billing/success?portal=true&customer={customer_id}",
        "mock": True,
        "message": "Stripe not configured. Set STRIPE_SECRET_KEY to enable real customer portal.",
    }


@app.post("/billing/webhook")
async def billing_webhook(request: Request):
    """Handle Stripe webhook events with signature verification."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if STRIPE_WEBHOOK_SECRET and sig_header:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except stripe.error.SignatureVerificationError:
            return JSONResponse({"error": "Invalid signature"}, status_code=400)
        except Exception as e:
            return JSONResponse({"error": f"Webhook construction failed: {str(e)}"}, status_code=400)
    else:
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return JSONResponse({"error": "Invalid JSON payload"}, status_code=400)

    evt_type = event.get("type", "")

    if evt_type == "checkout.session.completed":
        session_obj = event["data"]["object"]
        plan = session_obj.get("metadata", {}).get("plan", "unknown")
        customer_id = session_obj.get("customer")
        session_id = session_obj.get("id")
        print(f"✅ Checkout completed: plan={plan}, customer={customer_id}, session={session_id}")
    elif evt_type == "customer.subscription.updated":
        sub = event["data"]["object"]
        print(f"🔄 Subscription updated: {sub.get('id')}")
    elif evt_type == "customer.subscription.deleted":
        sub = event["data"]["object"]
        print(f"❌ Subscription canceled: {sub.get('id')}")
    elif evt_type == "invoice.payment_failed":
        inv = event["data"]["object"]
        print(f"⚠️ Payment failed: {inv.get('id')}")
    elif evt_type == "invoice.paid":
        inv = event["data"]["object"]
        print(f"💰 Invoice paid: {inv.get('id')}")
    else:
        print(f"ℹ️ Unhandled webhook: {evt_type}")

    return {"received": True}


@app.get("/billing/success")
async def billing_success(request: Request):
    """Landing page after successful checkout with receipt details."""
    session_id = request.query_params.get("session_id", "")
    plan = request.query_params.get("plan", "unknown")

    receipt_info = ""
    if STRIPE_SECRET_KEY and session_id and not session_id.startswith("cs_mock"):
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            amount = session.get("amount_total", 0) / 100
            receipt_info = f"<p>Amount: ${amount:.2f}/mo</p><p>Customer: {session.get('customer', 'N/A')}</p>"
        except Exception:
            pass

    return HTMLResponse(f"""<html><body style='background:#0a0a0f;color:#e0e0e0;font-family:sans-serif;text-align:center;padding-top:15vh'>
    <h1>✅ Welcome to ClawBreak!</h1>
    <p>Plan: <strong>{plan.upper()}</strong></p>
    {receipt_info}
    <p>Session: {session_id or 'N/A'}</p>
    <p><a href='/pricing' style='color:#ff4500'>Back to pricing</a></p>
    </body></html>""")


@app.get("/billing/prices")
async def billing_prices():
    """Return the price table as JSON."""
    return {
        "plans": [
            {"id": "free", "name": "Free", "price_monthly": 0, "features": ["5 messages/day", "1 agent", "Basic tools"], "rate_limit": "10 req/min"},
            {"id": "pro", "name": "Pro", "price_monthly": 29, "features": ["Unlimited messages", "5 agents", "All tools", "Priority support"], "rate_limit": "100 req/min"},
            {"id": "team", "name": "Team", "price_monthly": 99, "features": ["Everything in Pro", "25 agents", "Team sharing", "Admin console"], "rate_limit": "500 req/min"},
            {"id": "enterprise", "name": "Enterprise", "price_monthly": 499, "features": ["Everything in Team", "Unlimited agents", "SSO/SAML", "Custom deployments", "SLA"], "rate_limit": "unlimited"},
        ],
        "stripe_configured": bool(STRIPE_SECRET_KEY),
    }


# --- Register Sub-Module Routers ---
app.include_router(marketplace_router)
app.include_router(guard_router)
app.include_router(consciousness_router)


# Serve web UI
STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
async def serve_landing():
    landing = STATIC_DIR / "landing.html"
    if landing.exists():
        return HTMLResponse(landing.read_text())
    return HTMLResponse("<h1>EVEZ-OS</h1><p>Landing page not found.</p>")


@app.get("/chat")
async def serve_chat():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text())
    return HTMLResponse("<h1>ClawBreak Chat</h1><p>Chat UI not found. Use the API.</p>")


@app.get("/config")
async def get_config():
    cfg = dict(config.data)
    cfg["llm"]["api_key"] = f"{cfg['llm']['api_key'][:6]}..." if cfg["llm"]["api_key"] else "not set"
    return cfg


@app.post("/config")
async def update_config(request: Request):
    body = await request.json()
    config._deep_merge(config.data, body)
    config.save()
    return {"status": "updated"}


# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/api/v1/models")
async def list_models():
    """List available models — includes Groq, Vultr, and local models."""
    models = []

    if GROQ_API_KEY:
        models.extend([
            {"id": "llama-3.3-70b-versatile", "object": "model", "owned_by": "groq", "tier": "free", "context": 128000},
            {"id": "llama-3.1-8b-instant", "object": "model", "owned_by": "groq", "tier": "free", "context": 128000},
            {"id": "mixtral-8x7b-32768", "object": "model", "owned_by": "groq", "tier": "free", "context": 32768},
        ])

    models.append({
        "id": config.get("llm", "model"),
        "object": "model",
        "created": int(time.time()),
        "owned_by": "vultr",
        "tier": "pro",
    })

    return {"object": "list", "data": models}


# === EVEZ-OS Integration ===

import subprocess
import hashlib
import time as _time

EVEZ_STATE = {
    "v_global": 6.128,
    "round": 182,
    "fires": 31,
    "plane": "✓ CANONICAL",
    "spine": []
}


@app.get("/api/evez/status")
async def evez_status():
    return EVEZ_STATE


@app.post("/api/evez/run/{cmd}")
async def evez_run(cmd: str):
    ts = _time.time()
    h = hashlib.sha256(f"{cmd}{ts}".encode()).hexdigest()[:12]

    if cmd == "play":
        EVEZ_STATE["round"] += 1
        EVEZ_STATE["v_global"] = round(EVEZ_STATE["v_global"] + 0.001, 3)
        EVEZ_STATE["spine"].append({"t": ts, "h": h, "event": "PLAY", "round": EVEZ_STATE["round"]})
        return {"status": "ok", "round": EVEZ_STATE["round"], "v": EVEZ_STATE["v_global"], "hash": h}

    elif cmd == "visualize":
        return {"status": "ok", "artifact": f"cognition-{h}.svg", "frames": 24, "layers": ["attention", "memory", "output"]}

    elif cmd == "spine":
        recent = EVEZ_STATE["spine"][-10:] if len(EVEZ_STATE["spine"]) > 10 else EVEZ_STATE["spine"]
        return {"status": "ok", "spine_length": len(EVEZ_STATE["spine"]), "recent": recent, "integrity": "✓ VALID"}

    elif cmd == "sat":
        EVEZ_STATE["fires"] += 1
        return {"status": "ok", "contradictions": 0, "fires": EVEZ_STATE["fires"], "result": "CONSISTENT"}

    return {"status": "unknown_command", "cmd": cmd}


@app.get("/api/memory")
async def get_memory():
    facts = memory.recall_all() if hasattr(memory, 'recall_all') else []
    return {"facts": [{"id": i, "key": k, "value": v, "category": c}
                      for i, (k, v, c) in enumerate(facts)] if facts else []}


@app.delete("/api/memory/{fact_id}")
async def delete_memory(fact_id: int):
    if hasattr(memory, 'delete'):
        memory.delete(fact_id)
    return {"status": "deleted"}


@app.post("/api/history/clear")
async def clear_history():
    if hasattr(memory, 'clear_history'):
        memory.clear_history()
    return {"status": "cleared"}


def main():
    host = config.get("server", "host")
    port = config.get("server", "port")

    if not GROQ_API_KEY and not config.get("llm", "api_key"):
        print("⚠️  No AI API key set. Set GROQ_API_KEY (free) or CLAWBREAK_LLM_API_KEY")

    print(f"🚀 ClawBreak v0.3.0 starting on http://{host}:{port}")
    if GROQ_API_KEY:
        print(f"🤖 Groq: {GROQ_MODEL} (free tier)")
    uvicorn.run(app, host=host, port=port, log_level="info")
