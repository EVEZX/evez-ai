"""ClawBreak - FastAPI server with chat, tools, memory, and web UI."""
import os
import sys
import json
import time
import uuid
import asyncio
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

# Init
config = Config()
memory = Memory(config.get("memory", "db_path"))
tools = ToolEngine(config, memory)

app = FastAPI(title="ClawBreak", version="0.1.0")

# --- LLM Client ---

async def chat_completion(messages, stream=False):
    """Call the LLM API."""
    api_key = config.get("llm", "api_key")
    base_url = config.get("llm", "base_url")
    model = config.get("llm", "model")

    if not api_key:
        return {"error": "No API key configured. Set CLAWBREAK_LLM_API_KEY or add to config.yaml"}

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

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"LLM API error {e.response.status_code}: {e.response.text[:500]}"}
        except Exception as e:
            return {"error": f"LLM request failed: {e}"}


async def chat_completion_stream(messages):
    """Stream chat completion chunks."""
    api_key = config.get("llm", "api_key")
    base_url = config.get("llm", "base_url")
    model = config.get("llm", "model")

    if not api_key:
        yield f"data: {json.dumps({'error': 'No API key'})}\n\n"
        return

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


async def process_message(user_message: str, session_id: str = "default") -> str:
    """Process a user message through the LLM with tool execution."""
    # Store user message
    memory.store_message("user", user_message, session_id)

    # Build context
    history = memory.get_messages(session_id, limit=config.get("memory", "max_context_messages"))
    messages = [{"role": "system", "content": config.get("system_prompt")}]
    messages.extend(history)

    # Call LLM
    response = await chat_completion(messages)

    if "error" in response:
        return f"Error: {response['error']}"

    try:
        assistant_msg = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return f"Error: Unexpected API response format"

    # Check for tool calls
    tool_calls = parse_tool_calls(assistant_msg)
    if tool_calls:
        tool_results = []
        for tc in tool_calls:
            result = tools.execute(tc["name"], tc["args"])
            tool_results.append(f"[tool:{tc['name']} result]\n{json.dumps(result, indent=2, ensure_ascii=False)[:2000]}")

        # Send tool results back to LLM for a proper response
        tool_context = "\n\n".join(tool_results)
        messages.append({"role": "assistant", "content": assistant_msg})
        messages.append({"role": "user", "content": f"Tool execution results:\n{tool_context}\n\nNow respond to the user based on these results."})

        response2 = await chat_completion(messages)
        if "error" not in response2:
            try:
                assistant_msg = response2["choices"][0]["message"]["content"]
            except:
                pass

    # Store and return
    memory.store_message("assistant", assistant_msg, session_id)
    memory.cleanup_old_messages(session_id)
    return assistant_msg


# --- Routes ---

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "model": config.get("llm", "model"),
        "memory_facts": len(memory.list_facts(limit=9999)),
        "uptime": time.time(),
    }


@app.post("/chat")
async def chat(request: Request):
    """Non-streaming chat endpoint."""
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id", "default")

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    reply = await process_message(message, session_id)
    return {"reply": reply, "session_id": session_id}


@app.post("/chat/stream")
async def chat_stream(request: Request):
    """Streaming chat endpoint."""
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id", "default")

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    memory.store_message("user", message, session_id)
    history = memory.get_messages(session_id, limit=config.get("memory", "max_context_messages"))
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
            memory.store_message("assistant", "".join(full_response), session_id)

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


# Serve web UI
STATIC_DIR = Path(__file__).parent / "static"

@app.get("/")
async def serve_ui():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return HTMLResponse(index.read_text())
    return HTMLResponse("<h1>ClawBreak</h1><p>Web UI not found. Use the API.</p>")


@app.get("/config")
async def get_config():
    """Get current config (redacting API key)."""
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


def main():
    host = config.get("server", "host")
    port = config.get("server", "port")

    # Ensure API key is set
    if not config.get("llm", "api_key"):
        print("⚠️  No LLM API key set. Set CLAWBREAK_LLM_API_KEY or add to config.yaml")

    print(f"🚀 ClawBreak starting on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
