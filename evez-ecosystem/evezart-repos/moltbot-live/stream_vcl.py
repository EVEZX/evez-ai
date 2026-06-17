#!/usr/bin/env python3
"""
EVEZ VCL Live Stream v2 — Hardened Pipeline
Xvfb → Headless Chromium → FFmpeg → YouTube RTMP
With health monitoring, auto-recovery, and metrics.
"""
import os, sys, signal, subprocess, time, atexit, shutil, json, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Configuration ──
DISPLAY = os.environ.get("STREAM_DISPLAY", ":99")
WIDTH = int(os.environ.get("STREAM_WIDTH", "1280"))
HEIGHT = int(os.environ.get("STREAM_HEIGHT", "720"))
FPS = os.environ.get("FPS", "30")
BITRATE = os.environ.get("BITRATE", "2500k")
YOUTUBE_RTMP_URL = os.environ.get("YOUTUBE_RTMP_URL", "rtmp://a.rtmp.youtube.com/live2")
YOUTUBE_STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY", "")
VCL_HTML = os.environ.get("VCL_HTML", "/app/visualizer/index.html")
HEALTH_PORT = int(os.environ.get("HEALTH_PORT", "8080"))

# ── State ──
processes = {}
start_time = time.time()
restart_count = 0
last_health_check = time.time()
stream_healthy = False

def cleanup():
    for name, p in processes.items():
        try: p.terminate(); p.wait(timeout=5)
        except:
            try: p.kill()
            except: pass
    print("[stream] All processes cleaned up.")

atexit.register(cleanup)
for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, lambda s,f: (cleanup(), sys.exit(0)))

# ── Health Server ──
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        uptime = int(time.time() - start_time)
        procs = {name: (p.poll() is None) for name, p in processes.items()}
        healthy = all(procs.values()) and len(procs) >= 3

        status = 200 if healthy else 503
        body = json.dumps({
            "status": "streaming" if healthy else "degraded",
            "uptime_seconds": uptime,
            "restarts": restart_count,
            "processes": procs,
            "resolution": f"{WIDTH}x{HEIGHT}",
            "fps": FPS,
            "bitrate": BITRATE
        })
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, format, *args): pass  # suppress logs

def start_health_server():
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[stream] Health server on :{HEALTH_PORT}")

# ── Process Launchers ──
def start_xvfb():
    print(f"[stream] Starting Xvfb {DISPLAY} @ {WIDTH}x{HEIGHT}x24")
    p = subprocess.Popen([
        "Xvfb", DISPLAY, "-screen", "0", f"{WIDTH}x{HEIGHT}x24",
        "-ac", "+extension", "GLX", "+render", "-noreset"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    processes["xvfb"] = p
    time.sleep(1.5)
    if p.poll() is not None:
        print("[stream] FATAL: Xvfb failed!"); sys.exit(1)
    os.environ["DISPLAY"] = DISPLAY
    print(f"[stream] Xvfb OK on {DISPLAY}")
    return p

def start_chromium():
    print("[stream] Starting headless Chromium...")
    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY

    chrome = None
    for c in ["chromium-browser", "chromium", "google-chrome-stable", "google-chrome"]:
        if shutil.which(c): chrome = c; break
    if not chrome:
        print("[stream] FATAL: No Chromium binary!"); sys.exit(1)

    p = subprocess.Popen([
        chrome,
        "--no-sandbox", "--disable-gpu", "--disable-software-rasterizer",
        "--use-gl=swiftshader",
        f"--window-size={WIDTH},{HEIGHT}", "--window-position=0,0",
        "--kiosk", "--disable-extensions",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-hang-monitor",
        "--autoplay-policy=no-user-gesture-required",
        "--disable-features=TranslateUI",
        "--force-device-scale-factor=1",
        f"file://{VCL_HTML}"
    ], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    processes["chromium"] = p
    time.sleep(4)
    if p.poll() is not None:
        print("[stream] FATAL: Chromium failed!"); sys.exit(1)
    print("[stream] Chromium rendering VCL visualizer")
    return p

def start_ffmpeg():
    if not YOUTUBE_STREAM_KEY:
        print("[stream] FATAL: YOUTUBE_STREAM_KEY not set!"); sys.exit(1)

    rtmp_url = f"{YOUTUBE_RTMP_URL}/{YOUTUBE_STREAM_KEY}"
    print(f"[stream] FFmpeg → {YOUTUBE_RTMP_URL}/****")

    bufsize = f"{int(BITRATE.replace('k','')) * 2}k" if 'k' in BITRATE else BITRATE

    cmd = [
        "ffmpeg", "-y", "-nostdin",
        # Video: X11 capture
        "-f", "x11grab", "-video_size", f"{WIDTH}x{HEIGHT}",
        "-framerate", FPS, "-i", DISPLAY,
        # Audio: silent (YouTube needs audio track)
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        # Encode
        "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
        "-b:v", BITRATE, "-maxrate", BITRATE, "-bufsize", bufsize,
        "-pix_fmt", "yuv420p",
        "-g", str(int(FPS) * 2),
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-shortest",
        "-f", "flv",
        "-flvflags", "no_duration_filesize",
        rtmp_url
    ]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    processes["ffmpeg"] = p
    time.sleep(3)
    if p.poll() is not None:
        stderr = p.stderr.read().decode()[:500]
        print(f"[stream] FATAL: FFmpeg failed!\n{stderr}"); sys.exit(1)
    print("[stream] FFmpeg streaming to YouTube Live!")
    return p

# ── Main ──
def main():
    global restart_count
    print("=" * 60)
    print("  EVEZ VCL Live — Cognition Topology Stream v2")
    print("  Infinite. Self-healing. Always on.")
    print("=" * 60)

    start_health_server()
    xvfb = start_xvfb()
    chrome = start_chromium()
    ffmpeg = start_ffmpeg()

    print(f"\n[stream] ✅ ALL SYSTEMS GO — Streaming to YouTube Live")
    print(f"[stream] {WIDTH}x{HEIGHT} @ {FPS}fps · {BITRATE} · H.264/AAC")
    print(f"[stream] Health: http://localhost:{HEALTH_PORT}/")

    while True:
        time.sleep(5)
        for name, proc in list(processes.items()):
            if proc.poll() is not None:
                restart_count += 1
                print(f"[stream] ⚠️ {name} died (exit {proc.returncode}). Total restarts: {restart_count}")
                # Let run_forever.sh handle full restart
                cleanup()
                sys.exit(1)

if __name__ == "__main__":
    main()
