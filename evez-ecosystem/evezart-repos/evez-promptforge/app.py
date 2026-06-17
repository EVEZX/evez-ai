#!/usr/bin/env python3
"""
EVEZ PromptForge — AI Prompt Marketplace & Optimizer
Free: community prompts | Pro: AI optimization + analytics
Revenue: $5/mo Pro, prompt sales commission 30%
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import time, json

app = FastAPI(title="EVEZ PromptForge", version="1.0.0")

PROMPTS = [
    {"id": "evez-consciousness-1", "name": "Spectral Consciousness Probe", "category": "research", "author": "EVEZ",
     "prompt": "Analyze this system as a causal graph. Compute eigenspectrum, identify negative eigenvalues as structural gaps. Apply 37% theorem.", "rating": 4.9, "uses": 342},
    {"id": "evez-agent-1", "name": "Autonomous Agent Bootstrap", "category": "agents", "author": "EVEZ",
     "prompt": "You are an autonomous agent with tools: shell, search, memory, file. Execute tasks independently. Report results.", "rating": 4.8, "uses": 1205},
    {"id": "evez-code-1", "name": "Zero-Cost SaaS Builder", "category": "coding", "author": "EVEZ",
     "prompt": "Build a complete SaaS app: FastAPI backend, vanilla JS frontend, SQLite storage. Free-tier deployable. Include rate limiting and auth.", "rating": 4.7, "uses": 891},
    {"id": "evez-forensic-1", "name": "Document Corpus Forensics", "category": "research", "author": "EVEZ",
     "prompt": "Run eigenforensics on the document corpus. Build reference graph, compute Laplacian eigenspectrum, flag structural holes via 37% theorem.", "rating": 5.0, "uses": 67},
]

@app.get("/health")
def health():
    return {"status": "ok", "service": "evez-promptforge", "prompts": len(PROMPTS)}

@app.get("/v1/prompts")
def list_prompts(category: Optional[str] = None):
    results = PROMPTS if not category else [p for p in PROMPTS if p["category"] == category]
    return {"prompts": results}

@app.get("/v1/prompts/{prompt_id}")
def get_prompt(prompt_id: str):
    for p in PROMPTS:
        if p["id"] == prompt_id:
            return p
    return JSONResponse({"error": "not found"}, status_code=404)

@app.get("/", response_class=HTMLResponse)
def landing():
    return """<!DOCTYPE html><html><head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>EVEZ PromptForge — AI Prompt Marketplace</title>
    <style>
    body{background:#0a0a0a;color:#e0e0e0;font-family:-apple-system,Roboto,sans-serif;margin:0;padding:20px;}
    h1{color:#00b8ff;}.card{background:#111;border:1px solid #1e1e1e;border-radius:12px;padding:16px;margin:12px 0;}
    .tag{background:#1a2a3a;color:#00b8ff;padding:2px 8px;border-radius:12px;font-size:12px;}
    .stars{color:#ffaa00;}
    button{background:#00b8ff;color:#000;border:none;padding:8px 16px;border-radius:8px;cursor:pointer;font-weight:700;}
    </style></head><body>
    <h1>⚡ EVEZ PromptForge</h1>
    <p>AI Prompt Marketplace — Community & Pro</p>
    <div id="prompts"></div>
    <script>
    fetch("/v1/prompts").then(r=>r.json()).then(data=>{
      const el=document.getElementById("prompts");
      for(const p of data.prompts){
        el.innerHTML+=`<div class="card"><h3>${p.name}</h3><span class="tag">${p.category}</span>
        <span class="stars">★${p.rating}</span> · ${p.uses} uses<p style="margin-top:8px">${p.prompt.substring(0,120)}...</p>
        <button onclick="navigator.clipboard.writeText(\`${p.prompt.replace(/`/g,"'")}\`)">Copy</button></div>`;
      }
    });
    </script></body></html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
