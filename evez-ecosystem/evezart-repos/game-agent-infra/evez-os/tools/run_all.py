#!/usr/bin/env python3
"""
One-command runner: seeds spines (if empty), generates self-cartography, and prints a narrated "let's play"
transcript that is constrained by the immutable event spine.

Usage:
  python tools/run_all.py --seed --mode spicy
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPINE_DIR = os.path.join(REPO_ROOT, "spine")
EVENT_SPINE = os.path.join(SPINE_DIR, "EVENT_SPINE.jsonl")
ARG_SPINE = os.path.join(SPINE_DIR, "ARG_SPINE.jsonl")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_files():
    os.makedirs(SPINE_DIR, exist_ok=True)
    for p in (EVENT_SPINE, ARG_SPINE):
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write("")


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _append_jsonl(path: str, obj: Dict[str, Any]):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def seed_demo():
    """Seed a minimal but rich demo if spines are empty."""
    events = _read_jsonl(EVENT_SPINE)
    drops = _read_jsonl(ARG_SPINE)
    if events or drops:
        return False

    # Immutable events (truth spine): keep them plain, auditable.
    _append_jsonl(EVENT_SPINE, {
        "timestamp": _utcnow(),
        "type": "event",
        "layer": "public_internet",
        "summary": "DNS split-brain observed: LTE resolves new A/AAAA, Wi‑Fi resolver returns stale record. Pending purge/TTL convergence."
    })
    _append_jsonl(EVENT_SPINE, {
        "timestamp": _utcnow(),
        "type": "event",
        "layer": "public_internet",
        "summary": "BGP flap: prefix path changed twice within 90s; traceroute indicates alternate transit. User-perceived 'past path' invalidated after withdrawal."
    })
    _append_jsonl(EVENT_SPINE, {
        "timestamp": _utcnow(),
        "type": "event",
        "layer": "game_backend",
        "summary": "Rollback window widened from 120ms to 220ms after RTT p95 rose. Client prediction divergence increased; server reconciliation patch applied."
    })
    _append_jsonl(EVENT_SPINE, {
        "timestamp": _utcnow(),
        "type": "fsc_cycle",
        "cycle_id": "demo-0001",
        "anomaly": "Players report 'hit markers' that vanish after rollback; blame shifts between netcode and server auth.",
        "Sigma_f": ["pending_vs_final_confusion", "single_vantage_diagnosis"],
        "Omega": "two-vantage probing + explicit pending labels",
        "sigma_f": ["pending_vs_final_confusion", "single_vantage_diagnosis"],
        "omega": "two-vantage probing + explicit pending labels",
        "CS": ["story_first", "premature_finality", "metrics_over_truth"],
        "PS": ["append_only_spine", "compensation_events", "dual_vantage_probes"],
        "collapse_sequence": ["story_first", "premature_finality", "metrics_over_truth"],
        "preservation_set": ["append_only_spine", "compensation_events", "dual_vantage_probes"],
        "measures": {
            "delta_surprise_residue": 0.72,
            "delta_compression": 0.61,
            "stability": 0.66,
            "transfer": 0.59,
            "boundary_clarity": 0.74,
            "exploit_resistance": 0.58
        }
    })

    # Diegetic ARG drops (mutable projection layer) — still provenance-stamped.
    _append_jsonl(ARG_SPINE, {
        "timestamp": _utcnow(),
        "type": "arg_drop",
        "lens": "public_internet",
        "title": "Internet X-Ray: Naming is Reality",
        "content": "If your resolver lies, your world-map lies. Two vantages or you're worshipping one cache.",
        "provenance": [{"spine": "EVENT_SPINE.jsonl", "reason": "dns split-brain event"}]
    })
    _append_jsonl(ARG_SPINE, {
        "timestamp": _utcnow(),
        "type": "arg_drop",
        "lens": "game_backend",
        "title": "Internet X-Ray: Rollback is Paid-For Illusion",
        "content": "Client-side prediction is a performance lie you ship on purpose. Label pending state like you mean it, or the player will call your truth a bug.",
        "provenance": [{"spine": "EVENT_SPINE.jsonl", "reason": "rollback window change event"}]
    })
    return True


def run_self_cartography():
    cmd = [sys.executable, os.path.join(REPO_ROOT, "tools", "self_cartography.py")]
    subprocess.check_call(cmd, cwd=REPO_ROOT)


def run_narrator(mode: str, last: int, out_path: str):
    cmd = [
        sys.executable, os.path.join(REPO_ROOT, "tools", "narrate.py"),
        "--repo", REPO_ROOT,
        "--mode", mode,
        "--last", str(last),
    ]
    if out_path:
        cmd += ["--out", out_path]
    subprocess.check_call(cmd, cwd=REPO_ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the EVEZ stack demo: seed -> cartography -> narration.")
    ap.add_argument("--seed", action="store_true", help="Seed demo data if spines are empty.")
    ap.add_argument("--mode", choices=["clean", "spicy"], default="spicy")
    ap.add_argument("--last", type=int, default=40, help="Narrate last N items.")
    ap.add_argument("--out", default=os.path.join(REPO_ROOT, "docs", "LET_PLAY_TRANSCRIPT.txt"),
                    help="Output transcript path.")
    args = ap.parse_args()

    _ensure_files()
    if args.seed:
        seeded = seed_demo()
        if seeded:
            print("seeded demo spines.")
        else:
            print("spines already non-empty; skipped seeding.")

    # Generate cartography artifacts
    run_self_cartography()

    # Generate narration transcript
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    run_narrator(args.mode, args.last, args.out)

    print(f"\nDone. Transcript: {os.path.relpath(args.out, REPO_ROOT)}")
    print("Cartography: docs/SELF_CARTOGRAPHY.mmd + docs/SELF_CARTOGRAPHY.dot")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
