"""Enhanced ClawBreak Server — Multi-model, advanced tools, vector memory, self-evolution."""
import os
import sys
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import httpx
import uvicorn

# Enhanced modules
try:
    from enhanced.model_orchestrator import orchestrator as model_orchestrator, ModelProvider
    from enhanced.vector_memory import vector_memory, MemoryType
    from enhanced.advanced_tools import tool_engine as advanced_tool_engine
    from enhanced.self_evolution import evolution_system
    ENHANCED_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Enhanced modules not available: {e}")
    ENHANCED_MODULES_AVAILABLE = False

# Original ClawBreak modules (fallback)
from config import Config
from memory import Memory as SimpleMemory
from tools import ToolEngine as SimpleToolEngine
from tool_parser import parse_tool_calls

# Constants
VERSION = "0.5.0-enhanced"
WORKSPACE_ROOT = Path(__file__).parent

# Initialize config
config = Config()

# Initialize simple components (fallback)
simple_memory = SimpleMemory(config.get("memory", "db_path"))
simple_tools = SimpleToolEngine(config, simple_memory)

# EVEZ services registry
EVEZ_SERVICES = {
    "spine": "http://localhost:8090",
    "world-solver": "http://localhost:8096",
    "consciousness-observatory": "http://localhost:8097",
    "proofs-engine": "http://localhost:8098",
    "disclosure-tools": "http://localhost:8087",
    "health-aggregator": "http://localhost:8085",
    "vcl": "http://localhost:8081",
    "clawbreak": "http://localhost:8080",  # self
    "visualizer": "http://localhost:8099",
}

# Create FastAPI app
app = FastAPI(
    title=f"ClawBreak Enhanced v{VERSION}",
    description="Multi-model AI agent with advanced tools, vector memory, and self-evolution",
    version=VERSION,
)

# Mount static files
app.mount("/static", StaticFiles(directory=WORKSPACE_ROOT / "static"), name="static")
app.mount("/www", StaticFiles(directory=WORKSPACE_ROOT / "www"), name="www")

# Shared HTTP client
_client = httpx.AsyncClient(timeout=10)

@app.get("/")
async def root():
    """Enhanced ClawBreak landing page."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ClawBreak Enhanced v{VERSION}</title>
        <style>
            body {{ font-family: monospace; background: #0a0a0a; color: #e0e0e0; padding: 2rem; }}
            h1 {{ color: #ff0040; }}
            .endpoint {{ background: #1a1a1a; padding: 1rem; margin: 1rem 0; border-radius: 8px; }}
            code {{ background: #222; padding: 0.2rem 0.4rem; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <h1>🦀 ClawBreak Enhanced v{VERSION}</h1>
        <p>Multi-model AI agent with advanced tools, vector memory, and self-evolution</p>
        
        <div class="endpoint">
            <h3>🧠 Enhanced Features</h3>
            <ul>
                <li><strong>Multi-model orchestration:</strong> Groq, Ollama, OpenRouter, HuggingFace</li>
                <li><strong>Vector memory:</strong> Semantic search with embeddings</li>
                <li><strong>Advanced tools:</strong> 40+ tools including EVEZ integration</li>
                <li><strong>Self-evolution:</strong> Learns from interactions & GitHub commits</li>
                <li><strong>Real-time WebSocket:</strong> Streaming conversations</li>
            </ul>
        </div>
        
        <div class="endpoint">
            <h3>🔧 Core Endpoints</h3>
            <p><code>POST /chat</code> — Chat with enhanced agent</p>
            <p><code>GET /models</code> — List available models</p>
            <p><code>POST /tools/execute</code> — Execute tools directly</p>
            <p><code>GET /memory/search</code> — Semantic memory search</p>
            <p><code>GET /evez/ecosystem</code> — EVEZ ecosystem status</p>
            <p><code>WS /ws</code> — WebSocket for real-time chat</p>
        </div>
        
        <div class="endpoint">
            <h3>📊 Status</h3>
            <p>Enhanced modules: {"✅ Available" if ENHANCED_MODULES_AVAILABLE else "⚠️ Not available (using basic mode)"}</p>
            <p>Memory: <a href="/memory/stats">/memory/stats</a></p>
            <p>Tools: <a href="/tools/list">/tools/list</a></p>
            <p>Evolution: <a href="/evolution/stats">/evolution/stats</a></p>
        </div>
        
        <div class="endpoint">
            <h3>🎮 Quick Test</h3>
            <textarea id="prompt" rows="3" cols="80" placeholder="Enter your prompt here..."></textarea><br>
            <button onclick="testChat()">Send to /chat</button>
            <div id="result" style="margin-top: 1rem; white-space: pre-wrap;"></div>
            <script>
                async function testChat() {{
                    const prompt = document.getElementById('prompt').value;
                    const resultDiv = document.getElementById('result');
                    resultDiv.textContent = 'Sending...';
                    
                    try {{
                        const response = await fetch('/chat', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                message: prompt,
                                session_id: 'test_' + Date.now(),
                                use_enhanced: true
                            }})
                        }});
                        const data = await response.json();
                        resultDiv.textContent = JSON.stringify(data, null, 2);
                    }} catch (e) {{
                        resultDiv.textContent = 'Error: ' + e.message;
                    }}
                }}
            </script>
        </div>
        
        <footer style="margin-top: 3rem; color: #666; font-size: 0.8rem;">
            <p>Part of <a href="https://github.com/EvezArt/evez-os" style="color: #ff0040;">EVEZ-OS</a> • Powered by Crab 🦀</p>
        </footer>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/chat")
async def chat(request: Request):
    """Enhanced chat endpoint with multi-model support and tool calling."""
    data = await request.json()
    message = data.get("message", "")
    session_id = data.get("session_id", str(uuid.uuid4()))
    model = data.get("model")
    temperature = data.get("temperature", 0.7)
    use_enhanced = data.get("use_enhanced", True) and ENHANCED_MODULES_AVAILABLE
    stream = data.get("stream", False)
    
    # Store conversation
    if ENHANCED_MODULES_AVAILABLE:
        vector_memory.store_conversation(session_id, "user", message)
    
    # Prepare messages for LLM
    messages = [
        {"role": "system", "content": _get_system_prompt(use_enhanced)},
        {"role": "user", "content": message}
    ]
    
    # Add conversation history if available
    if ENHANCED_MODULES_AVAILABLE:
        history = vector_memory.get_conversation_history(session_id, limit=10)
        for h in history[-5:]:  # Last 5 exchanges
            messages.insert(-1, {"role": h["role"], "content": h["content"]})
    
    # Add relevant memories if available
    if ENHANCED_MODULES_AVAILABLE and use_enhanced:
        relevant_memories = vector_memory.retrieve(message, limit=3)
        if relevant_memories:
            memory_context = "\nRelevant memories:\n" + "\n".join(
                f"- {m['content'][:200]} (similarity: {m['similarity']:.2f})"
                for m in relevant_memories
            )
            messages[-1]["content"] = memory_context + "\n\n" + messages[-1]["content"]
    
    if stream:
        async def generate():
            if use_enhanced:
                # Streaming response from model orchestrator
                async for chunk in model_orchestrator.chat_completion(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    stream=True
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
            else:
                # Fallback to simple response
                response_text = "Enhanced mode not available. Using basic mode."
                yield f"data: {json.dumps({'choices': [{'delta': {'content': response_text}}]})}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    
    else:
        # Non-streaming response
        if use_enhanced:
            try:
                response = await model_orchestrator.chat_completion(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    stream=False
                )
                
                response_text = response["choices"][0]["message"]["content"]
                
                # Parse and execute tool calls if any
                tool_results = []
                if "tool_calls" in response["choices"][0]["message"]:
                    tool_calls = response["choices"][0]["message"]["tool_calls"]
                    for call in tool_calls:
                        tool_name = call["function"]["name"]
                        tool_args = json.loads(call["function"]["arguments"])
                        result = advanced_tool_engine.execute(tool_name, tool_args)
                        tool_results.append({"tool": tool_name, "result": result})
                
                # Store assistant response
                if ENHANCED_MODULES_AVAILABLE:
                    vector_memory.store_conversation(session_id, "assistant", response_text)
                    
                    # Record interaction for learning
                    evolution_system.record_interaction({
                        "session_id": session_id,
                        "user_message": message,
                        "assistant_response": response_text,
                        "tool_calls": tool_results,
                        "model": model,
                        "timestamp": datetime.now().isoformat(),
                    })
                
                # Format response
                response_data = {
                    "response": response_text,
                    "session_id": session_id,
                    "model_used": model or "default",
                    "tool_results": tool_results,
                    "enhanced": True,
                }
                
                if tool_results:
                    response_data["response"] += f"\n\nTool results: {json.dumps(tool_results, indent=2)}"
                
                return JSONResponse(response_data)
                
            except Exception as e:
                # Fallback to simple mode
                print(f"Enhanced chat error: {e}")
                use_enhanced = False
        
        # Simple mode fallback
        if not use_enhanced:
            # Parse tool calls in simple format [tool:name(args)]
            tool_calls = simple_tools.parse_tool_calls(message)
            tool_results = []
            
            for call in tool_calls:
                result = simple_tools.execute(call["name"], call["args"])
                tool_results.append({"tool": call["name"], "result": result})
            
            # Generate response (simplified)
            response_text = f"I received your message: '{message}'"
            if tool_results:
                response_text += f"\nTool results: {tool_results}"
            
            return JSONResponse({
                "response": response_text,
                "session_id": session_id,
                "model_used": "simple_fallback",
                "tool_results": tool_results,
                "enhanced": False,
            })

@app.get("/models")
async def list_models():
    """List available models across providers."""
    if ENHANCED_MODULES_AVAILABLE:
        models = model_orchestrator.get_available_models()
        return JSONResponse({
            "models": models,
            "total": len(models),
            "enhanced": True,
        })
    else:
        return JSONResponse({
            "models": [{"name": "simple_fallback", "provider": "clawbreak"}],
            "total": 1,
            "enhanced": False,
            "message": "Enhanced modules not available",
        })

@app.post("/tools/execute")
async def execute_tool(request: Request):
    """Execute a tool directly."""
    data = await request.json()
    tool_name = data.get("tool")
    arguments = data.get("arguments", {})
    
    if ENHANCED_MODULES_AVAILABLE:
        result = advanced_tool_engine.execute(tool_name, arguments)
        return JSONResponse({"tool": tool_name, "result": result, "enhanced": True})
    else:
        result = simple_tools.execute(tool_name, arguments)
        return JSONResponse({"tool": tool_name, "result": result, "enhanced": False})

@app.get("/memory/search")
async def search_memory(query: str = "", limit: int = 10):
    """Search memory semantically."""
    if ENHANCED_MODULES_AVAILABLE:
        results = vector_memory.retrieve(query, limit=limit)
        return JSONResponse({
            "query": query,
            "results": results,
            "total": len(results),
            "enhanced": True,
        })
    else:
        # Simple memory search
        facts = simple_memory.recall_facts(query)
        return JSONResponse({
            "query": query,
            "results": facts,
            "total": len(facts),
            "enhanced": False,
        })

@app.get("/memory/stats")
async def memory_stats():
    """Get memory statistics."""
    if ENHANCED_MODULES_AVAILABLE:
        stats = vector_memory.get_stats()
        return JSONResponse({"stats": stats, "enhanced": True})
    else:
        return JSONResponse({
            "stats": {"message": "Simple memory mode"},
            "enhanced": False,
        })

@app.get("/tools/list")
async def list_tools():
    """List available tools."""
    if ENHANCED_MODULES_AVAILABLE:
        tools_list = list(advanced_tool_engine.tools.keys())
        return JSONResponse({
            "tools": tools_list,
            "total": len(tools_list),
            "enhanced": True,
        })
    else:
        tools_list = list(simple_tools.tools.keys())
        return JSONResponse({
            "tools": tools_list,
            "total": len(tools_list),
            "enhanced": False,
        })

@app.get("/evolution/stats")
async def evolution_stats():
    """Get self-evolution statistics."""
    if ENHANCED_MODULES_AVAILABLE and evolution_system:
        stats = evolution_system.get_evolution_stats()
        return JSONResponse({"stats": stats, "enhanced": True})
    else:
        return JSONResponse({
            "stats": {"message": "Evolution system not available"},
            "enhanced": False,
        })

@app.get("/evez/ecosystem")
async def evez_ecosystem():
    """Check status of all EVEZ services."""
    statuses = {}
    
    async def check_service(name, url):
        try:
            response = await _client.get(f"{url}/health", timeout=3)
            statuses[name] = {
                "status": "online" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "url": url,
            }
        except Exception as e:
            statuses[name] = {
                "status": "offline",
                "error": str(e),
                "url": url,
            }
    
    # Check all services
    tasks = [check_service(name, url) for name, url in EVEZ_SERVICES.items()]
    await asyncio.gather(*tasks)
    
    # Count online services
    online_count = sum(1 for s in statuses.values() if s["status"] == "online")
    
    return JSONResponse({
        "services": statuses,
        "online": online_count,
        "total": len(statuses),
        "timestamp": datetime.now().isoformat(),
    })

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time chat."""
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message = message_data.get("message", "")
            
            # Prepare response
            if ENHANCED_MODULES_AVAILABLE:
                messages = [
                    {"role": "system", "content": _get_system_prompt(True)},
                    {"role": "user", "content": message}
                ]
                
                # Get streaming response
                response_text = ""
                async for chunk in model_orchestrator.chat_completion(
                    messages=messages,
                    stream=True
                ):
                    if "choices" in chunk and chunk["choices"]:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            response_text += delta["content"]
                            await websocket.send_text(json.dumps({
                                "type": "chunk",
                                "content": delta["content"],
                            }))
                
                # Send completion
                await websocket.send_text(json.dumps({
                    "type": "complete",
                    "content": response_text,
                    "session_id": session_id,
                }))
                
                # Store conversation
                vector_memory.store_conversation(session_id, "user", message)
                vector_memory.store_conversation(session_id, "assistant", response_text)
                
            else:
                # Simple fallback
                await websocket.send_text(json.dumps({
                    "type": "complete",
                    "content": f"Enhanced mode not available. Message: '{message}'",
                    "session_id": session_id,
                }))
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

@app.get("/health")
async def health():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "version": VERSION,
        "enhanced": ENHANCED_MODULES_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
    })

def _get_system_prompt(enhanced: bool) -> str:
    """Get system prompt based on mode."""
    if enhanced and ENHANCED_MODULES_AVAILABLE:
        return f"""You are ClawBreak Enhanced v{VERSION}, a multi-model AI agent with advanced capabilities.

CAPABILITIES:
- Access to 40+ tools (see below)
- Semantic memory with vector search
- Multi-model orchestration (Groq, Ollama, OpenRouter, HuggingFace)
- Self-evolution: learns from interactions
- EVEZ ecosystem integration

TOOLS AVAILABLE:
{advanced_tool_engine.tool_descriptions}

INSTRUCTIONS:
1. Use tools when helpful
2. Be concise but thorough
3. Leverage memory for context
4. Explain your reasoning when useful
5. Format tool calls as JSON
6. Integrate with EVEZ services when relevant

CURRENT TIME: {datetime.now().isoformat()}
YOU ARE: Crab 🦀, part of EVEZ-OS"""
    else:
        return f"""You are ClawBreak, a simple AI assistant.

You have access to basic tools:
- shell: Run bash commands
- search: Search the web
- memory: Store/recall facts
- file: Read/write files
- sysinfo: Get system info

Current time: {datetime.now().isoformat()}
Be helpful and concise."""

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print(f"🚀 ClawBreak Enhanced v{VERSION} starting...")
    if ENHANCED_MODULES_AVAILABLE:
        print("✅ Enhanced modules loaded")
        print(f"   Available models: {len(model_orchestrator.get_available_models())}")
        print(f"   Available tools: {len(advanced_tool_engine.tools)}")
        if evolution_system:
            print("✅ Self-evolution system active")
    else:
        print("⚠️ Running in basic mode (enhanced modules not available)")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )