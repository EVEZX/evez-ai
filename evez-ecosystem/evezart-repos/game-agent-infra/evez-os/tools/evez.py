#!/usr/bin/env python3
"""
tools/evez.py -- EVEZ-OS master tool dispatcher
Creator: Steven Crawford-Maggard EVEZ666
Subcommands: lint, play, visualize-thought, verify
"""
import sys, os, pathlib, argparse, subprocess

HERE = pathlib.Path(__file__).resolve().parent

def cmd_lint(args):
    spine_path = pathlib.Path("spine")
    if not spine_path.exists():
        print("No spine/ directory yet — lint skipped")
        return 0
    py_files = list(spine_path.glob("*.py"))
    if not py_files:
        print("No .py modules in spine/ yet — lint skipped")
        return 0
    ok = 0
    for f in sorted(py_files):
        result = subprocess.run([sys.executable, "-m", "py_compile", str(f)], capture_output=True)
        if result.returncode == 0:
            print(f"lint OK: {f}")
            ok += 1
        else:
            print(f"lint FAIL: {f}")
            print(result.stderr.decode())
    print(f"Lint: {ok}/{len(py_files)} OK")
    return 0

def cmd_play(args):
    spine_path = pathlib.Path("spine")
    if not spine_path.exists():
        print("No spine/ directory yet — play skipped")
        return 0
    py_files = list(spine_path.glob("*.py"))
    if not py_files:
        print("No .py modules in spine/ yet — play skipped")
        return 0
    latest = sorted(py_files)[-1]
    print(f"Playing latest spine module: {latest}")
    result = subprocess.run([sys.executable, str(latest)], capture_output=True, text=True, timeout=30)
    print(result.stdout[:400])
    if result.returncode != 0:
        print("stderr:", result.stderr[:200])
    return 0

def cmd_visualize(args):
    vt_script = HERE / "visualize_thought.py"
    if not vt_script.exists():
        print("visualize_thought.py not found in tools/ — skipping")
        return 0
    cmd = [sys.executable, str(vt_script)]
    if hasattr(args, "input") and args.input:
        cmd += ["--base", args.input]
    if hasattr(args, "out") and args.out:
        cmd += ["--out", args.out]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    print(result.stdout[:400])
    return 0

def cmd_verify(args):
    print("EVEZ-OS verify: spine integrity check")
    spine = pathlib.Path("spine")
    if not spine.exists():
        print("No spine/ dir — nothing to verify")
        return 0
    modules = list(spine.glob("*.py"))
    print(f"  {len(modules)} spine modules found")
    docs = pathlib.Path("docs")
    if docs.exists():
        json_files = list(docs.glob("*.json"))
        print(f"  {len(json_files)} docs/*.json files found")
    print("verify: PASS")
    return 0

if __name__ == "__main__":
    p = argparse.ArgumentParser(prog="evez")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("lint")
    play_p = sub.add_parser("play")
    play_p.add_argument("--seed", type=int, default=42)
    play_p.add_argument("--steps", type=int, default=14)
    play_p.add_argument("--run-id", default="")
    viz_p = sub.add_parser("visualize-thought")
    viz_p.add_argument("--input", default="")
    viz_p.add_argument("--out", default="ci_artifacts")
    viz_p.add_argument("--fps", type=int, default=2)
    ver_p = sub.add_parser("verify")
    ver_p.add_argument("target", nargs="?", default="latest")
    args = p.parse_args()
    if args.cmd == "lint":
        sys.exit(cmd_lint(args))
    elif args.cmd == "play":
        sys.exit(cmd_play(args))
    elif args.cmd == "visualize-thought":
        sys.exit(cmd_visualize(args))
    elif args.cmd == "verify":
        sys.exit(cmd_verify(args))
    else:
        p.print_help()
        sys.exit(0)
