"""
EVEZ HyperStream API — Vercel serverless endpoint
Live stream status + control plane for 8 hypergeometric visualizers
"""
from http.server import BaseHTTPRequestHandler
import json, time

STREAMS = [
    {"id": "hyper_2d", "name": "Hypergeometric 2D", "url": "https://youtube.com/watch?v=a0bPZMrznIM", "status": "live"},
    {"id": "hyper_3d", "name": "Hypergeometric 3D", "url": "https://youtube.com/watch?v=_5l0CfgE3g0", "status": "live"},
    {"id": "polytope_4d", "name": "4D Polytope Arena", "url": "https://youtube.com/watch?v=-5FDrSt7nZc", "status": "live"},
    {"id": "lattice", "name": "Reactive Lattice", "url": "https://youtube.com/watch?v=0n8_Kkaijfk", "status": "live"},
    {"id": "ai_arena", "name": "AI Arena", "url": "https://youtube.com/watch?v=HhgWYqc8rbg", "status": "live"},
    {"id": "mandelbrot", "name": "Mandelbrot Reactive", "url": "https://youtube.com/watch?v=x-q93pHVUoA", "status": "live"},
    {"id": "fourier", "name": "Fourier Arena", "url": "https://youtube.com/watch?v=1igd9N7kqqI", "status": "live"},
    {"id": "cognitive", "name": "EVEZ666 Cognitive", "url": "https://youtube.com/watch?v=AZKZDbM2Fbk", "status": "live"},
]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/health":
            self._json({"status": "ok", "ts": int(time.time())})
        elif self.path == "/api/streams":
            self._json({"streams": STREAMS, "count": len(STREAMS), "ts": int(time.time())})
        else:
            # Landing page
            html = self._landing()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())

    def _json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _landing(self):
        cards = "".join([
            f'''<a href="{s["url"]}" target="_blank" class="card">
              <div class="status {s["status"]}"></div>
              <h3>{s["name"]}</h3>
              <p>▶ Watch Live</p>
            </a>'''
            for s in STREAMS
        ])
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>EVEZ HyperStream — 8 Live Mathematical Universes</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:#0a0a0f;color:#e0e0ff;font-family:system-ui,sans-serif;min-height:100vh}}
  header{{padding:3rem 2rem;text-align:center;background:linear-gradient(135deg,#0d0d1a,#1a0a2e)}}
  h1{{font-size:2.5rem;background:linear-gradient(90deg,#00ffcc,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
  .sub{{color:#888;margin-top:.5rem;font-size:1.1rem}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1.5rem;padding:2rem;max-width:1200px;margin:0 auto}}
  .card{{background:#111;border:1px solid #2a2a4a;border-radius:12px;padding:1.5rem;text-decoration:none;color:inherit;transition:transform.2s,border-color.2s;position:relative}}
  .card:hover{{transform:translateY(-4px);border-color:#7c3aed}}
  .status{{width:10px;height:10px;border-radius:50%;background:#00ff88;position:absolute;top:1rem;right:1rem;animation:pulse 2s infinite}}
  @keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 rgba(0,255,136,.4)}}50%{{box-shadow:0 0 0 8px rgba(0,255,136,0)}}}}
  h3{{font-size:1.1rem;margin-bottom:.5rem;color:#e0e0ff}}
  p{{color:#7c3aed;font-size:.9rem}}
  footer{{text-align:center;padding:2rem;color:#444}}
</style>
</head>
<body>
<header>
  <h1>⚡ EVEZ HyperStream</h1>
  <p class="sub">8 Live Mathematical Universes — 24/7 Autonomous Streams</p>
</header>
<div class="grid">{cards}</div>
<footer>EVEZ Ecosystem — Powered by Hypergeometric Functions &amp; 4D Polytopes</footer>
</body>
</html>"""
    def log_message(self, *args): pass
