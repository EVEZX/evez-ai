#!/usr/bin/env python3
"""
EVEZ Intel Livestream — live data ingestion + visible AI reasoning trace → YouTube RTMP

Layout (1280x720):
  LEFT   (0-400):    Live data — Polymarket odds, GitHub trending, signal feed
  CENTER (410-850):  AI reasoning trace streaming character by character
  RIGHT  (860-1280): Synthesis output — confidence, conclusions, next action

Runs indefinitely. Each cycle (~45s):
  1. Fetch Polymarket + GitHub live
  2. Run deepseek-r1 synthesis via AI/ML API
  3. Stream <think> trace into center panel
  4. Pipe frames → ffmpeg → YouTube RTMP
"""

import os, sys, time, math, textwrap, subprocess, threading, json, re
from datetime import datetime, timezone
from collections import deque
from urllib import request

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 24
RTMP_URL = os.environ.get("RTMP_URL", "rtmp://a.rtmp.youtube.com/live2")
STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY", "")
AI_ML_API_KEY = os.environ.get("AI_ML_API_KEY", "")
FULL_RTMP = f"{RTMP_URL}/{STREAM_KEY}" if STREAM_KEY else RTMP_URL

C = {
    "bg": (4, 6, 12), "border": (25, 40, 80),
    "green": (0, 230, 80), "cyan": (0, 200, 255),
    "amber": (255, 160, 0), "purple": (180, 60, 255),
    "white": (220, 225, 235), "dim": (60, 75, 100),
    "red": (255, 60, 60), "gold": (255, 200, 40),
}

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    "/usr/share/fonts/truetype/ubuntu/UbuntuMono-B.ttf",
]

def load_font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

F = {s: load_font(s) for s in [11, 13, 15, 18, 22, 28, 36]}

class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.poly = [
            {"q": "PRC military incident Q1 2026", "yes": 0.72},
            {"q": "AGI declared by end 2027",       "yes": 0.44},
            {"q": "BTC >$150k by Dec 2026",          "yes": 0.58},
            {"q": "US recession 2026",                "yes": 0.38},
            {"q": "OpenAI IPO in 2026",               "yes": 0.51},
        ]
        self.repos = ["deepseek-ai/DeepSeek-R1 \u272548k", "EvezArt/evez-os",
                      "microsoft/markitdown", "browser-use/browser-use", "astral-sh/uv"]
        self.signals = deque(maxlen=8)
        self.signals.extend([
            "[POLY] PRC incident 72% YES \u2014 pressure rising",
            "[GH]   evez-os: CI green, 3 commits today",
            "[NET]  deepseek-r1 trending +2.1k stars",
            "[SYN]  Reedley biolab: no new filings",
        ])
        self.think = ""
        self.think_cursor = 0
        self.synthesis = "Initializing..."
        self.confidence = 0.0
        self.status = "BOOT"
        self.cycle = 0
        self.last_fetch = 0.0
        self.frame_n = 0
        self.t0 = time.time()
        self.query = "Analyzing live signals..."

ST = State()

def fetch_polymarket():
    try:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=5"
        req = request.Request(url, headers={"User-Agent": "evez-os/1.1"})
        with request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        mkts = []
        for m in data[:5]:
            q = m.get("question", "?")[:55]
            op = m.get("outcomePrices") or []
            yes = float(op[0]) if op else 0.5
            mkts.append({"q": q, "yes": yes})
        if mkts:
            with ST.lock:
                ST.poly = mkts
                ST.signals.appendleft(f"[POLY] {mkts[0]['q'][:38]} {mkts[0]['yes']*100:.0f}%")
    except Exception as e:
        with ST.lock: ST.signals.appendleft(f"[POLY] err: {str(e)[:38]}")

def fetch_github():
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        url = f"https://api.github.com/search/repositories?q=stars:>50+created:>{today}&sort=stars&per_page=5"
        req = request.Request(url, headers={"User-Agent": "evez-os/1.1",
                                            "Accept": "application/vnd.github.v3+json"})
        with request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        repos = [f"{it['full_name']} \u2605{it['stargazers_count']}" for it in data.get("items", [])[:5]]
        if repos:
            with ST.lock:
                ST.repos = repos
                ST.signals.appendleft(f"[GH]   {repos[0][:42]}")
    except Exception as e:
        with ST.lock: ST.signals.appendleft(f"[GH]   err: {str(e)[:38]}")

def run_synthesis():
    if not AI_ML_API_KEY:
        seed = ("<think>\nNo API key. Seed run.\nPolymarket: geopolitical pressure 72% YES.\n"
                "GitHub: AI inference tooling trending hard.\nRevenue loop: nominal.\n</think>\n"
                "Three convergent signals: pressure, AI edge, loop nominal. Confidence: 0.81")
        with ST.lock:
            ST.think = seed
            ST.synthesis = "Geopolitical pressure + AI edge convergence. Loop nominal."
            ST.confidence = 0.81
            ST.think_cursor = 0
            ST.status = "LIVE"
        return
    try:
        with ST.lock:
            poly_str = "\n".join(f"  {m['q']}: {m['yes']*100:.0f}% YES" for m in ST.poly)
            gh_str = "\n".join(f"  {r}" for r in ST.repos[:3])
            cyc = ST.cycle
            ST.query = f"cycle {cyc}: multi-signal synthesis"
            ST.status = "QUERYING"

        prompt = (f"COMPUTE STATE checkpoint-{cyc}:\n"
                  f"Polymarket:\n{poly_str}\n\nGitHub trending:\n{gh_str}\n\n"
                  "Synthesize signals. Show reasoning chain. Output confidence 0-1. Be terse.")

        payload = json.dumps({
            "model": "deepseek/deepseek-r1",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500, "stream": False
        }).encode()

        req = request.Request("https://api.aimlapi.com/v1/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {AI_ML_API_KEY}",
                     "Content-Type": "application/json"},
            method="POST")
        with request.urlopen(req, timeout=35) as r:
            resp = json.loads(r.read())

        content = resp["choices"][0]["message"]["content"]
        conf_m = re.search(r"confidence[:\s]+([0-9.]+)", content, re.IGNORECASE)
        conf = float(conf_m.group(1)) if conf_m else 0.75
        think_m = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
        think = think_m.group(0) if think_m else f"<think>\n{content[:400]}\n</think>"
        synth = content.split("</think>")[-1].strip()[:200] if "</think>" in content else content[:200]

        with ST.lock:
            ST.think = think
            ST.synthesis = synth or content[:200]
            ST.confidence = min(1.0, max(0.0, conf))
            ST.think_cursor = 0
            ST.status = "LIVE"
            ST.signals.appendleft(f"[AI]   r1 c{cyc} conf={conf:.2f}")
    except Exception as e:
        with ST.lock:
            ST.status = "ERR"
            ST.signals.appendleft(f"[AI]   err: {str(e)[:45]}")

def data_loop():
    while True:
        with ST.lock: ST.cycle += 1
        fetch_polymarket()
        fetch_github()
        run_synthesis()
        with ST.lock: ST.last_fetch = time.time()
        time.sleep(45)

LW = 398; CX = 408; CW = 442; RX = 860; RW = W - RX - 6
PAD = 10; HDR = 44

def glow(d, x, y, txt, font, col, r=2):
    rv, gv, bv = col
    for dx in range(-r, r+1):
        for dy in range(-r, r+1):
            if dx*dx+dy*dy <= r*r:
                a = max(0, 1 - math.sqrt(dx*dx+dy*dy)/r)
                d.text((x+dx, y+dy), txt, font=font,
                       fill=(int(rv*a*.3), int(gv*a*.3), int(bv*a*.3)))
    d.text((x, y), txt, font=font, fill=col)

def bbar(d, x, y, w, h, pct, fc):
    d.rectangle([x, y, x+w, y+h], fill=(18, 22, 38))
    d.rectangle([x, y, x+int(w*pct), y+h], fill=fc)

def scanlines(d, t):
    for yi in range(0, H, 14):
        a = int(7 + 3*math.sin(yi*.04 + t*1.5))
        d.line([(0, yi), (W, yi)], fill=(a, a, a))

def pborder(d, x, y, w, h, col, t, lbl=""):
    tk = int((math.sin(t*2)*.5+.5)*5)
    d.rectangle([x, y, x+w, y+h], outline=col, width=1)
    for px, py in [(x,y),(x+w,y),(x,y+h),(x+w,y+h)]:
        d.rectangle([px-tk, py-1, px+tk, py+1], fill=col)
    if lbl:
        lw2 = F[11].getbbox(lbl)[2]
        d.rectangle([x+8, y-7, x+14+lw2, y+7], fill=C["bg"])
        d.text((x+10, y-6), lbl, font=F[11], fill=col)

def render_frame(t):
    img = Image.new("RGB", (W, H), C["bg"])
    d = ImageDraw.Draw(img)
    scanlines(d, t)

    with ST.lock:
        poly = list(ST.poly); repos = list(ST.repos)
        sigs = list(ST.signals); think = ST.think
        cur = ST.think_cursor; synth = ST.synthesis
        conf = ST.confidence; status = ST.status
        cyc = ST.cycle; fn = ST.frame_n
        elapsed = int(time.time() - ST.t0)
        lf = ST.last_fetch; query = ST.query

    d.rectangle([(0,0),(W,HDR)], fill=(5,7,15))
    up = f"{elapsed//3600:02d}:{(elapsed%3600)//60:02d}:{elapsed%60:02d}"
    sc = C["green"] if status=="LIVE" else C["amber"] if status=="QUERYING" else C["red"]
    glow(d, 10, 11, "\u26a1 EVEZ INTEL LIVESTREAM", F[22], C["cyan"], 2)
    d.text((305, 8), f"cycle {cyc}  frame {fn}  up {up}", font=F[13], fill=C["dim"])
    glow(d, W-115, 12, f"\u25cf {status}", F[15], sc)
    nxt = max(0, int(45-(time.time()-lf))) if lf else 45
    d.text((W-115, 27), f"fetch in {nxt}s", font=F[11], fill=C["dim"])
    if int(t*2)%2==0: d.text((W-22,13), "\u25ae", font=F[15], fill=C["cyan"])
    d.line([(0,HDR),(W,HDR)], fill=C["border"])

    Y0 = HDR + 12

    pborder(d, 4, Y0-6, LW-6, H-Y0-4, C["border"], t, "LIVE DATA")
    d.text((PAD, Y0), "POLYMARKET", font=F[13], fill=C["cyan"])
    for i, m in enumerate(poly[:5]):
        y = Y0+20+i*50
        for li, ln in enumerate(textwrap.wrap(m["q"], 42)[:2]):
            d.text((PAD, y+li*13), ln, font=F[11], fill=C["white"])
        by = y+28
        bbar(d, PAD, by, LW-22, 8, m["yes"], (0, int(255*m["yes"]), 80))
        d.text((PAD, by+10), f"YES {m['yes']*100:.0f}%", font=F[11], fill=C["green"])
        d.text((PAD+80, by+10), f"NO {(1-m['yes'])*100:.0f}%", font=F[11], fill=C["dim"])

    sy = Y0+275
    d.line([(PAD, sy-6),(LW-6, sy-6)], fill=C["border"])
    d.text((PAD, sy), "SIGNAL FEED", font=F[13], fill=C["amber"])
    for i, sig in enumerate(sigs[:6]):
        a = max(0.25, 1.0-i*.13)
        d.text((PAD, sy+18+i*18), sig[:47], font=F[11],
               fill=tuple(int(v*a) for v in C["white"]))

    gy = sy+138
    d.line([(PAD, gy-6),(LW-6, gy-6)], fill=C["border"])
    d.text((PAD, gy), "GITHUB TRENDING", font=F[13], fill=C["purple"])
    for i, repo in enumerate(repos[:5]):
        a = max(0.3, 1.0-i*.15)
        d.text((PAD, gy+18+i*17), repo[:44], font=F[11],
               fill=tuple(int(v*a) for v in C["purple"]))

    pborder(d, CX-2, Y0-6, CW, H-Y0-4, C["border"], t, "AI REASONING TRACE")
    cx2 = CX+4
    if think:
        new_cur = min(len(think), cur + max(1, int(len(think)/160)))
        with ST.lock: ST.think_cursor = new_cur
        visible = think[:new_cur]
    else:
        visible = "Waiting for data..."; new_cur = 0

    lines = []
    for raw in visible.split("\n"):
        lines.extend(textwrap.wrap(raw, 44) if len(raw) > 44 else [raw])
    ml = (H - Y0 - 22) // 14
    lines = lines[-ml:] if len(lines) > ml else lines

    for i, ln in enumerate(lines):
        yy = Y0 + i*14
        if yy > H-20: break
        if "<think>" in ln or "</think>" in ln: col = C["amber"]
        elif "COMPUTE STATE" in ln or ln.strip().startswith("#"): col = C["cyan"]
        elif "confidence" in ln.lower(): col = C["gold"]
        else:
            a = max(0.3, 1 - (len(lines)-i)/ml*.6)
            col = tuple(int(v*a) for v in C["green"])
        d.text((cx2, yy), ln[:44], font=F[13], fill=col)

    if think and new_cur < len(think) and int(t*3)%2==0:
        ly = Y0+len(lines)*14
        if ly < H-20: d.text((cx2, ly), "\u258c", font=F[13], fill=C["green"])

    pborder(d, RX-2, Y0-6, RW, H-Y0-4, C["border"], t, "SYNTHESIS")
    rx2 = RX+4
    d.text((rx2, Y0), "CONFIDENCE", font=F[13], fill=C["cyan"])
    cc = C["green"] if conf > 0.7 else C["amber"] if conf > 0.4 else C["red"]
    glow(d, rx2, Y0+18, f"{conf:.2f}", F[36], cc)
    bbar(d, rx2, Y0+62, RW-14, 10, conf, cc)

    d.line([(rx2, Y0+80),(RX+RW-4, Y0+80)], fill=C["border"])
    d.text((rx2, Y0+86), "OUTPUT", font=F[13], fill=C["amber"])
    for i, ln in enumerate(textwrap.wrap(synth, 26)[:8]):
        d.text((rx2, Y0+104+i*18), ln, font=F[13], fill=C["white"])

    d.line([(rx2, Y0+248),(RX+RW-4, Y0+248)], fill=C["border"])
    d.text((rx2, Y0+254), "QUERY", font=F[11], fill=C["dim"])
    for i, ln in enumerate(textwrap.wrap(query, 26)[:2]):
        d.text((rx2, Y0+268+i*14), ln, font=F[11], fill=C["dim"])

    ts2 = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    d.text((rx2, H-22), ts2, font=F[11], fill=C["dim"])
    p = int((math.sin(t*3)*.5+.5)*180)+75
    d.text((W-55, H-20), f"#{fn}", font=F[11], fill=(p, p, p))

    with ST.lock: ST.frame_n += 1
    return img

def start_ff():
    cmd = ["ffmpeg", "-y",
           "-f", "rawvideo", "-vcodec", "rawvideo",
           "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
           "-i", "-",
           "-vcodec", "libx264", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", "-g", str(FPS*2),
           "-b:v", "3000k", "-maxrate", "3000k", "-bufsize", "6000k",
           "-f", "flv", FULL_RTMP]
    print(f"[stream] ffmpeg \u2192 {FULL_RTMP[:55]}...", flush=True)
    return subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def main():
    print(f"[stream] EVEZ Intel Livestream starting {W}x{H}@{FPS}fps", flush=True)
    threading.Thread(target=data_loop, daemon=True).start()
    time.sleep(1)
    ff = start_ff()
    interval = 1.0 / FPS
    ts = time.time()
    try:
        while True:
            frame = render_frame(time.time() % 10000)
            try:
                ff.stdin.write(frame.tobytes())
                ff.stdin.flush()
            except BrokenPipeError:
                print("[stream] pipe broken \u2014 restarting ffmpeg", flush=True)
                ff = start_ff()
                continue
            sleep_t = interval - (time.time() - ts)
            if sleep_t > 0: time.sleep(sleep_t)
            ts = time.time()
    except KeyboardInterrupt:
        print("\n[stream] stopped", flush=True)
    finally:
        if ff.stdin: ff.stdin.close()
        ff.wait()

if __name__ == "__main__":
    main()
