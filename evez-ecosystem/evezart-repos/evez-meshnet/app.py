#!/usr/bin/env python3
"""
EVEZ MeshNet — Decentralized Node Monitor & Topology Visualizer
Free: self-hosted monitoring | Pro: multi-node mesh + alerts
Revenue: $7/mo Pro mesh monitoring
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import time, hashlib, json

app = FastAPI(title="EVEZ MeshNet", version="1.0.0")

class NodeReport(BaseModel):
    node_id: str
    status: str = "online"
    cpu: float = 0
    mem: float = 0
    disk: float = 0
    uptime: float = 0
    services: list = []

nodes = {}

@app.get("/health")
def health():
    return {"status": "ok", "service": "evez-meshnet", "nodes": len(nodes)}

@app.post("/v1/report")
def report(report: NodeReport):
    nodes[report.node_id] = report.dict()
    nodes[report.node_id]["last_seen"] = time.time()
    return {"ok": True}

@app.get("/v1/nodes")
def list_nodes():
    return {"nodes": list(nodes.values())}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """<!DOCTYPE html><html><head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>EVEZ MeshNet — Node Monitor</title>
    <style>
    body{background:#0a0a0a;color:#e0e0e0;font-family:-apple-system,Roboto,sans-serif;margin:0;padding:20px;}
    h1{color:#ff6600;}.node{background:#111;border:1px solid #1e1e1e;border-radius:12px;padding:16px;margin:12px 0;display:flex;gap:16px;align-items:center;}
    .dot{width:12px;height:12px;border-radius:50%;background:#00ff88;flex-shrink:0;}
    .dot.offline{background:#ff4444;}.bar{height:6px;border-radius:3px;background:#1e1e1e;width:100px;}
    .bar-fill{height:100%;border-radius:3px;background:#00ff88;}
    </style></head><body>
    <h1>🕸️ EVEZ MeshNet</h1>
    <p>Decentralized Node Monitor</p>
    <div id="nodes"></div>
    <script>
    setInterval(()=>{
      fetch("/v1/nodes").then(r=>r.json()).then(data=>{
        const el=document.getElementById("nodes");el.innerHTML="";
        for(const n of data.nodes){
          const cls=n.status==="online"?"dot":"dot offline";
          el.innerHTML+=`<div class="node"><div class="${cls}"></div><div><b>${n.node_id}</b><br>
          CPU: ${n.cpu.toFixed(1)}% | MEM: ${n.mem.toFixed(1)}% | DISK: ${n.disk.toFixed(1)}%<br>
          Services: ${n.services.join(", ")||"none"}</div></div>`;
        }
        if(!data.nodes.length)el.innerHTML="<p>No nodes reporting. POST /v1/report to register.</p>";
      });
    },5000);
    </script></body></html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)
