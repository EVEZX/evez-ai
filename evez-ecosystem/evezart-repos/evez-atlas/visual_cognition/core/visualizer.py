"""Generate visual cognition artifacts from a spine.

Outputs (when Pillow is available):
- attention_overlay.gif (observation + attention bboxes)
- memory_anchor.gif (memory/context used per step)
- cognition_flow.gif (pipeline/timeline per step)
- combined.gif (optional)

Always outputs:
- index.html (offline viewer)

The visualizer is intentionally schema-flexible: if a field is missing
it degrades gracefully.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .spine import read_events


def _have_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except Exception:
        return False


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class VisualizeOutput:
    out_dir: Path
    manifest_path: Path
    artifacts: List[Path]


def visualize_spine(
    spine_path: Path,
    out_dir: Path,
    title: str = "EVEZ Cognition Artifact",
    fps: int = 2,
    max_steps: Optional[int] = None,
) -> VisualizeOutput:
    out_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    events: List[Dict[str, Any]] = list(read_events(spine_path))
    if max_steps is not None:
        events = events[: max_steps]

    # Always write an offline viewer (works without Pillow)
    viewer_path = out_dir / "index.html"
    _write_html_viewer(viewer_path, spine_path, events, title)

    artifacts: List[Path] = [viewer_path]

    pillow_ok = True
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except Exception:
        pillow_ok = False

    if pillow_ok and events:
        attention_frames: List[Path] = []
        memory_frames: List[Path] = []
        flow_frames: List[Path] = []

        for idx, e in enumerate(events):
            attention_frames.append(_render_attention_frame(frames_dir, idx, e, spine_path))
            memory_frames.append(_render_memory_frame(frames_dir, idx, e))
            flow_frames.append(_render_flow_frame(frames_dir, idx, e, len(events)))

        attention_gif = out_dir / "attention_overlay.gif"
        memory_gif = out_dir / "memory_anchor.gif"
        flow_gif = out_dir / "cognition_flow.gif"
        combined_gif = out_dir / "combined.gif"

        _write_gif(attention_frames, attention_gif, fps=fps)
        _write_gif(memory_frames, memory_gif, fps=fps)
        _write_gif(flow_frames, flow_gif, fps=fps)
        _write_gif(_zip_frames(attention_frames, memory_frames, flow_frames, frames_dir), combined_gif, fps=fps)

        artifacts += [attention_gif, memory_gif, flow_gif, combined_gif]

        # Optional MP4
        if _have_ffmpeg():
            mp4 = out_dir / "combined.mp4"
            _write_mp4_from_frames(_zip_frames(attention_frames, memory_frames, flow_frames, frames_dir), mp4, fps=fps)
            artifacts.append(mp4)

    # Manifest: hashes for everything we generated
    manifest = _build_manifest(spine_path, out_dir, artifacts)
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out_dir / "manifest.json.sha256").write_text(_sha256_file(manifest_path) + "  manifest.json\n", encoding="utf-8")

    artifacts.append(manifest_path)
    artifacts.append(out_dir / "manifest.json.sha256")

    return VisualizeOutput(out_dir=out_dir, manifest_path=manifest_path, artifacts=artifacts)


def _build_manifest(spine_path: Path, out_dir: Path, artifacts: List[Path]) -> Dict[str, Any]:
    """Build a tamper-evident manifest.

    Includes:
    - SHA-256 of input spine file
    - Spine hash-chain summary + per-entry hashes (if present)
    - Output artifact hashes
    """

    # Hash input spine file itself (as bytes) + output artifacts
    spine_sha = _sha256_file(spine_path) if spine_path.exists() else None

    # Spine chain summary
    chain = None
    if spine_path.exists():
        from .spine import GENESIS_HASH, HASH_ALG, lint as lint_spine

        res = lint_spine(spine_path)
        # collect per-entry hashes (compact)
        entries = []
        try:
            for e in read_events(spine_path):
                entries.append({
                    "step": e.get("step"),
                    "prev_hash": e.get("prev_hash"),
                    "hash": e.get("hash"),
                })
        except Exception:
            entries = None

        chain = {
            "hash_alg": HASH_ALG,
            "genesis_hash": GENESIS_HASH,
            "root_hash": res.root_hash,
            "ok": res.ok,
            "warnings": res.warnings,
            "violations": res.violations,
            "entries": entries,
        }

    files = []
    for p in artifacts:
        if not p.exists() or p.is_dir():
            continue
        files.append(
            {
                "path": str(p.relative_to(out_dir)) if p.is_relative_to(out_dir) else str(p),
                "bytes": p.stat().st_size,
                "sha256": _sha256_file(p),
            }
        )

    # Best-effort dependency reporting
    deps: Dict[str, Optional[str]] = {
        "pillow": None,
        "numpy": None,
        "scipy": None,
        "ffmpeg": "present" if _have_ffmpeg() else None,
    }
    try:
        import PIL  # type: ignore

        deps["pillow"] = getattr(PIL, "__version__", None)
    except Exception:
        pass
    try:
        import numpy  # type: ignore

        deps["numpy"] = getattr(numpy, "__version__", None)
    except Exception:
        pass
    try:
        import scipy  # type: ignore

        deps["scipy"] = getattr(scipy, "__version__", None)
    except Exception:
        pass

    return {
        "powered_by": "EVEZ",
        "tool": "evez-os",
        "tool_version": "1.1.0",
        "generated_at": int(__import__("time").time()),
        "command": " ".join(map(str, sys.argv)),
        "input": {"spine_path": str(spine_path), "sha256": spine_sha},
        "spine_chain": chain,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "deps": deps,
        },
        "artifacts": files,
    }


def _write_html_viewer(viewer_path: Path, spine_path: Path, events: List[Dict[str, Any]], title: str) -> None:
    # Embed events inline to keep viewer self-contained.
    data = json.dumps(events)
    html = f"""<!doctype html>
<html>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width, initial-scale=1'/>
<title>{title}</title>
<style>
  body {{ font-family: ui-sans-serif, system-ui, -apple-system; margin: 0; background:#0b0f14; color:#e7eef7; }}
  header {{ padding: 16px 20px; border-bottom: 1px solid #1b2633; }}
  .wrap {{ display:grid; grid-template-columns: 1fr 360px; gap:16px; padding:16px; }}
  .card {{ background:#0f1620; border:1px solid #1b2633; border-radius:14px; padding:14px; }}
  pre {{ white-space: pre-wrap; word-break: break-word; }}
  button {{ background:#182435; color:#e7eef7; border:1px solid #223247; border-radius:12px; padding:10px 12px; cursor:pointer; }}
  input[type='range']{{ width:100%; }}
  .muted{{ color:#8aa0b6; }}
</style>
</head>
<body>
<header>
  <div style='display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;'>
    <div>
      <div style='font-size:18px; font-weight:700;'>{title}</div>
      <div class='muted' style='margin-top:4px;'>Offline viewer • Input: {spine_path}</div>
    </div>
    <div style='display:flex; gap:10px; align-items:center;'>
      <button id='prev'>◀</button>
      <button id='play'>▶</button>
      <button id='next'>▶▶</button>
    </div>
  </div>
</header>
<div class='wrap'>
  <div class='card'>
    <div style='display:flex; justify-content:space-between; align-items:center; gap:12px;'>
      <div id='title' style='font-weight:700;'></div>
      <div class='muted' id='meta'></div>
    </div>
    <div style='margin-top:10px;'>
      <div class='muted'>Claim / Action</div>
      <pre id='claim'></pre>
    </div>
    <div style='margin-top:10px;'>
      <div class='muted'>Observation (text)</div>
      <pre id='obs'></pre>
    </div>
  </div>
  <div class='card'>
    <div class='muted'>Memory anchor</div>
    <pre id='mem'></pre>
    <div style='margin-top:14px;' class='muted'>Step</div>
    <input id='slider' type='range' min='0' max='{max(0, len(events)-1)}' value='0'/>
  </div>
</div>
<script>
const EVENTS = {data};
let i = 0;
let timer = null;
function render(){{
  const e = EVENTS[i] || {{}};
  const step = e.step ?? i;
  document.getElementById('title').textContent = 'step ' + step;
  const lob = e.lobby ? (' • ' + e.lobby) : '';
  document.getElementById('meta').textContent = ((e.hash ? e.hash.slice(0,16) : '') + lob);
  document.getElementById('claim').textContent = e.claim || e.action || JSON.stringify(e, null, 2);
  const obs = (e.observation && (e.observation.text || e.observation)) || e.observation_text || '';
  document.getElementById('obs').textContent = typeof obs === 'string' ? obs : JSON.stringify(obs, null, 2);
  const mem = e.memory || (e.context && e.context.memory) || [];
  document.getElementById('mem').textContent = Array.isArray(mem) ? mem.map(x=> (typeof x==='string'? '- ' + x : '- ' + JSON.stringify(x))).join('\n') : JSON.stringify(mem, null, 2);
  document.getElementById('slider').value = i;
}}
function next(){{ i = Math.min(EVENTS.length-1, i+1); render(); }}
function prev(){{ i = Math.max(0, i-1); render(); }}
function togglePlay(){{
  if (timer){{ clearInterval(timer); timer=null; document.getElementById('play').textContent='▶'; return; }}
  document.getElementById('play').textContent='⏸';
  timer = setInterval(()=>{{ if (i>=EVENTS.length-1){{ togglePlay(); return; }} next(); }}, 500);
}}

document.getElementById('next').onclick = next;
document.getElementById('prev').onclick = prev;
document.getElementById('play').onclick = togglePlay;
document.getElementById('slider').oninput = (ev)=>{{ i = parseInt(ev.target.value); render(); }}
render();
</script>
</body>
</html>"""
    viewer_path.write_text(html, encoding="utf-8")


def _resolve_image_path(spine_path: Path, img_ref: str) -> Path:
    p = Path(img_ref)
    if p.is_absolute():
        return p
    # relative to spine file location
    return (spine_path.parent / p).resolve()


def _render_attention_frame(frames_dir: Path, idx: int, e: Dict[str, Any], spine_path: Path) -> Path:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore

    W, H = 960, 540
    canvas = Image.new("RGB", (W, H), (10, 15, 25))
    draw = ImageDraw.Draw(canvas)

    # Load observation image if provided
    obs_img: Optional[Image.Image] = None
    img_ref = None
    if isinstance(e.get("observation"), dict):
        img_ref = e["observation"].get("image") or e["observation"].get("img")
    img_ref = img_ref or e.get("image") or e.get("observation_image")

    if isinstance(img_ref, str):
        p = _resolve_image_path(spine_path, img_ref)
        if p.exists():
            try:
                obs_img = Image.open(p).convert("RGB")
            except Exception:
                obs_img = None

    if obs_img is not None:
        obs_img = obs_img.resize((W, H))
        canvas.paste(obs_img, (0, 0))

    # Overlay attention bboxes
    att = e.get("attention") or (e.get("observation", {}) if isinstance(e.get("observation"), dict) else {}).get("attention")
    if isinstance(att, list):
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        for box in att:
            if not isinstance(box, dict):
                continue
            x = float(box.get("x", 0))
            y = float(box.get("y", 0))
            w = float(box.get("w", 0))
            h = float(box.get("h", 0))
            weight = float(box.get("weight", box.get("score", 1.0)))
            alpha = max(40, min(200, int(255 * max(0.15, min(1.0, weight)))))
            od.rectangle([x * W, y * H, (x + w) * W, (y + h) * H], outline=(255, 50, 80, 255), width=3)
            od.rectangle([x * W, y * H, (x + w) * W, (y + h) * H], fill=(255, 50, 80, alpha))
        canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(canvas)

    # Header text
    step = e.get("step", idx)
    lobby = e.get("lobby", "")
    hsh = (e.get("hash") or "")[:16]
    draw.rectangle([0, 0, W, 44], fill=(0, 0, 0))
    draw.text((12, 12), f"step {step}  {lobby}  {hsh}", fill=(230, 240, 255))

    out = frames_dir / f"attention_{idx:04d}.png"
    canvas.save(out)
    return out


def _render_memory_frame(frames_dir: Path, idx: int, e: Dict[str, Any]) -> Path:
    from PIL import Image, ImageDraw  # type: ignore

    W, H = 960, 540
    img = Image.new("RGB", (W, H), (10, 15, 25))
    draw = ImageDraw.Draw(img)

    step = e.get("step", idx)
    draw.rectangle([0, 0, W, 44], fill=(0, 0, 0))
    draw.text((12, 12), f"step {step}  memory anchor", fill=(230, 240, 255))

    mem = e.get("memory") or (e.get("context", {}) if isinstance(e.get("context"), dict) else {}).get("memory") or []
    used_ids = set()
    if isinstance(e.get("memory_used"), list):
        used_ids = set(map(str, e.get("memory_used")))

    y = 60
    if not mem:
        draw.text((12, y), "(no memory fields found)", fill=(140, 160, 180))
    else:
        for item in mem[:18]:
            if isinstance(item, dict):
                txt = item.get("text") or item.get("content") or json.dumps(item)
                mid = str(item.get("id", ""))
                is_used = bool(item.get("used")) or (mid in used_ids)
            else:
                txt = str(item)
                is_used = False

            prefix = "▶ " if is_used else "• "
            color = (255, 220, 120) if is_used else (200, 210, 225)
            draw.text((12, y), prefix + txt[:120], fill=color)
            y += 24

    out = frames_dir / f"memory_{idx:04d}.png"
    img.save(out)
    return out


def _render_flow_frame(frames_dir: Path, idx: int, e: Dict[str, Any], total: int) -> Path:
    from PIL import Image, ImageDraw  # type: ignore

    W, H = 960, 540
    img = Image.new("RGB", (W, H), (10, 15, 25))
    draw = ImageDraw.Draw(img)

    step = e.get("step", idx)
    draw.rectangle([0, 0, W, 44], fill=(0, 0, 0))
    draw.text((12, 12), f"step {step}  cognition flow", fill=(230, 240, 255))

    # Pipeline nodes (fixed for interpretability)
    nodes = ["observe", "retrieve", "think", "act", "verify"]
    present = {
        "observe": bool(e.get("observation") or e.get("observation_text") or e.get("image")),
        "retrieve": bool(e.get("memory") or e.get("context") or e.get("memory_used")),
        "think": bool(e.get("thought") or e.get("analysis") or e.get("reasoning")),
        "act": bool(e.get("action") or e.get("claim")),
        "verify": bool(e.get("truth_plane") or e.get("verdict")),
    }

    x0, y0 = 80, 140
    dx = 160
    for i, n in enumerate(nodes):
        x = x0 + i * dx
        y = y0
        w, h = 120, 70
        active = present.get(n, False)
        fill = (30, 45, 70) if active else (16, 22, 32)
        outline = (255, 220, 120) if active else (60, 80, 105)
        draw.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=fill, outline=outline, width=3)
        draw.text((x + 18, y + 26), n, fill=(230, 240, 255))
        if i < len(nodes) - 1:
            # arrow
            ax1 = x + w
            ax2 = x + dx
            ay = y + h / 2
            draw.line([ax1, ay, ax2, ay], fill=(100, 130, 160), width=4)
            draw.polygon([(ax2, ay), (ax2 - 10, ay - 6), (ax2 - 10, ay + 6)], fill=(100, 130, 160))

    # Timeline at bottom
    bar_y = H - 80
    bar_x = 40
    bar_w = W - 80
    draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 20], fill=(16, 22, 32), outline=(40, 55, 75))
    if total > 1:
        t = idx / (total - 1)
    else:
        t = 1.0
    cx = bar_x + int(t * bar_w)
    draw.rectangle([cx - 4, bar_y - 6, cx + 4, bar_y + 26], fill=(255, 220, 120))
    draw.text((bar_x, bar_y + 30), f"{idx+1}/{total}", fill=(140, 160, 180))

    out = frames_dir / f"flow_{idx:04d}.png"
    img.save(out)
    return out


def _write_gif(frames: List[Path], out_path: Path, fps: int) -> None:
    from PIL import Image  # type: ignore

    imgs = [Image.open(p).convert("P", palette=Image.Palette.ADAPTIVE) for p in frames]
    duration_ms = int(1000 / max(1, fps))
    imgs[0].save(out_path, save_all=True, append_images=imgs[1:], duration=duration_ms, loop=0)


def _zip_frames(att: List[Path], mem: List[Path], flow: List[Path], frames_dir: Path) -> List[Path]:
    """Create combined storyboard frames from three lists."""
    from PIL import Image  # type: ignore

    out_frames: List[Path] = []
    for i, (a, m, f) in enumerate(zip(att, mem, flow)):
        ia = Image.open(a).convert("RGB")
        im = Image.open(m).convert("RGB")
        ifl = Image.open(f).convert("RGB")
        W, H = ia.size
        canvas = Image.new("RGB", (W * 2, H * 2), (10, 15, 25))
        canvas.paste(ia, (0, 0))
        canvas.paste(im, (W, 0))
        canvas.paste(ifl, (0, H))
        # bottom-right = compact meta
        meta = Image.new("RGB", (W, H), (10, 15, 25))
        canvas.paste(meta, (W, H))
        out = frames_dir / f"combined_{i:04d}.png"
        canvas.save(out)
        out_frames.append(out)
    return out_frames


def _write_mp4_from_frames(frames: List[Path], out_path: Path, fps: int) -> None:
    # Use ffmpeg image2 sequence
    # Write frames to a temp pattern directory (we already have them named combined_XXXX.png)
    if not frames:
        return
    pattern = str(frames[0].parent / "combined_%04d.png")
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(max(1, fps)),
        "-i",
        pattern,
        "-pix_fmt",
        "yuv420p",
        str(out_path),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
