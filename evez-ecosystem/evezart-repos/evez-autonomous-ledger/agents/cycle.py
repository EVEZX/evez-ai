#!/usr/bin/env python3
"""
CIPHER CYCLE v3 — Master Launcher
Runs ALL cipher engines in sequence. No stop. No delay.
Called by unified_daily.yml (08:00 UTC daily + manual dispatch).
"""
import os, sys, subprocess, datetime

def ts(): return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

ENGINES = [
    ("TRUNK",       "agents/cipher_trunk.py"),
    ("MANIFOLD",    "agents/cipher_manifold.py"),
    ("SPECULATIVE", "agents/cipher_speculative.py"),
    ("SKILL_SYNTH", "agents/cipher_skill_synth.py"),
    ("FIX",         "agents/cipher_fix.py"),
    ("BUILD",       "agents/cipher_build.py"),
]

print(f"\n{'='*65}")
print(f"CIPHER CYCLE v3 — {ts()}")
print(f"NO STOP. NO DELAY. {len(ENGINES)} ENGINES FIRING.")
print(f"{'='*65}\n")

results = {}
for name, script in ENGINES:
    if not os.path.exists(script):
        print(f"[{name:12s}] SKIP — {script} not found")
        results[name] = "SKIP"
        continue
    print(f"\n[{name:12s}] >>> {script}")
    try:
        r = subprocess.run([sys.executable, script], timeout=240, env={**os.environ})
        results[name] = "OK" if r.returncode == 0 else f"EXIT_{r.returncode}"
        print(f"[{name:12s}] {'✓' if r.returncode==0 else '⚠'} {results[name]}")
    except subprocess.TimeoutExpired:
        results[name] = "TIMEOUT"
        print(f"[{name:12s}] ⚠ TIMEOUT")
    except Exception as e:
        results[name] = f"ERR"
        print(f"[{name:12s}] ✗ {e}")

print(f"\n{'='*65}")
print("CYCLE COMPLETE:")
for name, status in results.items():
    icon = "✓" if status=="OK" else "↷" if status in ["SKIP","TIMEOUT"] else "✗"
    print(f"  {icon} {name:12s}: {status}")
print(f"\npoly_c=τ×ω×topo/2√N | append-only | no edits | ever")
print(f"witnessed: XyferViperZephyr | {ts()}")
print(f"{'='*65}")
