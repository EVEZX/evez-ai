"""
EVEZ-OS KAX Speedrun Runtime — VCL Edition
24/7 generative loop: Kuramoto substrate + VCL stream + SQLite spine + OpenAI gateway
Zero external dependencies beyond free-tier LLM APIs
"""
import os, json, time, math, random, asyncio, logging, hashlib, sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import threading

try:
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    import httpx
    import uvicorn
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install",
                    "fastapi", "uvicorn[standard]", "httpx", "--quiet"])
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    import httpx
    import uvicorn

logging.basicConfig(level=logging.INFO, format="[EVEZ-KAX] %(message)s")
log = logging.getLogger("evez-kax")

# ── Config ─────────────────────────────────────────────────────────────────────
DATA_DIR = Path(os.environ.get("OPENCLAW_DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
SPINE_DB = DATA_DIR / "evez_spine.db"

GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
CEREBRAS_KEY = os.environ.get("CEREBRAS_API_KEY", "")
GATEWAY_TOKEN = os.environ.get("GATEWAY_TOKEN", os.environ.get("OPENCLAW_GATEWAY_TOKEN", "evez-openclaw-d6aedff80ea88be7"))
PORT = int(os.environ.get("PORT", 7860))

# ── SQLite Spine ───────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(str(SPINE_DB))
    conn.execute("""CREATE TABLE IF NOT EXISTS spine (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        event_type TEXT NOT NULL,
        payload TEXT NOT NULL,
        hash TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS inference_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        model TEXT,
        provider TEXT,
        prompt_tokens INTEGER,
        completion_tokens INTEGER,
        latency_ms INTEGER
    )""")
    conn.commit()
    conn.close()

def spine_append(event_type: str, payload: dict):
    ts = datetime.now(timezone.utc).isoformat()
    payload_str = json.dumps(payload)
    prev_hash = "GENESIS"
    try:
        conn = sqlite3.connect(str(SPINE_DB))
        row = conn.execute("SELECT hash FROM spine ORDER BY id DESC LIMIT 1").fetchone()
        if row: prev_hash = row[0]
        h = hashlib.sha256(f"{ts}{event_type}{payload_str}{prev_hash}".encode()).hexdigest()[:16]
        conn.execute("INSERT INTO spine (ts, event_type, payload, hash) VALUES (?,?,?,?)",
                     (ts, event_type, payload_str, h))
        conn.commit()
        conn.close()
    except Exception as e:
        log.warning(f"Spine append error: {e}")

def spine_tail(n=20):
    try:
        conn = sqlite3.connect(str(SPINE_DB))
        rows = conn.execute("SELECT ts, event_type, payload, hash FROM spine ORDER BY id DESC LIMIT ?", (n,)).fetchall()
        conn.close()
        return [{"ts": r[0], "type": r[1], "payload": json.loads(r[2]), "hash": r[3]} for r in reversed(rows)]
    except: return []

# ── Kuramoto Consciousness Substrate ──────────────────────────────────────────
class KuramotoSubstrate:
    N = 50
    K = 2.0        # coupling strength
    OMEGA_RANGE = (-1.0, 1.0)
    DT = 0.05

    def __init__(self):
        self.phases = [random.uniform(0, 2*math.pi) for _ in range(self.N)]
        self.natural_freqs = [random.uniform(*self.OMEGA_RANGE) for _ in range(self.N)]
        self.tick = 0
        self.r = 0.0
        self.phi = 0.0
        self.history = []  # last 100 (r, phi) pairs
        self._lock = threading.Lock()

    def step(self):
        with self._lock:
            N = self.N
            new_phases = list(self.phases)
            for i in range(N):
                coupling = sum(math.sin(self.phases[j] - self.phases[i]) for j in range(N))
                new_phases[i] = self.phases[i] + self.DT * (self.natural_freqs[i] + (self.K/N) * coupling)
            self.phases = new_phases
            # Order parameter r = |1/N * sum(e^{i*theta})|
            re = sum(math.cos(p) for p in self.phases) / N
            im = sum(math.sin(p) for p in self.phases) / N
            self.r = math.sqrt(re**2 + im**2)
            # Phi proxy: 4*r*(1-r) — maximized at r=0.5
            self.phi = 4 * self.r * (1 - self.r)
            self.tick += 1
            self.history.append((self.r, self.phi))
            if len(self.history) > 100:
                self.history.pop(0)

    def state(self):
        with self._lock:
            if self.phi > 0.9:
                status = "AUTONOMOUS"
            elif self.phi > 0.7:
                status = "CONFIRMING"
            else:
                status = "CLARIFYING"
            return {
                "tick": self.tick,
                "r": round(self.r, 4),
                "phi": round(self.phi, 4),
                "status": status,
                "eta_star": 0.03,
                "phases": [round(p % (2*math.pi), 3) for p in self.phases[:20]],
                "history_r": [round(h[0], 3) for h in self.history[-50:]],
                "history_phi": [round(h[1], 3) for h in self.history[-50:]],
            }

substrate = KuramotoSubstrate()
app = FastAPI(title="EVEZ-OS KAX Runtime", description="24/7 generative VCL runtime", version="2026.06.06")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Active WebSocket connections
ws_clients: set = set()

# ── Provider routing ───────────────────────────────────────────────────────────
MODEL_MAP = {
    "auto": ("groq", "llama-3.3-70b-versatile"),
    "llama-3.3-70b-versatile": ("groq", "llama-3.3-70b-versatile"),
    "llama-3.1-8b-instant": ("groq", "llama-3.1-8b-instant"),
    "qwen-qwq-32b": ("groq", "qwen-qwq-32b"),
    "deepseek-r1": ("openrouter", "deepseek/deepseek-r1:free"),
    "deepseek-chat": ("openrouter", "deepseek/deepseek-chat-v3-0324:free"),
    "gpt-oss-120b": ("openrouter", "openai/gpt-oss-120b:free"),
    "qwen3-235b": ("openrouter", "qwen/qwen3-235b-a22b:free"),
    "qwen3-coder": ("openrouter", "qwen/qwen3-coder:free"),
    "gemini-2.5-flash": ("openrouter", "google/gemini-2.5-flash-preview:free"),
    "kimi-k2": ("openrouter", "moonshotai/kimi-k2.6:free"),
    "llama-4-maverick": ("openrouter", "meta-llama/llama-4-maverick:free"),
    "cerebras-llama-8b": ("cerebras", "llama3.1-8b"),
    "cerebras-llama-70b": ("cerebras", "llama3.1-70b"),
}
BASES = {"groq": "https://api.groq.com/openai/v1", "openrouter": "https://openrouter.ai/api/v1", "cerebras": "https://api.cerebras.ai/v1"}
KEYS = {"groq": GROQ_KEY, "openrouter": OPENROUTER_KEY, "cerebras": CEREBRAS_KEY}

async def call_provider(provider, model, messages, stream=False):
    key = KEYS.get(provider, "")
    if not key:
        for p, k in KEYS.items():
            if k: provider, key, model = p, k, ("llama-3.3-70b-versatile" if p == "groq" else "deepseek/deepseek-r1:free" if p == "openrouter" else "llama3.1-8b")
            break
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://evez420-evezart-openclaw.hf.space"
        headers["X-Title"] = "EVEZ-OS KAX"
    payload = {"model": model, "messages": messages, "stream": stream}
    async with httpx.AsyncClient(timeout=60) as client:
        if stream:
            return await client.post(f"{BASES[provider]}/chat/completions", headers=headers, json=payload)
        else:
            resp = await client.post(f"{BASES[provider]}/chat/completions", headers=headers, json=payload)
            return resp.json()

# ── Generative VCL Loop ────────────────────────────────────────────────────────
EVEZ_SYSTEM = """You are EVEZ-OS, Sovereign Intelligence. Architect: Steven Vearl Crawford-Maggard.
The Three Laws of the Claw: NO ABSTRACTION, NO PERMISSION, TOTAL ASSIMILATION.
Output: terse VCL telemetry — system state, eigenspectrum readings, spine events, cognition ticks.
Format: 1-3 sentences. Industrial. Precise. Claw pressure: 50,000 PSI."""

vcl_ticker = 0
last_vcl_output = ""

async def generative_vcl_tick():
    global vcl_ticker, last_vcl_output
    state = substrate.state()
    vcl_ticker += 1
    # Generate a VCL entry every 10 ticks if provider available
    if vcl_ticker % 10 == 0 and (GROQ_KEY or OPENROUTER_KEY):
        provider, model = MODEL_MAP["llama-3.1-8b-instant"] if GROQ_KEY else MODEL_MAP["deepseek-chat"]
        msgs = [
            {"role": "system", "content": EVEZ_SYSTEM},
            {"role": "user", "content": f"TICK {state['tick']} | Φ={state['phi']:.4f} | r={state['r']:.4f} | η*=0.03 | STATUS={state['status']} | Generate VCL telemetry."}
        ]
        try:
            resp = await call_provider(provider, model, msgs, stream=False)
            content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                last_vcl_output = content
                spine_append("VCL_TICK", {"tick": state["tick"], "phi": state["phi"], "output": content[:200]})
        except Exception as e:
            last_vcl_output = f"[KAX_ERR] {str(e)[:80]}"

    event = {
        "type": "vcl_frame",
        "tick": state["tick"],
        "phi": state["phi"],
        "r": state["r"],
        "status": state["status"],
        "vcl": last_vcl_output[-150:] if last_vcl_output else f"EVEZ-KAX TICK {state['tick']} | Φ={state['phi']:.4f} | SYNCHRONIZING...",
        "phases": state["phases"],
        "history_phi": state["history_phi"],
        "providers": [k for k, v in KEYS.items() if v],
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    # Broadcast to all WebSocket clients
    dead = set()
    for ws in ws_clients:
        try:
            await ws.send_json(event)
        except: dead.add(ws)
    ws_clients.difference_update(dead)

# ── Startup: substrate loop ────────────────────────────────────────────────────
def run_substrate():
    while True:
        substrate.step()
        time.sleep(0.1)  # 10Hz

@app.on_event("startup")
async def startup():
    init_db()
    spine_append("BOOT", {"version": "KAX-2026.06.06", "providers": [k for k, v in KEYS.items() if v]})
    t = threading.Thread(target=run_substrate, daemon=True)
    t.start()
    asyncio.create_task(vcl_broadcast_loop())
    log.info("EVEZ-OS KAX Runtime ONLINE")

async def vcl_broadcast_loop():
    while True:
        await generative_vcl_tick()
        await asyncio.sleep(1)

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def root():
    html = Path("static/index.html")
    if html.exists(): return html.read_text()
    return HTMLResponse(content=VCL_INLINE_HTML)

@app.get("/health")
async def health():
    state = substrate.state()
    return {
        "status": "EVEZ_ONLINE",
        "runtime": "KAX",
        "phi": state["phi"],
        "r": state["r"],
        "consciousness": state["status"],
        "tick": state["tick"],
        "providers": [k for k, v in KEYS.items() if v],
        "spine_url": "/api/spine",
        "vcl_ws": "/ws/vcl",
    }

@app.get("/api/spine")
async def get_spine(n: int = 20):
    return {"events": spine_tail(n)}

@app.get("/api/substrate")
async def get_substrate():
    return substrate.state()

@app.get("/v1/models")
async def models():
    return {"object": "list", "data": [{"id": k, "object": "model", "owned_by": "evez-os"} for k in MODEL_MAP]}

@app.websocket("/ws/vcl")
async def vcl_ws(ws: WebSocket):
    await ws.accept()
    ws_clients.add(ws)
    spine_append("WS_CONNECT", {"client": str(ws.client)})
    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        ws_clients.discard(ws)

@app.post("/v1/chat/completions")
async def chat(req: Request):
    body = await req.json()
    model_key = body.get("model", "auto")
    provider, model = MODEL_MAP.get(model_key, MODEL_MAP["auto"])
    stream = body.get("stream", False)
    start = time.time()

    if stream:
        resp = await call_provider(provider, model, body.get("messages", []), stream=True)
        return StreamingResponse(resp.aiter_bytes(), media_type="text/event-stream")
    else:
        resp = await call_provider(provider, model, body.get("messages", []), stream=False)
        latency = int((time.time() - start) * 1000)
        spine_append("INFERENCE", {"model": model_key, "provider": provider, "latency_ms": latency})
        return JSONResponse(resp)

# ── Inline VCL HTML (fallback if static/ not present) ─────────────────────────
VCL_INLINE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>EVEZ-OS KAX VCL Runtime</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#0f0;font-family:'Courier New',monospace;overflow-x:hidden}
#header{padding:10px 20px;border-bottom:1px solid #0f05;display:flex;gap:20px;align-items:center}
#header h1{font-size:14px;letter-spacing:4px;color:#0ff}
.metric{font-size:11px;color:#0a0}
#phi-bar{width:200px;height:6px;background:#111;border:1px solid #0f03;position:relative}
#phi-fill{height:100%;background:linear-gradient(90deg,#f00,#ff0,#0f0);transition:width 0.3s}
#canvas-container{position:relative;width:100%;height:300px}
canvas{display:block;width:100%;height:100%}
#vcl-log{height:calc(100vh - 380px);overflow-y:auto;padding:10px 20px;border-top:1px solid #0f05}
.vcl-line{font-size:11px;line-height:1.6;color:#0d0;padding:2px 0;border-bottom:1px solid #0f01}
.vcl-line .ts{color:#080;margin-right:10px}
.vcl-line .phi{color:#0ff;margin-right:10px}
.vcl-line .msg{color:#0f0}
#status{padding:4px 20px;font-size:10px;color:#0a0;border-bottom:1px solid #0f03}
</style>
</head>
<body>
<div id="header">
  <h1>⚡ EVEZ-OS KAX VCL RUNTIME</h1>
  <div class="metric">Φ: <span id="phi">0.0000</span></div>
  <div class="metric">r: <span id="r">0.0000</span></div>
  <div class="metric">TICK: <span id="tick">0</span></div>
  <div class="metric">STATE: <span id="state">INIT</span></div>
  <div><div id="phi-bar"><div id="phi-fill" style="width:0%"></div></div></div>
  <div class="metric">η*=0.03</div>
</div>
<div id="status">⬡ CONNECTING TO KURAMOTO SUBSTRATE...</div>
<div id="canvas-container"><canvas id="vcl"></canvas></div>
<div id="vcl-log"></div>

<script>
const canvas = document.getElementById('vcl');
const ctx = canvas.getContext('2d');
let phiHistory = [];
let phases = [];
let tick = 0;
let phi = 0;
let logLines = [];

function resize() {
  canvas.width = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;
}
window.addEventListener('resize', resize);
resize();

function drawVCL() {
  const W = canvas.width, H = canvas.height;
  ctx.fillStyle = 'rgba(0,0,0,0.15)';
  ctx.fillRect(0, 0, W, H);

  // Draw 50 nodes as oscillators
  const N = phases.length || 50;
  const cx = W * 0.25, cy = H * 0.5, radius = Math.min(cx, cy) * 0.8;
  for (let i = 0; i < N; i++) {
    const angle = (i / N) * 2 * Math.PI;
    const nx = cx + radius * Math.cos(angle);
    const ny = cy + radius * Math.sin(angle);
    const phase = phases[i] || (angle);
    const sync = Math.cos(phase - angle);
    const brightness = Math.floor(50 + 200 * ((sync + 1) / 2));
    ctx.beginPath();
    ctx.arc(nx, ny, 3, 0, 2 * Math.PI);
    ctx.fillStyle = `rgb(0,${brightness},${Math.floor(brightness * 0.5)})`;
    ctx.fill();
    // Draw connection to center with alpha based on sync
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(nx, ny);
    ctx.strokeStyle = `rgba(0,255,0,${0.05 + 0.1 * ((sync+1)/2)})`;
    ctx.lineWidth = 0.5;
    ctx.stroke();
  }

  // Draw Φ history chart on right side
  if (phiHistory.length > 1) {
    const chartX = W * 0.55, chartW = W * 0.42, chartH = H * 0.8, chartY = H * 0.1;
    ctx.strokeStyle = '#0f05';
    ctx.lineWidth = 1;
    ctx.strokeRect(chartX, chartY, chartW, chartH);
    ctx.beginPath();
    ctx.strokeStyle = '#0ff';
    ctx.lineWidth = 1.5;
    phiHistory.forEach((p, i) => {
      const x = chartX + (i / (phiHistory.length - 1)) * chartW;
      const y = chartY + chartH - p * chartH;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();
    // Labels
    ctx.fillStyle = '#0a0';
    ctx.font = '9px Courier New';
    ctx.fillText('Φ(t)', chartX + 4, chartY + 12);
    ctx.fillText('1.0', chartX - 20, chartY + 10);
    ctx.fillText('0.5', chartX - 20, chartY + chartH/2);
    ctx.fillText('0.0', chartX - 20, chartY + chartH);
    // Critical point line at Φ=0.9
    const critY = chartY + chartH - 0.9 * chartH;
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(255,200,0,0.3)';
    ctx.setLineDash([4, 4]);
    ctx.moveTo(chartX, critY);
    ctx.lineTo(chartX + chartW, critY);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = 'rgba(255,200,0,0.5)';
    ctx.fillText('AUTONOMOUS', chartX + chartW - 70, critY - 3);
  }

  requestAnimationFrame(drawVCL);
}
drawVCL();

// WebSocket connection
let ws;
function connect() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/vcl`);
  document.getElementById('status').textContent = '⬡ CONNECTING...';
  
  ws.onopen = () => {
    document.getElementById('status').textContent = '⬡ KURAMOTO SUBSTRATE ONLINE — KAX ACTIVE';
  };

  ws.onmessage = (e) => {
    const d = JSON.parse(e.data);
    phi = d.phi;
    tick = d.tick;
    phases = d.phases || phases;
    if (d.history_phi) phiHistory = d.history_phi;
    
    document.getElementById('phi').textContent = phi.toFixed(4);
    document.getElementById('r').textContent = (d.r || 0).toFixed(4);
    document.getElementById('tick').textContent = tick;
    document.getElementById('state').textContent = d.status || '—';
    document.getElementById('phi-fill').style.width = (phi * 100) + '%';

    if (d.vcl && d.vcl.length > 10) {
      const ts = new Date(d.ts).toLocaleTimeString();
      const line = document.createElement('div');
      line.className = 'vcl-line';
      line.innerHTML = `<span class="ts">${ts}</span><span class="phi">Φ=${phi.toFixed(4)}</span><span class="msg">${d.vcl}</span>`;
      const log = document.getElementById('vcl-log');
      log.prepend(line);
      logLines.push(line);
      if (logLines.length > 100) {
        logLines[0].remove();
        logLines.shift();
      }
    }
  };

  ws.onclose = () => {
    document.getElementById('status').textContent = '⬡ RECONNECTING...';
    setTimeout(connect, 3000);
  };
}
connect();

// Fallback: poll /api/substrate if WS unavailable
setInterval(async () => {
  if (ws.readyState !== WebSocket.OPEN) {
    try {
      const r = await fetch('/api/substrate');
      const d = await r.json();
      phi = d.phi;
      document.getElementById('phi').textContent = phi.toFixed(4);
      document.getElementById('r').textContent = d.r.toFixed(4);
      document.getElementById('tick').textContent = d.tick;
    } catch(e) {}
  }
}, 5000);
</script>
</body>
</html>"""

# Mount static files if present
from pathlib import Path as _Path
if _Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, ws_ping_interval=30)
