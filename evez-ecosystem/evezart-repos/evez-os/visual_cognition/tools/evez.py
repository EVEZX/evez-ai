#!/usr/bin/env python3
"""EVEZ-OS CLI — Visual Cognition Layer

One command (offline) to convert a JSONL spine into animated cognition artifacts:
    python3 tools/evez.py visualize-thought --input spine/spine.jsonl

Commands:
  play             Generate a demo append-only spine
  lint             Validate a spine for integrity
  visualize-thought  Build animations + manifest from a spine

This CLI is dependency-minimal:
- Works with stdlib only (HTML viewer + manifest)
- Adds GIF/MP4 generation when Pillow/ffmpeg are available
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Allow running from repo root without installing
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.spine import LintResult, append_event, lint, read_events  # noqa: E402
from core.visualizer import visualize_spine  # noqa: E402

DEFAULT_SPINE = REPO_ROOT / "spine" / "spine.jsonl"

LOBBIES = ["DNS", "BGP", "TLS", "CDN", "AUTH", "ROLLBACK", "FUNDING", "MIXED"]
NARRATORS = {
    "PUBLIC_INTERNET": "The world argues about truth at line-rate. You do not get one reality. You get convergence.",
    "FSC_FORGE": "Compression applied. The model cracked first at the boundary of pending vs final.",
    "XRAY_ROOM": "If your resolver lies, your world-map lies. Two vantages or you are worshipping one cache.",
}


def _maybe_make_demo_image(out_dir: Path, step: int, seed: int) -> Optional[str]:
    """Optionally create a synthetic observation image.

    If Pillow isn't installed, we simply skip image output.
    """
    try:
        from PIL import Image, ImageDraw  # type: ignore
    except Exception:
        return None

    rng = random.Random(seed * 99991 + step)
    W, H = 640, 360
    img = Image.new("RGB", (W, H), (12, 18, 28))
    d = ImageDraw.Draw(img)

    # draw random blocks
    for _ in range(6):
        x1 = rng.randint(0, W - 40)
        y1 = rng.randint(0, H - 40)
        x2 = x1 + rng.randint(30, 160)
        y2 = y1 + rng.randint(30, 160)
        col = (rng.randint(40, 255), rng.randint(40, 255), rng.randint(40, 255))
        d.rectangle([x1, y1, x2, y2], outline=(230, 240, 255), width=2, fill=col)

    # crosshair
    cx = rng.randint(80, W - 80)
    cy = rng.randint(80, H - 80)
    d.line([cx - 30, cy, cx + 30, cy], fill=(255, 255, 255), width=2)
    d.line([cx, cy - 30, cx, cy + 30], fill=(255, 255, 255), width=2)

    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"obs_{step:04d}.png"
    img.save(p)
    return str(p.relative_to(REPO_ROOT))


def cmd_play(args: argparse.Namespace) -> None:
    random.seed(args.seed)
    spine_path = Path(args.output).resolve()

    print(f"\n{'='*68}")
    print(f" EVEZ Play Engine | seed={args.seed} | steps={args.steps} | out={spine_path}")
    print(f" Powered by EVEZ | github.com/EvezArt/evez-os")
    print(f"{'='*68}\n")

    img_dir = REPO_ROOT / "spine" / "obs"

    for i in range(args.steps):
        lobby = random.choice(LOBBIES)
        narrator = random.choice(list(NARRATORS.keys()))

        claim = f"step_{i:03d}: {lobby} probe — hypothesis pending falsification"

        img_rel = _maybe_make_demo_image(img_dir, i, args.seed) if args.with_images else None

        # normalized bbox around a random focus
        fx, fy = random.random(), random.random()
        w, h = 0.25, 0.25
        attention = [{"x": max(0.0, fx - w/2), "y": max(0.0, fy - h/2), "w": w, "h": h, "weight": 0.85}]

        memory = [
            {"id": "goal", "text": "Maintain append-only provenance (no rewrite)", "used": True},
            {"id": "threat", "text": "Assume untrusted environment; verify hashes", "used": True},
            {"id": "lobby", "text": f"Current lobby: {lobby}", "used": True},
            {"id": "note", "text": NARRATORS[narrator], "used": False},
        ]

        event: Dict[str, Any] = {
            "step": i,
            "lobby": lobby,
            "narrator": narrator,
            "claim": claim,
            "truth_plane": "PENDING",
            "observation": {
                "text": f"Synthetic observation for {lobby} (demo).",
                "image": img_rel,
                "attention": attention,
            },
            "memory": memory,
        }

        appended = append_event(spine_path, event)

        print(f"[{i:03d}] {lobby:10s} | {narrator:12s} | {appended['hash'][:16]}")
        time.sleep(0.03)

    print(f"\n✅ {args.steps} spine entries written.")
    print(f"   Lint: python3 tools/evez.py lint --input {spine_path}")
    print(f"   Visualize: python3 tools/evez.py visualize-thought --input {spine_path}\n")


def _print_lint_result(res: LintResult, verbose: bool) -> None:
    status = "✅" if res.violations == 0 else "❌"
    print(f"Lint: {res.ok} OK, {res.warnings} warnings, {res.violations} violations {status}")
    if res.root_hash:
        print(f"Root hash: {res.root_hash}")
    if verbose and res.messages:
        print("\nDetails:")
        for m in res.messages[:200]:
            print(" - " + m)
        if len(res.messages) > 200:
            print(f" ... ({len(res.messages)-200} more)")


def cmd_lint(args: argparse.Namespace) -> None:
    path = Path(args.input).resolve()
    if not path.exists():
        print(f"No spine found at {path}")
        sys.exit(2)

    res = lint(path)
    _print_lint_result(res, verbose=args.verbose)
    if res.violations:
        sys.exit(1)


def cmd_visualize(args: argparse.Namespace) -> None:
    spine_path = Path(args.input).resolve()
    if not spine_path.exists():
        print(f"No spine found at {spine_path}")
        sys.exit(2)

    out_dir = Path(args.out).resolve()
    out = visualize_spine(
        spine_path=spine_path,
        out_dir=out_dir,
        title=args.title,
        fps=args.fps,
        max_steps=args.max_steps,
    )

    print(f"✅ Artifacts written to: {out.out_dir}")
    for p in out.artifacts:
        if p.exists():
            rel = p.relative_to(out.out_dir) if p.is_relative_to(out.out_dir) else p
            print(f" - {rel}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="evez", description="EVEZ-OS Visual Cognition Layer")
    sub = p.add_subparsers(dest="cmd")

    play = sub.add_parser("play", help="Generate a demo append-only spine")
    play.add_argument("--seed", type=int, default=42)
    play.add_argument("--steps", type=int, default=14)
    play.add_argument("--output", default=str(DEFAULT_SPINE))
    play.add_argument("--with-images", action="store_true", help="Also write synthetic observation PNGs (requires Pillow)")
    play.set_defaults(func=cmd_play)

    li = sub.add_parser("lint", help="Validate the append-only spine for integrity")
    li.add_argument("--input", default=str(DEFAULT_SPINE))
    li.add_argument("--verbose", action="store_true")
    li.set_defaults(func=cmd_lint)

    vz = sub.add_parser("visualize-thought", help="Generate cognition artifacts from a spine")
    vz.add_argument("--input", default=str(DEFAULT_SPINE))
    vz.add_argument("--out", default=str(REPO_ROOT / "artifacts"))
    vz.add_argument("--title", default="EVEZ Cognition Artifact")
    vz.add_argument("--fps", type=int, default=2)
    vz.add_argument("--max-steps", type=int, default=None)
    vz.set_defaults(func=cmd_visualize)

    return p


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
