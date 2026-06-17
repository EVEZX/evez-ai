"""
EVEZ HyperStream Manager — 24/7 persistent engine
8 streams: hypergeometric 2D/3D, 4D polytopes, reactive lattice,
AI arena, Mandelbrot fractals, Fourier, EVEZ666 cognitive.
Reacts to YouTube live chat. Self-restarts on any failure.
"""
import subprocess, threading, time, json, logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("evez-stream")

with open("config.json") as f:
    CONFIGS = json.load(f)

VIS_MAP = {
    "hyper_2d":    "visualizers.hyper_2d",
    "hyper_3d":    "visualizers.hyper_3d",
    "polytope_4d": "visualizers.polytope_4d",
    "lattice":     "visualizers.lattice",
    "arena":       "visualizers.arena",
    "fractal":     "visualizers.fractal",
    "fourier":     "visualizers.fourier",
    "cognitive":   "visualizers.cognitive",
}

YT_CHAT_URL = "https://www.googleapis.com/youtube/v3/liveChat/messages"
YT_TOKEN_REFRESH_INTERVAL = 1800  # 30 min

_yt_token = {"token": "", "refreshed": 0}

def get_yt_token():
    now = time.time()
    if now - _yt_token["refreshed"] > YT_TOKEN_REFRESH_INTERVAL:
        try:
            r = subprocess.run("surething auth token youtube", shell=True,
                               capture_output=True, text=True, timeout=15)
            _yt_token["token"] = json.loads(r.stdout)["access_token"]
            _yt_token["refreshed"] = now
        except Exception as e:
            log.warning(f"Token refresh failed: {e}")
    return _yt_token["token"]


class StreamWorker(threading.Thread):
    def __init__(self, cfg):
        name = f"stream-{cfg['vis']}"
        super().__init__(daemon=True, name=name)
        self.cfg = cfg
        self.rtmp = f"{cfg['rtmp_url']}/{cfg['stream_key']}"
        self.running = True
        self.frames = 0
        self.fps = 24
        self.W, self.H = 1280, 720

        import importlib
        mod = importlib.import_module(VIS_MAP[cfg["vis"]])
        self.render_frame = mod.render_frame
        self.mutate = getattr(mod, "mutate", lambda c: None)
        log.info(f"[{cfg['vis']}] visualizer loaded")

    def _ffmpeg_cmd(self):
        return [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgba",
            "-s", f"{self.W}x{self.H}", "-r", str(self.fps), "-i", "pipe:0",
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
            "-b:v", "2500k", "-maxrate", "3000k", "-bufsize", "6000k",
            "-g", str(self.fps * 2), "-keyint_min", str(self.fps),
            "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p",
            "-f", "flv", self.rtmp
        ]

    def run(self):
        while self.running:
            proc = None
            try:
                log.info(f"[{self.cfg['vis']}] FFmpeg starting → {self.rtmp[:55]}...")
                proc = subprocess.Popen(self._ffmpeg_cmd(), stdin=subprocess.PIPE)
                t = 0.0; dt = 1.0 / self.fps
                while self.running and proc.poll() is None:
                    frame = self.render_frame(t)
                    proc.stdin.write(frame)
                    proc.stdin.flush()
                    self.frames += 1
                    t += dt
                    time.sleep(dt * 0.8)  # slight speedup to avoid buffer lag
                rc = proc.returncode
                log.warning(f"[{self.cfg['vis']}] FFmpeg exited rc={rc}, restarting in 4s")
                time.sleep(4)
            except BrokenPipeError:
                log.warning(f"[{self.cfg['vis']}] BrokenPipe, restarting in 4s")
                time.sleep(4)
            except Exception as e:
                log.error(f"[{self.cfg['vis']}] {type(e).__name__}: {e}")
                if proc:
                    try: proc.kill()
                    except: pass
                time.sleep(5)

    def stop(self):
        self.running = False


class ChatReactor(threading.Thread):
    """Poll YouTube live chat every ~8s and route to visualizers."""
    def __init__(self, workers):
        super().__init__(daemon=True, name="chat-reactor")
        self.workers = workers
        self._seen = set()

    def _fetch(self, w):
        chat_id = w.cfg.get("live_chat_id")
        if not chat_id: return
        token = get_yt_token()
        if not token: return
        r = requests.get(YT_CHAT_URL,
                         params={"liveChatId": chat_id, "part": "snippet", "maxResults": 200},
                         headers={"Authorization": f"Bearer {token}"}, timeout=8)
        if r.status_code != 200: return
        for m in r.json().get("items", [])[-15:]:
            mid = m.get("id", "")
            if mid in self._seen: continue
            self._seen.add(mid)
            text = m.get("snippet", {}).get("displayMessage", "")
            if not text: continue
            w.mutate(text)
            # Pulse lattice on every message from any stream
            for ow in self.workers:
                if ow.cfg["vis"] == "lattice":
                    ow.mutate(text)

    def run(self):
        while True:
            for w in self.workers:
                try: self._fetch(w)
                except Exception as e:
                    log.debug(f"ChatReactor {w.cfg['vis']}: {e}")
            if len(self._seen) > 10000:
                self._seen = set(list(self._seen)[-5000:])
            time.sleep(8)


class HealthHandler(BaseHTTPRequestHandler):
    workers_ref = []

    def do_GET(self):
        data = {"status": "running",
                "streams": [{"vis": w.cfg["vis"], "frames": w.frames,
                              "watch": w.cfg.get("watch_url","")}
                             for w in self.workers_ref]}
        body = json.dumps(data, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_): pass


def main():
    log.info(f"EVEZ HyperStream — {len(CONFIGS)} streams starting")
    workers = [StreamWorker(cfg) for cfg in CONFIGS]
    for i, w in enumerate(workers):
        w.start()
        time.sleep(1.5)  # stagger to avoid CPU spike

    reactor = ChatReactor(workers)
    reactor.start()
    log.info("Chat reactor started")

    HealthHandler.workers_ref = workers
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    log.info("Health API on :8080")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down")
        for w in workers: w.stop()


if __name__ == "__main__":
    main()
