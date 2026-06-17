#!/usr/bin/env python3
"""
EVEZ Sentinel — AI Website Security Scanner
Free tier: 10 scans/day | Pro: unlimited + reports + API
Zero-cost self-hosted. Revenue: Stripe $9/mo Pro tier.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import httpx, hashlib, time, json, re
from typing import Optional

app = FastAPI(title="EVEZ Sentinel", version="1.0.0")

class ScanRequest(BaseModel):
    url: str
    depth: int = 1

class ScanResult(BaseModel):
    url: str
    grade: str  # A-F
    score: int  # 0-100
    headers: dict
    findings: list
    scanned_at: float

# Rate limit store (per-IP, free tier)
scan_store = {}

async def scan_security(url: str) -> dict:
    """Core scanner — checks headers, TLS, known vuln patterns."""
    findings = []
    score = 100
    headers = {}

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url)

        headers = dict(r.headers)

        # Security header checks
        checks = {
            "strict-transport-security": ("HSTS missing", 15),
            "content-security-policy": ("CSP missing", 15),
            "x-content-type-options": ("X-Content-Type-Options missing", 10),
            "x-frame-options": ("X-Frame-Options missing", 10),
            "x-xss-protection": ("X-XSS-Protection missing", 5),
            "referrer-policy": ("Referrer-Policy missing", 5),
            "permissions-policy": ("Permissions-Policy missing", 5),
        }

        for header, (msg, penalty) in checks.items():
            if header not in headers:
                findings.append({"severity": "medium" if penalty >= 10 else "low", "message": msg, "header": header})
                score -= penalty

        # TLS check
        if not url.startswith("https"):
            findings.append({"severity": "critical", "message": "No HTTPS — data transmitted in plaintext"})
            score -= 25

        # Server disclosure
        server = headers.get("server", "")
        if server and len(server) > 2:
            findings.append({"severity": "low", "message": f"Server header discloses: {server}"})
            score -= 3

        # Powered-by disclosure
        powered = headers.get("x-powered-by", "")
        if powered:
            findings.append({"severity": "medium", "message": f"X-Powered-By discloses: {powered}"})
            score -= 5

    except Exception as e:
        findings.append({"severity": "critical", "message": f"Scan failed: {str(e)}"})
        score = 0

    score = max(0, min(100, score))
    grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"

    return ScanResult(url=url, grade=grade, score=score, headers=headers, findings=findings, scanned_at=time.time())

@app.get("/health")
def health():
    return {"status": "ok", "service": "evez-sentinel", "version": "1.0.0"}

@app.post("/v1/scan", response_model=ScanResult)
async def scan(req: ScanRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    key = f"scan:{ip}"
    now = time.time()

    # Free tier: 10 scans/hour
    count = scan_store.get(key, [])
    count = [t for t in count if now - t < 3600]
    if len(count) >= 10:
        raise HTTPException(429, "Free tier: 10 scans/hour. Upgrade to Pro for unlimited.")
    count.append(now)
    scan_store[key] = count

    return await scan_security(req.url)

@app.get("/", response_class=HTMLResponse)
def landing():
    return """<!DOCTYPE html><html><head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>EVEZ Sentinel — AI Security Scanner</title>
    <style>
    body{background:#0a0a0a;color:#e0e0e0;font-family:-apple-system,Roboto,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:20px;}
    h1{color:#00ff88;font-size:2rem;}input{background:#111;border:1px solid #1e1e1e;color:#e0e0e0;padding:12px;border-radius:8px;width:100%;max-width:400px;font-size:16px;}
    button{background:#00ff88;color:#000;border:none;padding:12px 24px;border-radius:8px;font-weight:700;cursor:pointer;margin-top:8px;font-size:16px;}
    button:hover{background:#00cc6a;}#result{margin-top:20px;width:100%;max-width:500px;}.finding{background:#111;border:1px solid #1e1e1e;border-radius:8px;padding:12px;margin:8px 0;}
    .grade{font-size:4rem;font-weight:900;text-align:center;margin:16px 0;}.critical{border-color:#ff4444;}.medium{border-color:#ffaa00;}.low{border-color:#666;}
    </style></head><body>
    <h1>🛡️ EVEZ Sentinel</h1>
    <p>AI Website Security Scanner — Free</p>
    <input id="url" placeholder="https://example.com" value="https://">
    <button onclick="scan()">Scan</button>
    <div id="result"></div>
    <script>
    async function scan(){
      const url=document.getElementById("url").value;
      document.getElementById("result").innerHTML="<p>Scanning...</p>";
      try{const r=await fetch("/v1/scan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url})});
      const d=await r.json();if(d.detail){document.getElementById("result").innerHTML="<p>"+d.detail+"</p>";return;}
      let html='<div class="grade" style="color:'+("#00ff88" if d.grade=="A" else "#88ff00" if d.grade=="B" else "#ffaa00" if d.grade in ["C","D"] else "#ff4444")+' ">'+d.grade+"</div>";
      html+="<p>Score: "+d.score+"/100</p>";
      for(const f of d.findings){html+='<div class="finding '+f.severity+'"><b>'+f.severity.toUpperCase()+"</b>: "+f.message+"</div>";}
      document.getElementById("result").innerHTML=html;
      }catch(e){document.getElementById("result").innerHTML="<p>Error: "+e.message+"</p>";}}
    </script></body></html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
