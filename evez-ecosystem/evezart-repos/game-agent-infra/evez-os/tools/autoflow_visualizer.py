#!/usr/bin/env python3
"""
AutoFlow Visualizer (v4)
- Saliency-aware text placement (spectral residual saliency + edges)
- MP4 export (ffmpeg) + GIF
- Memory inscription: write memory text onto seed images BEFORE blending
- Attention Heatmap Mode:
    * saliency_heatmap.png / saliency_overlay.png
    * attention.mp4 (heatmap video)
    * autoflow_with_attention.mp4 (flow + attention composite)

Usage:
  python autoflow_visualizer.py --base base.png --overlay overlay.png --prompt "..." --out outdir

Full:
  python autoflow_visualizer.py --base base.png --overlay overlay.png --prompt "$(cat demo_prompt.txt)" \
    --out out_run --overlay-flow --attention --mp4 \
    --inscribe "SEED MEMORY: ..." --inscribe-base --inscribe-overlay

Notes:
- MP4 requires ffmpeg in PATH.
"""

import argparse, os, re, math, random, shutil, subprocess
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops


# ---------------- Tokenization / weighting ----------------

def _tokenize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9_\-\+\#\.\:\s]", " ", text)
    words = [w for w in text.split() if len(w) >= 3]
    stop = set("""
        the and for with this that from into your you are not but then than have has had
        will would should could can just very more most less few some any all
    """.split())
    return [w for w in words if w not in stop]


def _pick_words(prompt: str, max_words: int = 60):
    toks = _tokenize(prompt)
    if not toks:
        return [("prompt", 1.0)]
    c = Counter(toks)
    scored = [(w, float(freq) * math.log(len(w) + 1.0)) for w, freq in c.items()]
    scored.sort(key=lambda x: x[1], reverse=True)
    scored = scored[:max_words]
    mx = max(s for _, s in scored) if scored else 1.0
    return [(w, s / mx) for w, s in scored]


# ---------------- Image maps (edges + saliency) ----------------

def _to_np_gray(img: Image.Image):
    return np.asarray(img.convert("L"), dtype=np.float32) / 255.0


def _sobel_edges(gray: np.ndarray):
    """Fast Sobel magnitude. Uses scipy if available, else gradient fallback."""
    try:
        from scipy import ndimage as ndi
        gx = ndi.sobel(gray, axis=1, mode="nearest")
        gy = ndi.sobel(gray, axis=0, mode="nearest")
        mag = np.sqrt(gx*gx + gy*gy)
        mag = mag / (mag.max() + 1e-6)
        return mag.astype(np.float32)
    except Exception:
        gx = np.zeros_like(gray)
        gy = np.zeros_like(gray)
        gx[:, 1:-1] = gray[:, 2:] - gray[:, :-2]
        gy[1:-1, :] = gray[2:, :] - gray[:-2, :]
        mag = np.sqrt(gx*gx + gy*gy)
        mag = mag / (mag.max() + 1e-6)
        return mag.astype(np.float32)


def _spectral_residual_saliency(gray: np.ndarray, avg_ksize: int = 7, blur_sigma: float = 2.0, scale: float = 0.6):
    """
    Spectral residual saliency (Hou & Zhang).
    Downsamples for speed then upsamples.
    """
    if scale < 1.0:
        h, w = gray.shape
        small = Image.fromarray((gray*255).astype("uint8")).resize((max(8, int(w*scale)), max(8, int(h*scale))), Image.BILINEAR)
        g = np.asarray(small, dtype=np.float32) / 255.0
    else:
        g = gray.astype(np.float32)

    F = np.fft.fft2(g)
    amp = np.abs(F) + 1e-8
    phase = np.angle(F)
    log_amp = np.log(amp)

    try:
        from scipy import ndimage as ndi
        avg = ndi.uniform_filter(log_amp, size=avg_ksize, mode="nearest")
    except Exception:
        k = avg_ksize
        pad = k // 2
        p = np.pad(log_amp, ((pad,pad),(pad,pad)), mode="edge")
        avg = np.zeros_like(log_amp)
        for y in range(avg.shape[0]):
            for x in range(avg.shape[1]):
                avg[y,x] = np.mean(p[y:y+k, x:x+k])

    residual = log_amp - avg
    recon = np.exp(residual + 1j*phase)
    s = np.fft.ifft2(recon)
    sal = (np.abs(s)**2).astype(np.float32)
    sal = sal / (sal.max() + 1e-8)

    try:
        from scipy import ndimage as ndi
        sal = ndi.gaussian_filter(sal, sigma=blur_sigma, mode="nearest")
    except Exception:
        sal = (sal + np.roll(sal,1,0) + np.roll(sal,-1,0) + np.roll(sal,1,1) + np.roll(sal,-1,1)) / 5.0

    sal = sal / (sal.max() + 1e-8)

    if scale < 1.0:
        h0, w0 = gray.shape
        up = Image.fromarray((sal*255).astype("uint8")).resize((w0, h0), Image.BILINEAR)
        sal = np.asarray(up, dtype=np.float32) / 255.0

    sal = sal / (sal.max() + 1e-8)
    return sal.astype(np.float32)


def _avoid_map(bg: Image.Image, use_saliency: bool = True, saliency_weight: float = 0.60, edge_weight: float = 0.40):
    gray = _to_np_gray(bg)
    edge = _sobel_edges(gray)
    sal = None
    if use_saliency:
        sal = _spectral_residual_saliency(gray, avg_ksize=7, blur_sigma=2.0, scale=0.6)
        avoid = (saliency_weight * sal) + (edge_weight * edge)
    else:
        avoid = edge
    avoid = avoid / (avoid.max() + 1e-6)
    return avoid.astype(np.float32), (sal.astype(np.float32) if sal is not None else None)


# ---------------- Motion field + layout ----------------

def _vector_field(x, y, t, w, h):
    cx, cy = w/2.0, h/2.0
    dx, dy = (x - cx) / w, (y - cy) / h
    vx, vy = -dy, dx
    vx += 0.35 * math.sin(2*math.pi*(y/h) + 0.9*t) + 0.15 * math.sin(4*math.pi*(x/w) - 0.6*t)
    vy += 0.35 * math.cos(2*math.pi*(x/w) - 0.8*t) + 0.15 * math.cos(4*math.pi*(y/h) + 0.7*t)
    n = math.hypot(vx, vy) + 1e-6
    return (vx/n, vy/n)


def _sample_low_positions(avoid, n, margin=20, thresh=0.22):
    h, w = avoid.shape
    positions = []
    tries = 0
    while len(positions) < n and tries < n*700:
        tries += 1
        x = random.randint(margin, w - margin - 1)
        y = random.randint(margin, h - margin - 1)
        if avoid[y, x] < thresh:
            positions.append([float(x), float(y)])
    if len(positions) < n:
        ys = np.linspace(margin, h - margin - 1, int(math.sqrt(n*7))+2).astype(int)
        xs = np.linspace(margin, w - margin - 1, int(math.sqrt(n*7))+2).astype(int)
        cand = []
        for yy in ys:
            for xx in xs:
                cand.append((avoid[yy,xx], float(xx), float(yy)))
        cand.sort(key=lambda z: z[0])
        for _, xx, yy in cand[:n-len(positions)]:
            positions.append([xx, yy])
    return positions


def _spiral_target(i, frame_idx, w, h, n):
    cx, cy = w/2.0, h/2.0
    frac = (i + 1) / (n + 1)
    r = (min(w,h) * 0.45) * frac
    ang = 2*math.pi*(3.0*frac + 0.0009*frame_idx)
    return (cx + r * math.cos(ang), cy + r * math.sin(ang))


def _overlay_flow_frame(overlay: Image.Image, t: float, strength: float):
    deg = (strength * 2.5) * math.sin(0.9*t)
    ox = int((strength * 6.0) * math.sin(1.3*t))
    oy = int((strength * 6.0) * math.cos(1.1*t))
    f = overlay.rotate(deg, resample=Image.BICUBIC, expand=False)
    f = ImageChops.offset(f, ox, oy)
    return f


# ---------------- Memory inscription ----------------

def _load_font():
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _inscribe(img: Image.Image, text: str, opacity: int = 70, diag: bool = True):
    """Visible watermark-style inscription (not steganography)."""
    if not text:
        return img
    font_path = _load_font()
    w, h = img.size
    layer = Image.new("RGBA", (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(layer)

    base_sz = max(14, int(min(w, h) * 0.035))
    font = ImageFont.truetype(font_path, base_sz) if font_path else ImageFont.load_default()

    wrap_width = max(18, int(w / (base_sz * 0.55)))
    raw = re.sub(r"\s+", " ", text.strip())
    chunks = re.findall(r".{1,%d}(?:\s+|$)" % wrap_width, raw)
    lines = [c.strip() for c in chunks if c.strip()]
    if not lines:
        return img

    fill = (255, 255, 255, max(10, min(255, opacity)))
    shadow = (0, 0, 0, max(10, min(255, int(opacity*0.65))))

    if diag:
        step_y = int(base_sz * 3.4)
        step_x = int(base_sz * 11.0)
        n = len(lines)
        for y0 in range(-h, h*2, step_y):
            s = lines[(y0 // step_y) % n]
            for x0 in range(-w, w*2, step_x):
                draw.text((x0+2, y0+2), s, font=font, fill=shadow)
                draw.text((x0, y0), s, font=font, fill=fill)
        layer = layer.rotate(-18, resample=Image.BICUBIC, expand=False)

    out = img.convert("RGBA").copy()
    out.alpha_composite(layer)
    return out


# ---------------- Attention exports + video helpers ----------------

def _heatmap_rgba(map01: np.ndarray, alpha: float = 0.55):
    """map01 -> RGBA heat layer (red->yellow) with alpha proportional to map."""
    m = np.clip(map01, 0.0, 1.0).astype(np.float32)
    r = (np.ones_like(m) * 255).astype(np.uint8)
    g = (m * 255).astype(np.uint8)
    b = (np.zeros_like(m)).astype(np.uint8)
    a = (m * (alpha * 255)).astype(np.uint8)
    rgba = np.stack([r, g, b, a], axis=-1)
    return Image.fromarray(rgba, mode="RGBA")


def _save_attention_images(bg0: Image.Image, avoid: np.ndarray, sal: np.ndarray | None, outdir: Path,
                           source: str = "avoid", alpha: float = 0.55):
    src = avoid
    if source == "saliency" and sal is not None:
        src = sal
    heat = _heatmap_rgba(src, alpha=alpha)

    heat_only = Image.new("RGBA", bg0.size, (0,0,0,255))
    heat_only.alpha_composite(heat)
    heat_only.save(outdir / "saliency_heatmap.png")

    overlayed = bg0.convert("RGBA").copy()
    overlayed.alpha_composite(heat)
    overlayed.save(outdir / "saliency_overlay.png")


def _write_mp4_from_pattern(frames_dir: Path, pattern: str, out_mp4: Path, fps: int = 18):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    cmd = [
        ffmpeg, "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / pattern),
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out_mp4),
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (p.returncode == 0 and out_mp4.exists())


def _compose_attention_over_flow(frames_dir: Path, alpha: float = 0.85):
    flow_paths = sorted(frames_dir.glob("flow_*.png"))
    attn_paths = sorted(frames_dir.glob("attn_*.png"))
    if not flow_paths or not attn_paths:
        return False
    n = min(len(flow_paths), len(attn_paths))
    for i in range(n):
        flow = Image.open(flow_paths[i]).convert("RGBA")
        attn = Image.open(attn_paths[i]).convert("RGBA")
        if alpha < 1.0:
            a = attn.split()[-1]
            a = a.point(lambda v: int(v * alpha))
            attn.putalpha(a)
        flow.alpha_composite(attn)
        flow.save(frames_dir / f"flow_attn_{i:03d}.png")
    return True


# ---------------- Export helpers ----------------

def _write_mp4(frames_dir: Path, out_mp4: Path, fps: int = 18):
    return _write_mp4_from_pattern(frames_dir, "flow_%03d.png", out_mp4, fps=fps)


# ---------------- Main render ----------------

def render_autoflow(
    base_path, overlay_path, prompt, outdir,
    frames=64, alpha=0.45, seed=7,
    overlay_flow=False, overlay_strength=0.85,
    use_saliency=True, mp4=True,
    inscribe_text="", inscribe_base=False, inscribe_overlay=False, inscribe_opacity=70,
    attention=False, attention_source="avoid", attention_alpha=0.55, attention_mp4=True, composite=True
):
    random.seed(seed)
    np.random.seed(seed)

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    frames_dir = outdir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    base0 = Image.open(base_path).convert("RGBA")
    overlay0 = Image.open(overlay_path).convert("RGBA").resize(base0.size, Image.LANCZOS)

    base = _inscribe(base0, inscribe_text, opacity=inscribe_opacity, diag=True) if inscribe_base else base0
    overlay_seed = _inscribe(overlay0, inscribe_text, opacity=inscribe_opacity, diag=True) if inscribe_overlay else overlay0

    bg0 = Image.blend(base, overlay_seed, alpha=alpha)
    bg0.save(outdir / "blended.png")

    avoid, sal = _avoid_map(bg0, use_saliency=use_saliency)

    if attention:
        try:
            _save_attention_images(bg0, avoid=avoid, sal=sal, outdir=outdir, source=attention_source, alpha=attention_alpha)
        except Exception:
            pass

    words = _pick_words(prompt, max_words=60)
    n = len(words)
    pos = _sample_low_positions(avoid, n, margin=26, thresh=0.22)
    vel = [[0.0, 0.0] for _ in range(n)]

    font_path = _load_font()

    def get_font(sz):
        if font_path:
            return ImageFont.truetype(font_path, sz)
        return ImageFont.load_default()

    def hash_cell(x, y, cell=60):
        return int(x//cell), int(y//cell)

    H, W = avoid.shape
    best_static = None
    best_score = 1e9

    for fi in range(frames):
        t = fi / max(frames-1, 1) * 2*math.pi
        overlay = _overlay_flow_frame(overlay_seed, t, overlay_strength) if overlay_flow else overlay_seed
        bg = Image.blend(base, overlay, alpha=alpha)

        if attention:
            src = avoid
            if attention_source == "saliency" and sal is not None:
                src = sal
            heat = _heatmap_rgba(src, alpha=attention_alpha)
            heat_only = Image.new("RGBA", bg.size, (0,0,0,255))
            heat_only.alpha_composite(heat)
            heat_only.save(frames_dir / f"attn_{fi:03d}.png")

        grid = defaultdict(list)
        for i, (x, y) in enumerate(pos):
            grid[hash_cell(x, y)].append(i)

        for i, (word, wgt) in enumerate(words):
            x, y = pos[i]
            tx, ty = _spiral_target(i, fi, W, H, n)
            fx, fy = _vector_field(x, y, t, W, H)

            xi = int(min(max(x,1), W-2))
            yi = int(min(max(y,1), H-2))
            axg = float(avoid[yi, xi+1] - avoid[yi, xi-1])
            ayg = float(avoid[yi+1, xi] - avoid[yi-1, xi])

            rx, ry = 0.0, 0.0
            cx, cy = hash_cell(x, y)
            for gx in (cx-1, cx, cx+1):
                for gy in (cy-1, cy, cy+1):
                    for j in grid.get((gx, gy), []):
                        if j == i:
                            continue
                        x2, y2 = pos[j]
                        dx, dy = x - x2, y - y2
                        d2 = dx*dx + dy*dy
                        if d2 < 1e-3:
                            continue
                        if d2 < 45*45:
                            inv = 1.0 / (math.sqrt(d2) + 1e-6)
                            rx += dx * inv
                            ry += dy * inv

            ax = 0.030*(tx - x) + 1.8*fx - 52.0*axg + 18.0*rx
            ay = 0.030*(ty - y) + 1.8*fy - 52.0*ayg + 18.0*ry

            vel[i][0] = 0.78*vel[i][0] + ax
            vel[i][1] = 0.78*vel[i][1] + ay

            x += vel[i][0]
            y += vel[i][1]
            x = min(max(x, 24.0), W - 24.0)
            y = min(max(y, 24.0), H - 24.0)
            pos[i][0], pos[i][1] = x, y

        frame = bg.copy()
        draw = ImageDraw.Draw(frame)

        score = 0.0
        for i, (word, wgt) in enumerate(words):
            x, y = pos[i]
            score += avoid[int(y), int(x)] * (1.0 + 1.4*wgt)
        if score < best_score:
            best_score = score
            best_static = frame.copy()

        for i, (word, wgt) in enumerate(words):
            x, y = pos[i]
            sz = int(12 + 32*wgt)
            font = get_font(sz)
            a = int(70 + 160*wgt + 40*math.sin(t + i*0.35))
            a = max(20, min(255, a))
            draw.text((x+2, y+2), word, font=font, fill=(0,0,0, int(a*0.60)))
            draw.text((x, y), word, font=font, fill=(255,255,255,a))

        frame.save(frames_dir / f"flow_{fi:03d}.png")

    if best_static:
        best_static.save(outdir / "best_layout.png")

    # GIF
    try:
        imgs = [Image.open(p).convert("P", palette=Image.ADAPTIVE) for p in sorted(frames_dir.glob("flow_*.png"))]
        if imgs:
            imgs[0].save(outdir / "autoflow.gif", save_all=True, append_images=imgs[1:], duration=55, loop=0, optimize=False)
    except Exception:
        pass

    # MP4(s)
    if mp4:
        _write_mp4(frames_dir, outdir / "autoflow.mp4", fps=18)

    if attention and attention_mp4:
        _write_mp4_from_pattern(frames_dir, "attn_%03d.png", outdir / "attention.mp4", fps=18)

    if attention and composite:
        ok = _compose_attention_over_flow(frames_dir, alpha=0.85)
        if ok:
            _write_mp4_from_pattern(frames_dir, "flow_attn_%03d.png", outdir / "autoflow_with_attention.mp4", fps=18)

    return str(outdir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--overlay", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", default="out_autoflow")
    ap.add_argument("--frames", type=int, default=64)
    ap.add_argument("--alpha", type=float, default=0.45)
    ap.add_argument("--seed", type=int, default=7)

    ap.add_argument("--overlay-flow", action="store_true")
    ap.add_argument("--overlay-strength", type=float, default=0.85)

    ap.add_argument("--saliency", action="store_true")
    ap.add_argument("--no-saliency", action="store_true")

    ap.add_argument("--mp4", action="store_true")
    ap.add_argument("--no-mp4", action="store_true")

    ap.add_argument("--inscribe", default="")
    ap.add_argument("--inscribe-base", action="store_true")
    ap.add_argument("--inscribe-overlay", action="store_true")
    ap.add_argument("--inscribe-opacity", type=int, default=70)

    # Attention heatmap mode
    ap.add_argument("--attention", action="store_true")
    ap.add_argument("--attention-source", choices=["avoid", "saliency"], default="avoid")
    ap.add_argument("--attention-alpha", type=float, default=0.55)
    ap.add_argument("--no-attention-mp4", action="store_true")
    ap.add_argument("--no-composite", action="store_true")

    args = ap.parse_args()

    use_saliency = True
    if args.no_saliency:
        use_saliency = False
    if args.saliency:
        use_saliency = True

    use_mp4 = True
    if args.no_mp4:
        use_mp4 = False
    if args.mp4:
        use_mp4 = True

    render_autoflow(
        args.base, args.overlay, args.prompt, args.out,
        frames=args.frames, alpha=args.alpha, seed=args.seed,
        overlay_flow=args.overlay_flow, overlay_strength=args.overlay_strength,
        use_saliency=use_saliency, mp4=use_mp4,
        inscribe_text=args.inscribe,
        inscribe_base=args.inscribe_base,
        inscribe_overlay=args.inscribe_overlay,
        inscribe_opacity=args.inscribe_opacity,
        attention=args.attention,
        attention_source=args.attention_source,
        attention_alpha=args.attention_alpha,
        attention_mp4=(not args.no_attention_mp4),
        composite=(not args.no_composite),
    )


if __name__ == "__main__":
    main()
