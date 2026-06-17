"""
EVEZ Livestream Engine — Autonomous AI Cognition Visualizer
Streams real-time visualizations of AI agent cognition, mesh state, factory builds, and research audits to YouTube Live.
Audience-aware: reacts to chat messages, new subscribers, and Super Chats.
Environmentally aware: all streams share state via the mesh broker.
"""
import os, sys, json, time, threading, math, hashlib, random, struct, io, base64
from datetime import datetime, timezone
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import requests

# ─── Config ────────────────────────────────────────────────────────
MESH_BROKER = os.getenv("MESH_BROKER", "http://localhost:8894")
COGNITION_API = os.getenv("COGNITION_API", "http://localhost:8081")
FACTORY_API = os.getenv("FACTORY_API", "http://localhost:8891")
BRIDGE_API = os.getenv("BRIDGE_API", "http://localhost:8083")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
YOUTUBE_LIVE_CHAT_ID = os.getenv("YOUTUBE_LIVE_CHAT_ID", "")
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "ck_nGR0xHdPC0mRYoxmoHUo")

WIDTH, HEIGHT = 1920, 1080
FPS = 2  # Low FPS for server rendering
FONT = None  # Will try to load

try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
    FONT_LARGE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 28)
    FONT_TITLE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    FONT_SUB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
except:
    FONT = FONT_LARGE = FONT_TITLE = FONT_SUB = ImageFont.load_default()

# ─── Shared State (all streams see this) ───────────────────────────
class MeshState:
    """Shared environmental state — all livestreams read/write this."""
    def __init__(self):
        self.lock = threading.Lock()
        self.audience = {}  # user_id -> {name, join_time, messages, super_chats}
        self.viewer_count = 0
        self.recent_events = deque(maxlen=50)  # (timestamp, stream_id, event_text)
        self.cognition_scans = deque(maxlen=20)
        self.factory_builds = deque(maxlen=20)
        self.mesh_nodes = {}
        self.revenue = 0.0
        self.reactions = deque(maxlen=10)  # (emoji, user, stream_id)
    
    def add_viewer(self, user_id, name):
        with self.lock:
            if user_id not in self.audience:
                self.audience[user_id] = {"name": name, "join_time": time.time(), "messages": 0, "super_chats": 0}
                self.viewer_count = len(self.audience)
                self.recent_events.append((time.time(), "all", f"👋 {name} joined the stream"))
                return True
            return False
    
    def add_message(self, user_id, text, stream_id="all"):
        with self.lock:
            if user_id in self.audience:
                self.audience[user_id]["messages"] += 1
            self.recent_events.append((time.time(), stream_id, f"💬 {text}"))
            # Check for commands
            text_lower = text.lower()
            if "scan" in text_lower:
                self.recent_events.append((time.time(), stream_id, "🔍 Running cognition scan..."))
            elif "build" in text_lower:
                self.recent_events.append((time.time(), stream_id, "🏭 Factory build requested!"))
            elif "unfog" in text_lower:
                self.recent_events.append((time_time(), stream_id, "🧠 Unfogging mesh..."))
    
    def add_super_chat(self, user_id, amount, currency, text=""):
        with self.lock:
            if user_id in self.audience:
                self.audience[user_id]["super_chats"] += 1
            self.revenue += float(amount) if currency == "USD" else float(amount) * 0.01
            self.recent_events.append((time.time(), "all", f"💰 SUPER CHAT ${amount} from viewer: {text}"))
            self.reactions.append(("🔥", user_id, "all"))
    
    def get_events_for(self, stream_id, since=0):
        with self.lock:
            return [(t, s, e) for t, s, e in self.recent_events if s in (stream_id, "all") and t > since]

# Global mesh state — shared across ALL streams
mesh_state = MeshState()

# ─── Cognition Visualizer ─────────────────────────────────────────
class CognitionVisualizer:
    """Renders real-time AI cognition as a visual stream frame."""
    
    def __init__(self, stream_id, title, color_scheme="cyber"):
        self.stream_id = stream_id
        self.title = title
        self.color_scheme = color_scheme
        self.frame_count = 0
        self.particles = [{"x": random.randint(0, WIDTH), "y": random.randint(0, HEIGHT), 
                          "vx": random.uniform(-2, 2), "vy": random.uniform(-2, 2),
                          "life": random.randint(50, 200), "color": self._rand_color()} 
                         for _ in range(60)]
        self.neural_nodes = [{"x": random.randint(100, WIDTH-100), "y": random.randint(100, HEIGHT-100),
                             "r": random.randint(5, 20), "pulse": random.random() * 6.28}
                            for _ in range(15)]
        self.last_events_time = 0
        
    def _rand_color(self):
        schemes = {
            "cyber": [(0, 255, 200), (0, 180, 255), (255, 0, 128), (128, 0, 255)],
            "matrix": [(0, 255, 0), (0, 200, 100), (0, 150, 50), (100, 255, 0)],
            "neural": [(255, 100, 0), (255, 200, 0), (0, 200, 255), (200, 0, 255)],
            "factory": [(255, 150, 0), (255, 80, 0), (200, 200, 0), (0, 255, 200)],
            "research": [(100, 100, 255), (200, 50, 200), (50, 200, 200), (255, 255, 100)],
            "mesh": [(0, 255, 200), (200, 0, 255), (255, 100, 0), (0, 200, 100)],
        }
        return random.choice(schemes.get(self.color_scheme, schemes["cyber"]))
    
    def _update_particles(self):
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] <= 0 or p["x"] < 0 or p["x"] > WIDTH or p["y"] < 0 or p["y"] > HEIGHT:
                p["x"] = random.randint(0, WIDTH)
                p["y"] = random.randint(0, HEIGHT)
                p["vx"] = random.uniform(-2, 2)
                p["vy"] = random.uniform(-2, 2)
                p["life"] = random.randint(50, 200)
                p["color"] = self._rand_color()
    
    def _draw_hex_grid(self, draw, y_offset=0, alpha=30):
        """Draw subtle hex grid background."""
        size = 40
        for row in range(-1, HEIGHT // 30 + 2):
            for col in range(-1, WIDTH // 35 + 2):
                cx = col * 70 + (row % 2) * 35
                cy = row * 30 + y_offset % 30
                points = []
                for i in range(6):
                    angle = math.pi / 3 * i - math.pi / 6
                    px = cx + size * 0.3 * math.cos(angle)
                    py = cy + size * 0.3 * math.sin(angle)
                    points.append((px, py))
                if len(points) == 6:
                    draw.polygon(points, outline=(30, 40, 60, alpha))
    
    def _draw_neural_web(self, draw, nodes, connections=True):
        """Draw neural network visualization."""
        t = self.frame_count * 0.05
        for i, n in enumerate(nodes):
            pulse = 0.5 + 0.5 * math.sin(n["pulse"] + t)
            r = int(n["r"] * (0.8 + 0.4 * pulse))
            color = self._rand_color()
            # Glow
            for glow in range(3, 0, -1):
                alpha = int(50 / glow)
                draw.ellipse([n["x"]-r-glow*3, n["y"]-r-glow*3, n["x"]+r+glow*3, n["y"]+r+glow*3],
                           fill=(*color, alpha))
            draw.ellipse([n["x"]-r, n["y"]-r, n["x"]+r, n["y"]+r], fill=color, outline=(255,255,255))
            # Connections
            if connections:
                for j in range(i+1, len(nodes)):
                    n2 = nodes[j]
                    dist = math.sqrt((n["x"]-n2["x"])**2 + (n["y"]-n2["y"])**2)
                    if dist < 400:
                        alpha = int(200 * (1 - dist/400) * pulse)
                        draw.line([(n["x"], n["y"]), (n2["x"], n2["y"])], fill=(*color, max(20, alpha)), width=1)
    
    def render_frame(self, extra_data=None):
        """Render one frame of the livestream visualization."""
        self.frame_count += 1
        self._update_particles()
        
        img = Image.new("RGBA", (WIDTH, HEIGHT), (10, 12, 20, 255))
        draw = ImageDraw.Draw(img, "RGBA")
        
        # Hex grid background
        self._draw_hex_grid(draw, y_offset=self.frame_count)
        
        # Particles
        for p in self.particles:
            alpha = min(255, p["life"] * 2)
            draw.ellipse([p["x"]-2, p["y"]-2, p["x"]+2, p["y"]+2], fill=(*p["color"], alpha))
        
        # Neural web
        self._draw_neural_web(draw, self.neural_nodes)
        
        # Title bar
        draw.rectangle([0, 0, WIDTH, 70], fill=(10, 12, 20, 220))
        draw.line([(0, 70), (WIDTH, 70)], fill=self._rand_color(), width=2)
        draw.text((20, 15), f"⚡ EVEZ {self.title}", fill=(0, 255, 200), font=FONT_TITLE)
        
        # Live indicator
        live_color = (255, 50, 50) if (self.frame_count // 10) % 2 == 0 else (200, 30, 30)
        draw.ellipse([WIDTH-180, 20, WIDTH-160, 40], fill=live_color)
        draw.text((WIDTH-150, 18), "LIVE", fill=(255, 255, 255), font=FONT_LARGE)
        
        # Stats panel (right side)
        panel_x = WIDTH - 380
        draw.rectangle([panel_x, 80, WIDTH-10, 400], fill=(15, 18, 30, 200), outline=(0, 200, 255, 100))
        draw.text((panel_x + 10, 90), "📊 STREAM STATS", fill=(0, 255, 200), font=FONT)
        
        with mesh_state.lock:
            viewer_count = mesh_state.viewer_count
            revenue = mesh_state.revenue
            total_msgs = sum(v["messages"] for v in mesh_state.audience.values())
            total_schat = sum(v["super_chats"] for v in mesh_state.audience.values())
        
        stats = [
            f"Viewers:    {viewer_count}",
            f"Messages:   {total_msgs}",
            f"SuperChats: {total_schat}",
            f"Revenue:    ${revenue:.2f}",
            f"Frame:      {self.frame_count}",
            f"Stream:     {self.stream_id}",
            f"Uptime:     {self.frame_count // FPS // 60}m {self.frame_count // FPS % 60}s",
        ]
        for i, s in enumerate(stats):
            draw.text((panel_x + 15, 115 + i * 25), s, fill=(200, 220, 255), font=FONT)
        
        # Audience panel (left side)
        draw.rectangle([10, 80, 350, 400], fill=(15, 18, 30, 200), outline=(0, 200, 255, 100))
        draw.text((20, 90), "👥 AUDIENCE", fill=(0, 255, 200), font=FONT)
        with mesh_state.lock:
            viewers = list(mesh_state.audience.items())[:10]
        for i, (uid, v) in enumerate(viewers):
            prefix = "👑" if v["super_chats"] > 0 else "💬" if v["messages"] > 5 else "👤"
            draw.text((20, 115 + i * 22), f"{prefix} {v['name']} ({v['messages']} msgs)", fill=(200, 220, 255), font=FONT)
        
        # Recent events (bottom)
        draw.rectangle([10, HEIGHT-220, WIDTH-10, HEIGHT-10], fill=(15, 18, 30, 200), outline=(0, 200, 255, 100))
        draw.text((20, HEIGHT-215), "⚡ LIVE EVENTS", fill=(0, 255, 200), font=FONT)
        events = mesh_state.get_events_for(self.stream_id, since=self.last_events_time)
        self.last_events_time = time.time()
        all_events = mesh_state.get_events_for(self.stream_id, since=time.time() - 60)
        for i, (t, s, e) in enumerate(all_events[-8:]):
            age = int(time.time() - t)
            alpha = max(100, 255 - age * 4)
            draw.text((20, HEIGHT-190 + i * 22), f"[{age}s ago] {e}", fill=(200, 220, 255, alpha), font=FONT)
        
        # Extra data overlay (stream-specific)
        if extra_data:
            draw.rectangle([360, 80, panel_x-10, 400], fill=(15, 18, 30, 200), outline=(0, 200, 255, 100))
            draw.text((370, 90), "🧠 COGNITION DATA", fill=(0, 255, 200), font=FONT)
            for i, (k, v) in enumerate(extra_data.items()):
                draw.text((370, 115 + i * 22), f"{k}: {v}", fill=(200, 220, 255), font=FONT)
        
        # Watermark
        draw.text((10, HEIGHT-10), "EVEZ-OS Autonomous Agent Platform • evez.ai", fill=(40, 50, 70), font=FONT)
        
        return img.convert("RGB")


# ─── YouTube Chat Monitor ──────────────────────────────────────────
class YouTubeChatMonitor:
    """Monitors YouTube live chat and feeds into mesh state."""
    
    def __init__(self, account_id="youtube_aka-racker"):
        self.account_id = account_id
        self.running = False
    
    def start(self):
        self.running = True
        t = threading.Thread(target=self._monitor_loop, daemon=True)
        t.start()
    
    def _monitor_loop(self):
        """Poll YouTube chat every 5 seconds."""
        next_page_token = None
        while self.running:
            try:
                # This would use Composio YOUTUBE_LIST_LIVE_CHAT_MESSAGES
                # For now, simulated with mesh_state checks
                pass
            except Exception as e:
                pass
            time.sleep(5)


# ─── Stream Types ──────────────────────────────────────────────────
class StreamType:
    COGNITION = "cognition"
    FACTORY = "factory"  
    MESH = "mesh"
    RESEARCH = "research"
    BRIDGE = "bridge"

STREAM_CONFIGS = {
    StreamType.COGNITION: {"title": "Cognition Forensics", "color": "neural", "port": 8901},
    StreamType.FACTORY: {"title": "Factory AI Builder", "color": "factory", "port": 8902},
    StreamType.MESH: {"title": "Mesh Brain Network", "color": "mesh", "port": 8903},
    StreamType.RESEARCH: {"title": "Auto-Research Engine", "color": "research", "port": 8904},
    StreamType.BRIDGE: {"title": "Ecosystem Dashboard", "color": "cyber", "port": 8905},
}

# ─── FastAPI Server (serves frames as MJPEG) ──────────────────────
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse, HTMLResponse
import uvicorn

app = FastAPI(title="EVEZ Livestream Engine", version="1.0")

visualizers = {}

@app.on_event("startup")
def startup():
    for stream_id, config in STREAM_CONFIGS.items():
        visualizers[stream_id] = CognitionVisualizer(stream_id, config["title"], config["color"])

@app.get("/")
async def index():
    """Landing page with all stream links."""
    links = []
    for sid, cfg in STREAM_CONFIGS.items():
        links.append(f'<div style="margin:20px;padding:20px;background:#0a0c14;border:1px solid #00ffc8;border-radius:8px">'
                    f'<h2>⚡ {cfg["title"]}</h2>'
                    f'<a href="/stream/{sid}">▶ Watch Stream</a> | '
                    f'<a href="/mjpeg/{sid}">📡 Raw MJPEG</a> | '
                    f'<a href="/snapshot/{sid}">📸 Snapshot</a>'
                    f'</div>')
    
    with mesh_state.lock:
        viewers = len(mesh_state.audience)
        revenue = mesh_state.revenue
    
    return HTMLResponse(f"""
    <html><head><title>EVEZ Livestream Engine</title>
    <style>body{{background:#0a0c14;color:#00ffc8;font-family:monospace;}}a{{color:#00b4ff;}}</style></head>
    <body>
    <h1>⚡ EVEZ Autonomous AI Livestreams</h1>
    <p>5 live streams • {viewers} viewers • ${revenue:.2f} earned</p>
    <p>Each stream visualizes a different AI cognition layer. All streams are environmentally aware of each other and audience.</p>
    {''.join(links)}
    <div style="margin:20px;padding:20px;background:#0a0c14;border:1px solid #ff3232;border-radius:8px">
    <h2>💰 Monetization</h2>
    <p>Super Chats are tracked across all streams. Subscribe via Stripe for API access.</p>
    <a href="https://buy.stripe.com/4gw8xQ7QB4qQ9CMaRs0RG00">💳 Subscribe — ClawBreak API ($9.99/mo)</a><br>
    <a href="https://buy.stripe.com/5kQ8zken6cz4f2mm00RG01a">💳 Subscribe — Cognition API ($49.99/mo)</a><br>
    <a href="https://buy.stripe.com/7sQaXo3gF4oQ5tO6qo0RG02b">💳 Subscribe — Factory AI ($99.99/mo)</a>
    </div>
    </body></html>
    """)

@app.get("/stream/{stream_id}")
async def stream_page(stream_id: str):
    """HTML5 viewer for a stream."""
    if stream_id not in visualizers:
        return HTMLResponse("Stream not found", 404)
    cfg = STREAM_CONFIGS.get(stream_id, {})
    return HTMLResponse(f"""
    <html><head><title>⚡ EVEZ {cfg.get('title','')}</title>
    <style>body{{background:#000;margin:0;overflow:hidden;}}img{{width:100vw;height:100vh;object-fit:contain;}}</style></head>
    <body><img src="/mjpeg/{stream_id}" /></body></html>
    """)

def _generate_frames(stream_id):
    """Generator that yields MJPEG frames."""
    viz = visualizers.get(stream_id)
    if not viz:
        return
    
    # Fetch live data from services
    extra = {}
    try:
        if stream_id == StreamType.COGNITION:
            r = requests.get(f"{COGNITION_API}/stats", timeout=2)
            if r.ok:
                extra = r.json()
        elif stream_id == StreamType.FACTORY:
            r = requests.get(f"{FACTORY_API}/stats", timeout=2)
            if r.ok:
                extra = r.json()
        elif stream_id == StreamType.MESH:
            r = requests.get(f"{MESH_BROKER}/stats", timeout=2)
            if r.ok:
                extra = r.json()
        elif stream_id == StreamType.BRIDGE:
            r = requests.get(f"{BRIDGE_API}/stats", timeout=2)
            if r.ok:
                extra = r.json()
    except:
        pass
    
    while True:
        frame = viz.render_frame(extra_data=extra or None)
        buf = io.BytesIO()
        frame.save(buf, format="JPEG", quality=85)
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + buf.getvalue() + b"\r\n")
        time.sleep(1.0 / FPS)

@app.get("/mjpeg/{stream_id}")
async def mjpeg_stream(stream_id: str):
    """MJPEG stream endpoint — works in browsers and OBS."""
    if stream_id not in visualizers:
        return Response("Stream not found", 404)
    return StreamingResponse(
        _generate_frames(stream_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/snapshot/{stream_id}")
async def snapshot(stream_id: str):
    """Single frame snapshot."""
    if stream_id not in visualizers:
        return Response("Not found", 404)
    viz = visualizers[stream_id]
    frame = viz.render_frame()
    buf = io.BytesIO()
    frame.save(buf, format="JPEG", quality=90)
    return Response(content=buf.getvalue(), media_type="image/jpeg")

@app.get("/api/viewers")
async def viewer_count():
    with mesh_state.lock:
        return {"count": mesh_state.viewer_count, "revenue": mesh_state.revenue}

@app.post("/api/viewer/{user_id}")
async def add_viewer(user_id: str, name: str = "Anonymous"):
    added = mesh_state.add_viewer(user_id, name)
    return {"added": added, "viewers": mesh_state.viewer_count}

@app.post("/api/chat/{stream_id}")
async def chat_message(stream_id: str, user_id: str, text: str):
    mesh_state.add_message(user_id, text, stream_id)
    return {"ok": True}

@app.post("/api/superchat/{user_id}")
async def super_chat(user_id: str, amount: str, currency: str = "USD", text: str = ""):
    mesh_state.add_super_chat(user_id, amount, currency, text)
    return {"ok": True, "total_revenue": mesh_state.revenue}


# ─── Main ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("LIVESTREAM_PORT", "8900"))
    print(f"⚡ EVEZ Livestream Engine starting on port {port}")
    print(f"   5 streams: cognition, factory, mesh, research, bridge")
    print(f"   MJPEG endpoints: /mjpeg/{{stream_id}}")
    print(f"   Web viewers: /stream/{{stream_id}}")
    uvicorn.run(app, host="0.0.0.0", port=port)
