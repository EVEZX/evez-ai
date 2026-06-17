#!/usr/bin/env python3
"""
EVEZ Intel Livestream — live data + AI reasoning + VCL Honeypot NPC Audit → YouTube RTMP

Layout (1280x720) — 4 panels:
  PANEL 1 (0-295):     LIVE DATA — Polymarket odds, signal feed, GitHub trending
  PANEL 2 (303-598):   AI REASONING TRACE — deepseek-r1 <think> stream
  PANEL 3 (606-901):   SYNTHESIS — confidence, output, query
  PANEL 4 (909-1276):  NPC AUDIT FEED — honeypot intruder classifications live

Each cycle (~45s): fetch Polymarket + GitHub + deepseek-r1 synthesis
NPC feed: pulls from Ably channel 'evez-vcl-npc' every 8s (background thread)
→ Pipe all frames → ffmpeg → YouTube RTMP 24fps
"""

import os, time, math, textwrap, subprocess, threading, json, re, base64
from datetime import datetime, timezone
from collections import deque
from urllib import request

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 24
RTMP_URL   = os.environ.get("RTMP_URL", "rtmp://a.rtmp.youtube.com/live2")
STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY", "")
AI_ML_KEY  = os.environ.get("AI_ML_API_KEY", "")
ABLY_KEY   = os.environ.get("ABLY_API_KEY", "")
FULL_RTMP  = f"{RTMP_URL}/{STREAM_KEY}" if STREAM_KEY else RTMP_URL

# panel x boundaries
P1X, P2X, P3X, P4X = 4, 303, 606, 909
PW = 290          # panel content width
PAD, HDR = 8, 44

C = {
    "bg":     (4, 6, 12),    "border":  (25, 40, 80),
    "green":  (0, 230, 80),  "cyan":    (0, 200, 255),
    "amber":  (255, 160, 0), "purple":  (180, 60, 255),
    "white":  (220, 225, 235),"dim":    (60, 75, 100),
    "red":    (255, 60, 60), "gold":    (255, 200, 40),
    "teal":   (0, 210, 180), "pink":    (255, 80, 180),
    "orange": (255, 120, 30),
}

TIER_COLOR = {
    "clean":     (0, 200, 80),
    "suspect":   (255, 160, 0),
    "hostile":   (255, 60, 60),
    "confirmed": (200, 0, 200),
}
CLASS_COLOR = {
    "SCANNER":          (255, 60, 60),
    "SCRAPER":          (255, 120, 30),
    "DISINFO_SHILL":    (200, 0, 200),
    "SPAM_BOT":         (255, 80, 180),
    "PROBE_AGENT":      (255, 60, 60),
    "LURK_WATCHER":     (0, 200, 255),
    "DISCLOSURE_DENIER":(200, 0, 200),
    "UNCLASSIFIED":     (60, 75, 100),
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

F = {s: load_font(s) for s in [10, 11, 13, 15, 18, 22, 28, 36]}


# ── STATE ─────────────────────────────────────────────────────────────────────

class State:
    def __init__(self):
        self.lock = threading.Lock()
        # panel 1 — live data
        self.poly = [
            {"q": "PRC military incident Q1 2026", "yes": 0.72},
            {"q": "AGI declared by end 2027",       "yes": 0.44},
            {"q": "BTC >$150k by Dec 2026",          "yes": 0.58},
            {"q": "US recession 2026",               "yes": 0.38},
            {"q": "OpenAI IPO in 2026",              "yes": 0.51},
        ]
        self.repos  = ["deepseek-ai/DeepSeek-R1 ★48k", "EvezArt/evez-os",
                       "microsoft/markitdown", "browser-use/browser-use", "astral-sh/uv"]
        self.signals = deque(maxlen=8)
        self.signals.extend([
            "[POLY] PRC incident 72% YES — pressure rising",
            "[GH]   evez-os: CI green, 3 commits today",
            "[NET]  deepseek-r1 trending +2.1k stars",
            "[SYN]  Reedley biolab: no new filings",
        ])
        # panel 2 — reasoning
        self.think        = ""
        self.think_cursor = 0
        # panel 3 — synthesis
        self.synthesis  = "Initializing..."
        self.confidence = 0.0
        self.query      = "Analyzing live signals..."
        # panel 4 — NPC audit
        self.npc_list   = deque(maxlen=20)   # recent NPC records
        self.npc_stats  = {}                  # class → count
        self.npc_total  = 0
        self.npc_last_ts = ""
        # meta
        self.status   = "BOOT"
        self.cycle    = 0
        self.last_fetch = 0.0
        self.frame_n  = 0
        self.t0       = time.time()

ST = State()


# ── DATA FETCHERS ──────────────────────────────────────────────────────────────

def fetch_polymarket():
    try:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=5"
        req = request.Request(url, headers={"User-Agent": "evez-os/2.0"})
        with request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        mkts = []
        for m in data[:5]:
            q  = m.get("question", "?")[:55]
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
        url = (f"https://api.github.com/search/repositories"
               f"?q=stars:>50+created:>{today}&sort=stars&per_page=5")
        req = request.Request(url, headers={"User-Agent": "evez-os/2.0",
                                            "Accept": "application/vnd.github.v3+json"})
        with request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        repos = [f"{it['full_name']} ★{it['stargazers_count']}"
                 for it in data.get("items", [])[:5]]
        if repos:
            with ST.lock:
                ST.repos = repos
                ST.signals.appendleft(f"[GH]   {repos[0][:42]}")
    except Exception as e:
        with ST.lock: ST.signals.appendleft(f"[GH]   err: {str(e)[:38]}")

def run_synthesis():
    if not AI_ML_KEY:
        seed = ("<think>\nNo API key — seed run.\nPolymarket: geopolitical pressure 72% YES.\n"
                "GitHub: AI inference tooling trending hard.\nHoneypot: monitoring live.\n</think>\n"
                "Three convergent signals: pressure, AI edge, honeypot active. Confidence: 0.81")
        with ST.lock:
            ST.think = seed; ST.synthesis = "Geopolitical + AI edge + honeypot active."
            ST.confidence = 0.81; ST.think_cursor = 0; ST.status = "LIVE"
        return
    try:
        with ST.lock:
            poly_str = "\n".join(f"  {m['q']}: {m['yes']*100:.0f}% YES" for m in ST.poly)
            gh_str   = "\n".join(f"  {r}" for r in ST.repos[:3])
            npc_str  = f"  {ST.npc_total} total actors classified" if ST.npc_total else "  no actors yet"
            cyc = ST.cycle
            ST.query  = f"cycle {cyc}: multi-signal synthesis"
            ST.status = "QUERYING"
        prompt = (f"COMPUTE STATE checkpoint-{cyc}:\n"
                  f"Polymarket:\n{poly_str}\n\nGitHub trending:\n{gh_str}\n\n"
                  f"Honeypot NPC feed:\n{npc_str}\n\n"
                  "Synthesize signals. Show reasoning chain. Output confidence 0-1. Be terse.")
        payload = json.dumps({
            "model": "deepseek/deepseek-r1",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500, "stream": False
        }).encode()
        req = request.Request("https://api.aimlapi.com/v1/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {AI_ML_KEY}",
                     "Content-Type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=35) as r:
            resp = json.loads(r.read())
        content  = resp["choices"][0]["message"]["content"]
        conf_m   = re.search(r"confidence[:\s]+([0-9.]+)", content, re.IGNORECASE)
        conf     = float(conf_m.group(1)) if conf_m else 0.75
        think_m  = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
        think    = think_m.group(0) if think_m else f"<think>\n{content[:400]}\n</think>"
        synth    = content.split("</think>")[-1].strip()[:200] if "</think>" in content else content[:200]
        with ST.lock:
            ST.think = think; ST.synthesis = synth or content[:200]
            ST.confidence = min(1.0, max(0.0, conf))
            ST.think_cursor = 0; ST.status = "LIVE"
            ST.signals.appendleft(f"[AI]   r1 c{cyc} conf={conf:.2f}")
    except Exception as e:
        with ST.lock:
            ST.status = "ERR"
            ST.signals.appendleft(f"[AI]   err: {str(e)[:45]}")

def data_loop():
    while True:
        with ST.lock: ST.cycle += 1
        fetch_polymarket(); fetch_github(); run_synthesis()
        with ST.lock: ST.last_fetch = time.time()
        time.sleep(45)


# ── NPC ABLY FEED ──────────────────────────────────────────────────────────────

def ably_get_channel_history(channel: str, limit: int = 20) -> list[dict]:
    """Pull recent Ably channel history via REST API."""
    if not ABLY_KEY: return []
    try:
        key_id, key_secret = ABLY_KEY.split(":", 1)
        token = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
        url = (f"https://rest.ably.io/channels/{channel}/messages"
               f"?limit={limit}&direction=backwards")
        req = request.Request(url, headers={"Authorization": f"Basic {token}",
                                            "Accept": "application/json"})
        with request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except Exception as e:
        return []

def npc_loop():
    """Background thread: pull NPC records from Ably evez-vcl-npc every 8s."""
    seen_ids = set()
    while True:
        try:
            msgs = ably_get_channel_history("evez-vcl-npc", limit=20)
            new_records = []
            for msg in msgs:
                mid = msg.get("id", "")
                if mid in seen_ids: continue
                seen_ids.add(mid)
                payload = msg.get("data")
                if isinstance(payload, str):
                    try: payload = json.loads(payload)
                    except: continue
                if isinstance(payload, dict) and "npc_class" in payload:
                    new_records.append(payload)
            if new_records:
                with ST.lock:
                    for rec in reversed(new_records):
                        ST.npc_list.appendleft(rec)
                        cls = rec.get("npc_class", "UNCLASSIFIED")
                        ST.npc_stats[cls] = ST.npc_stats.get(cls, 0) + 1
                        ST.npc_total += 1
                    ST.npc_last_ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
                    if new_records:
                        ST.signals.appendleft(
                            f"[NPC]  +{len(new_records)} actors classified")
        except Exception:
            pass
        # also try local fallback file (written by honeypot watcher on same runner)
        try:
            local = "output/naughty_list.json"
            if os.path.exists(local):
                with open(local) as f:
                    records = json.load(f)
                for rec in records[-5:]:
                    fp = rec.get("fingerprint", "")
                    if fp and fp not in seen_ids:
                        seen_ids.add(fp)
                        with ST.lock:
                            ST.npc_list.appendleft(rec)
                            cls = rec.get("npc_class", "UNCLASSIFIED")
                            ST.npc_stats[cls] = ST.npc_stats.get(cls, 0) + 1
                            ST.npc_total += 1
        except Exception:
            pass
        time.sleep(8)


# ── RENDER HELPERS ─────────────────────────────────────────────────────────────

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

def panel_border(d, x, y, w, h, col, t, lbl=""):
    tk = int((math.sin(t*2)*.5+.5)*4)
    d.rectangle([x, y, x+w, y+h], outline=col, width=1)
    for px, py in [(x,y),(x+w,y),(x,y+h),(x+w,y+h)]:
        d.rectangle([px-tk, py-1, px+tk, py+1], fill=col)
    if lbl:
        lw2 = F[10].getbbox(lbl)[2]
        d.rectangle([x+6, y-6, x+10+lw2, y+6], fill=C["bg"])
        d.text((x+8, y-5), lbl, font=F[10], fill=col)

def tier_badge(d, x, y, tier):
    col = TIER_COLOR.get(tier, C["dim"])
    label = tier.upper()[:4]
    d.rectangle([x, y, x+32, y+12], fill=col)
    d.text((x+2, y+1), label, font=F[10], fill=(4, 6, 12))

def class_badge(d, x, y, cls):
    col = CLASS_COLOR.get(cls, C["dim"])
    short = cls[:10]
    bw = F[10].getbbox(short)[2] + 6
    d.rectangle([x, y, x+bw, y+12], fill=(18, 22, 38))
    d.rectangle([x, y, x+bw, y+12], outline=col, width=1)
    d.text((x+3, y+1), short, font=F[10], fill=col)
    return bw


# ── RENDER FRAME ───────────────────────────────────────────────────────────────

def render_frame(t):
    img = Image.new("RGB", (W, H), C["bg"])
    d   = ImageDraw.Draw(img)
    scanlines(d, t)

    with ST.lock:
        poly      = list(ST.poly)
        repos     = list(ST.repos)
        sigs      = list(ST.signals)
        think     = ST.think
        cur       = ST.think_cursor
        synth     = ST.synthesis
        conf      = ST.confidence
        status    = ST.status
        cyc       = ST.cycle
        fn        = ST.frame_n
        elapsed   = int(time.time() - ST.t0)
        lf        = ST.last_fetch
        query     = ST.query
        npc_list  = list(ST.npc_list)
        npc_stats = dict(ST.npc_stats)
        npc_total = ST.npc_total
        npc_lts   = ST.npc_last_ts

    # ── HUD bar ──────────────────────────────────────────────────────────────
    d.rectangle([(0,0),(W,HDR)], fill=(5,7,15))
    up  = f"{elapsed//3600:02d}:{(elapsed%3600)//60:02d}:{elapsed%60:02d}"
    sc  = C["green"] if status=="LIVE" else C["amber"] if status=="QUERYING" else C["red"]
    glow(d, 8, 11, "⚡ EVEZ INTEL LIVESTREAM v2", F[18], C["cyan"], 2)
    d.text((285, 8),  f"cycle {cyc}  frame {fn}  up {up}", font=F[11], fill=C["dim"])
    glow(d, W-115, 12, f"● {status}", F[13], sc)
    nxt = max(0, int(45-(time.time()-lf))) if lf else 45
    d.text((W-115, 27), f"fetch in {nxt}s", font=F[10], fill=C["dim"])
    d.text((720, 8),  f"NPC:{npc_total} classified", font=F[11], fill=C["teal"])
    if int(t*2)%2==0: d.text((W-22,13), "▮", font=F[13], fill=C["cyan"])
    d.line([(0,HDR),(W,HDR)], fill=C["border"])

    Y0 = HDR + 10
    PH = H - Y0 - 6   # panel height

    # ── PANEL 1: LIVE DATA ────────────────────────────────────────────────────
    panel_border(d, P1X, Y0-4, PW+2, PH, C["border"], t, "LIVE DATA")
    px = P1X + PAD
    d.text((px, Y0+2), "POLYMARKET", font=F[11], fill=C["cyan"])
    for i, m in enumerate(poly[:5]):
        y = Y0+18+i*46
        for li, ln in enumerate(textwrap.wrap(m["q"], 36)[:2]):
            d.text((px, y+li*11), ln, font=F[10], fill=C["white"])
        by = y+24
        bbar(d, px, by, PW-12, 7, m["yes"], (0, int(255*m["yes"]), 80))
        d.text((px, by+9), f"YES {m['yes']*100:.0f}%", font=F[10], fill=C["green"])
        d.text((px+56, by+9), f"NO {(1-m['yes'])*100:.0f}%", font=F[10], fill=C["dim"])
    sy = Y0+255
    d.line([(px, sy-4),(P1X+PW-4, sy-4)], fill=C["border"])
    d.text((px, sy), "SIGNAL FEED", font=F[11], fill=C["amber"])
    for i, sig in enumerate(sigs[:5]):
        a = max(0.3, 1.0-i*.14)
        d.text((px, sy+16+i*16), sig[:38], font=F[10],
               fill=tuple(int(v*a) for v in C["white"]))
    gy = sy+106
    d.line([(px, gy-4),(P1X+PW-4, gy-4)], fill=C["border"])
    d.text((px, gy), "GITHUB TRENDING", font=F[11], fill=C["purple"])
    for i, repo in enumerate(repos[:5]):
        a = max(0.3, 1.0-i*.15)
        d.text((px, gy+16+i*15), repo[:38], font=F[10],
               fill=tuple(int(v*a) for v in C["purple"]))

    # ── PANEL 2: AI REASONING TRACE ──────────────────────────────────────────
    panel_border(d, P2X-2, Y0-4, PW+4, PH, C["border"], t, "AI REASONING TRACE")
    cx = P2X + PAD
    if think:
        new_cur = min(len(think), cur + max(1, int(len(think)/160)))
        with ST.lock: ST.think_cursor = new_cur
        visible = think[:new_cur]
    else:
        visible = "Waiting for data..."; new_cur = 0
    lines = []
    for raw in visible.split("\n"):
        lines.extend(textwrap.wrap(raw, 36) if len(raw) > 36 else [raw])
    ml = (PH - 10) // 13
    lines = lines[-ml:] if len(lines) > ml else lines
    for i, ln in enumerate(lines):
        yy = Y0 + i*13
        if yy > H-18: break
        if "<think>" in ln or "</think>" in ln: col = C["amber"]
        elif "COMPUTE STATE" in ln or ln.strip().startswith("#"): col = C["cyan"]
        elif "confidence" in ln.lower(): col = C["gold"]
        else:
            a = max(0.3, 1 - (len(lines)-i)/ml*.6)
            col = tuple(int(v*a) for v in C["green"])
        d.text((cx, yy), ln[:36], font=F[13], fill=col)
    if think and new_cur < len(think) and int(t*3)%2==0:
        ly = Y0+len(lines)*13
        if ly < H-18: d.text((cx, ly), "▌", font=F[13], fill=C["green"])

    # ── PANEL 3: SYNTHESIS ───────────────────────────────────────────────────
    panel_border(d, P3X-2, Y0-4, PW+4, PH, C["border"], t, "SYNTHESIS")
    rx = P3X + PAD
    d.text((rx, Y0+2), "CONFIDENCE", font=F[11], fill=C["cyan"])
    cc = C["green"] if conf > 0.7 else C["amber"] if conf > 0.4 else C["red"]
    glow(d, rx, Y0+18, f"{conf:.2f}", F[28], cc)
    bbar(d, rx, Y0+56, PW-12, 9, conf, cc)
    d.line([(rx, Y0+72),(P3X+PW-4, Y0+72)], fill=C["border"])
    d.text((rx, Y0+78), "OUTPUT", font=F[11], fill=C["amber"])
    for i, ln in enumerate(textwrap.wrap(synth, 28)[:7]):
        d.text((rx, Y0+94+i*17), ln, font=F[11], fill=C["white"])
    d.line([(rx, Y0+218),(P3X+PW-4, Y0+218)], fill=C["border"])
    d.text((rx, Y0+224), "QUERY", font=F[10], fill=C["dim"])
    for i, ln in enumerate(textwrap.wrap(query, 28)[:2]):
        d.text((rx, Y0+236+i*13), ln, font=F[10], fill=C["dim"])
    ts2 = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    d.text((rx, H-20), ts2, font=F[10], fill=C["dim"])

    # ── PANEL 4: NPC AUDIT FEED ───────────────────────────────────────────────
    panel_border(d, P4X-2, Y0-4, W-P4X-4, PH, C["red"], t, "NPC AUDIT FEED")
    nx = P4X + PAD
    nw = W - P4X - 16

    # stats bar
    d.text((nx, Y0+2), f"HONEYPOT  total:{npc_total}", font=F[11], fill=C["teal"])
    if npc_lts:
        d.text((nx+180, Y0+2), npc_lts, font=F[10], fill=C["dim"])

    # top 4 class counts
    top_classes = sorted(npc_stats.items(), key=lambda x: -x[1])[:4]
    for i, (cls, cnt) in enumerate(top_classes):
        col = CLASS_COLOR.get(cls, C["dim"])
        label = f"{cls[:12]} {cnt}"
        d.text((nx + (i % 2)*140, Y0+18+(i//2)*13), label, font=F[10], fill=col)

    # separator
    sy2 = Y0+48
    d.line([(nx, sy2),(nx+nw, sy2)], fill=C["border"])
    d.text((nx, sy2+2), "LIVE INTRUDER LOG", font=F[10], fill=C["red"])

    # NPC records list
    if not npc_list:
        d.text((nx, sy2+20), "monitoring...", font=F[11], fill=C["dim"])
        d.text((nx, sy2+36), "vcl honeypot active", font=F[10], fill=C["dim"])
    else:
        y_off = sy2 + 18
        for i, rec in enumerate(npc_list[:13]):
            if y_off > H-20: break
            cls     = rec.get("npc_class", "UNCLASSIFIED")
            tier    = rec.get("tier", "clean")
            author  = (rec.get("author") or rec.get("remote_addr") or "???")[:14]
            conf_r  = rec.get("confidence", 0.0)
            evid    = rec.get("evidence", [])
            first_e = evid[0][:18] if evid else ""

            # row glow on new entries
            a_fade = max(0.25, 1.0 - i * 0.07)
            col_dim = tuple(int(v*a_fade) for v in C["white"])

            # class badge + tier badge
            bw = class_badge(d, nx, y_off, cls)
            tier_badge(d, nx+bw+3, y_off, tier)

            d.text((nx, y_off+14), author, font=F[10], fill=col_dim)
            if first_e:
                d.text((nx+80, y_off+14), first_e, font=F[10], fill=C["dim"])

            # mini confidence bar
            bbar(d, nx, y_off+27, int(nw*0.6), 4, conf_r,
                 CLASS_COLOR.get(cls, C["dim"]))

            y_off += 36
            if i < len(npc_list)-1 and y_off < H-20:
                d.line([(nx, y_off-2),(nx+nw, y_off-2)],
                       fill=(20, 28, 50))

    with ST.lock: ST.frame_n += 1
    return img


# ── FFMPEG ─────────────────────────────────────────────────────────────────────

def start_ff():
    cmd = ["ffmpeg", "-y",
           "-f", "rawvideo", "-vcodec", "rawvideo",
           "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
           "-i", "-",
           "-vcodec", "libx264", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", "-g", str(FPS*2),
           "-b:v", "3000k", "-maxrate", "3000k", "-bufsize", "6000k",
           "-f", "flv", FULL_RTMP]
    print(f"[stream] ffmpeg → {FULL_RTMP[:60]}...", flush=True)
    return subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def main():
    print(f"[stream] EVEZ Intel Livestream v2 — {W}x{H}@{FPS}fps", flush=True)
    print(f"[stream] RTMP: {FULL_RTMP[:60]}", flush=True)
    print(f"[stream] Ably NPC feed: {'enabled' if ABLY_KEY else 'disabled (no key)'}", flush=True)
    threading.Thread(target=data_loop, daemon=True).start()
    threading.Thread(target=npc_loop, daemon=True).start()
    time.sleep(1)
    ff       = start_ff()
    interval = 1.0 / FPS
    ts       = time.time()
    try:
        while True:
            frame = render_frame(time.time() % 10000)
            try:
                ff.stdin.write(frame.tobytes())
                ff.stdin.flush()
            except BrokenPipeError:
                print("[stream] pipe broken — restarting ffmpeg", flush=True)
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
