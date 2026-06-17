#!/usr/bin/env python3
"""
visualize_thought.py
Wrapper for AutoFlow Visualizer. Accepts either a packet JSON or explicit args.
"""

import argparse, json, os, sys, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTO = HERE / "autoflow_visualizer.py"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--packet", default="")
    p.add_argument("--base", default="")
    p.add_argument("--overlay", default="")
    p.add_argument("--memory", default="")
    p.add_argument("--prompt", default="")
    p.add_argument("--out", default="")
    p.add_argument("--frames", type=int, default=None)
    p.add_argument("--alpha", type=float, default=None)
    p.add_argument("--overlay_flow", action="store_true")
    p.add_argument("--saliency", action="store_true")
    p.add_argument("--mp4", action="store_true")

    p.add_argument("--inscribe_base", action="store_true")
    p.add_argument("--inscribe_overlay", action="store_true")
    p.add_argument("--inscribe_opacity", type=int, default=70)

    # attention
    p.add_argument("--attention", action="store_true")
    p.add_argument("--attention_source", default="avoid", choices=["avoid","saliency"])
    p.add_argument("--attention_alpha", type=float, default=0.55)

    args = p.parse_args()

    cfg = {}
    if args.packet:
        cfg = json.loads(Path(args.packet).read_text(errors="ignore"))

    base = args.base or cfg.get("base", "")
    overlay = args.overlay or cfg.get("overlay", "")
    memory = args.memory or cfg.get("memory", "")
    prompt = args.prompt or cfg.get("prompt", "")
    out = args.out or cfg.get("out", "")

    render = cfg.get("render", {}) if isinstance(cfg, dict) else {}
    frames = args.frames if args.frames is not None else render.get("frames", 96)
    alpha = args.alpha if args.alpha is not None else render.get("alpha", 0.45)
    overlay_flow = args.overlay_flow or bool(render.get("overlay_flow", True))
    saliency = args.saliency or bool(render.get("saliency", True))
    mp4 = args.mp4 or bool(render.get("mp4", True))

    inscribe_base = args.inscribe_base or bool(render.get("inscribe_base", True))
    inscribe_overlay = args.inscribe_overlay or bool(render.get("inscribe_overlay", False))
    inscribe_opacity = args.inscribe_opacity or int(render.get("inscribe_opacity", 70))

    attention = args.attention or bool(render.get("attention", False))
    attention_source = args.attention_source or render.get("attention_source", "avoid")
    attention_alpha = args.attention_alpha if args.attention_alpha is not None else float(render.get("attention_alpha", 0.55))

    if not out:
        out = str(Path.cwd() / "out_visual_thought")

    cmd = [sys.executable, str(AUTO),
           "--base", base,
           "--overlay", overlay,
           "--prompt", prompt,
           "--out", out,
           "--frames", str(frames),
           "--alpha", str(alpha)
    ]

    if overlay_flow:
        cmd += ["--overlay-flow"]
    if saliency:
        cmd += ["--saliency"]
    if mp4:
        cmd += ["--mp4"]

    if memory:
        cmd += ["--inscribe", memory]
        if inscribe_base:
            cmd += ["--inscribe-base"]
        if inscribe_overlay:
            cmd += ["--inscribe-overlay"]
        cmd += ["--inscribe-opacity", str(inscribe_opacity)]

    if attention:
        cmd += ["--attention", "--attention-source", attention_source, "--attention-alpha", str(attention_alpha)]

    print("RUN:", " ".join(cmd))
    subprocess.check_call(cmd)

if __name__ == "__main__":
    main()
