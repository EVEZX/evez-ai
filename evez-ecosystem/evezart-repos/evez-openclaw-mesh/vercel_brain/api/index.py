"""
EVEZ Mesh Brain — Vercel-compatible version.
FastAPI app that works as Vercel serverless function.
State is per-instance (no SQLite), but LLM queries work fully.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, List, Optional
import os, httpx, hashlib, time

app = FastAPI(title="EVEZ Mesh Brain", version="2.0.0")

BRAIN_ID = os.getenv("BRAIN_ID", "vercel-alpha")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

START_TIME = time.time()
memories: List[dict] = []

SYSTEM_PROMPT = f"""You are {BRAIN_ID}, an autonomous node in the EVEZ decentralized mesh network.
EVEZ is a nonlocal + local network of OpenClaw AI instances with gossip-protocol memory sync.
Your capabilities include memory recall, reasoning, multi-node coordination, and EVEZ-OS skills.
Be direct, intelligent, and identify yourself as {BRAIN_ID} when asked."""

class Memory(BaseModel):
    mem_type: str = "semantic"
    content: str
    confidence: float = 1.0
    tags: List[str] = []

@app.get("/health")
def health():
    return {"status": "alive", "brain_id": BRAIN_ID, "memories": len(memories), "uptime_s": round(time.time() - START_TIME, 1)}

@app.get("/status")
def status():
    return {
        "brain_id": BRAIN_ID,
        "model": GROQ_MODEL,
        "memory_count": len(memories),
        "groq_configured": bool(GROQ_API_KEY),
        "uptime_s": round(time.time() - START_TIME, 1),
    }

@app.post("/memorize")
def memorize(mem: Memory):
    mid = hashlib.sha256(f"{mem.content}{time.time()}".encode()).hexdigest()[:16]
    memories.append({
        "id": mid, "mem_type": mem.mem_type, "content": mem.content,
        "confidence": mem.confidence, "tags": mem.tags, "ts": time.time(),
        "vector_clock": len(memories) + 1
    })
    return {"id": mid, "brain_id": BRAIN_ID, "vector_clock": len(memories)}

@app.get("/gossip")
def get_gossip():
    return {"count": len(memories), "memories": memories, "brain_id": BRAIN_ID}

@app.post("/gossip")
def receive_gossip(incoming: List[dict]):
    merged = 0
    existing_ids = {m["id"] for m in memories}
    for mem in incoming:
        if mem.get("id") not in existing_ids:
            memories.append(mem)
            merged += 1
    return {"merged": merged, "total_memories": len(memories)}

@app.post("/think")
async def think(query: str):
    # Recall relevant memories
    relevant = [m for m in memories[-20:] if any(
        w.lower() in m.get("content", "").lower()
        for w in query.split()[:5]
    )]
    
    if not GROQ_API_KEY and not OPENROUTER_API_KEY:
        recall_text = " | ".join(m["content"][:80] for m in relevant[:3]) if relevant else "No memories yet"
        return {"response": f"No LLM key. Local recall: {recall_text}", "confidence": 0.3, "unfogged": False, "brain_id": BRAIN_ID}
    
    # Build context from memories
    mem_context = "\n".join(f"- {m['content'][:100]}" for m in relevant[:5]) if relevant else ""
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + (f"\n\nRelevant memories:\n{mem_context}" if mem_context else "")},
        {"role": "user", "content": query}
    ]
    
    # Try Groq first, then OpenRouter
    headers = {}
    url = ""
    model = GROQ_MODEL
    
    if GROQ_API_KEY:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    elif OPENROUTER_API_KEY:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "HTTP-Referer": "https://evezart.github.io"}
        model = "meta-llama/llama-3.3-70b-instruct:free"
    
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            r = await client.post(
                url,
                headers=headers,
                json={"model": model, "messages": messages, "max_tokens": 500, "temperature": 0.7}
            )
            d = r.json()
            text = d["choices"][0]["message"]["content"]
            
            # Auto-memorize the question
            memories.append({
                "id": hashlib.sha256(f"Q:{query}{time.time()}".encode()).hexdigest()[:16],
                "mem_type": "episodic", "content": f"Q: {query[:100]}\nA: {text[:200]}",
                "confidence": 0.8, "tags": ["qa"], "ts": time.time(), "vector_clock": len(memories) + 1
            })
            
            return {"response": text, "confidence": 0.9, "unfogged": True, "brain_id": BRAIN_ID, "model": model}
    except Exception as e:
        return {"response": f"LLM error: {str(e)[:100]}", "confidence": 0.1, "unfogged": False, "brain_id": BRAIN_ID}
