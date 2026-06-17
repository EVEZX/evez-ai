#!/usr/bin/env python3
"""
llm_bridge.py
Portable validator + spine appender for LLM "Turn Packets".

Design:
- LLM outputs JSON (Turn Packet)
- Local runner validates speaking-rights gate (TRUTH requires provenance + falsifier)
- Local runner appends normalized events to append-only spine JSONL

This keeps ChatGPT/Perplexity interchangeable and prevents "winning by sounding like it won".
"""
from __future__ import annotations

import argparse, json, hashlib, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def stable_hash(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def load_turn(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Turn packet must be a JSON object.")
    return data

def validate_turn(turn: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    for k in ["episode","claims","probes","sigma_f","omega","next"]:
        if k not in turn:
            errs.append(f"missing key: {k}")
    claims = turn.get("claims", [])
    if not isinstance(claims, list):
        errs.append("claims must be a list")
        return errs
    for c in claims:
        if not isinstance(c, dict):
            errs.append("claim entry must be object")
            continue
        tp = c.get("truth_plane","")
        if tp == "TRUTH":
            if not str(c.get("provenance","")).strip():
                errs.append(f"TRUTH claim missing provenance: {c.get('id')}")
            if not str(c.get("falsifier","")).strip():
                errs.append(f"TRUTH claim missing falsifier: {c.get('id')}")
    return errs

def append_events(turn: Dict[str, Any], spine_path: Path) -> int:
    spine_path.parent.mkdir(parents=True, exist_ok=True)

    ts = now_iso()
    events = []

    # top-level turn event
    turn_event = {
        "kind": "llm.turn",
        "ts": ts,
        "trace_id": "T" + stable_hash(turn)[:16],
        "episode": turn.get("episode", {}),
        "payload": {"next": turn.get("next","")}
    }
    events.append(turn_event)

    for c in turn.get("claims", []):
        ev = {
            "kind": "llm.claim",
            "ts": ts,
            "trace_id": "C" + stable_hash(c)[:16],
            "episode": turn.get("episode", {}),
            "payload": c
        }
        events.append(ev)

    for p in turn.get("probes", []):
        ev = {
            "kind": "llm.probe_request",
            "ts": ts,
            "trace_id": "P" + stable_hash(p)[:16],
            "episode": turn.get("episode", {}),
            "vantage_id": p.get("vantage_id",""),
            "payload": p
        }
        events.append(ev)

    # Σf / Ω as events (optional)
    for s in turn.get("sigma_f", []):
        events.append({
            "kind": "fsc.sigma_f",
            "ts": ts,
            "trace_id": "SF" + stable_hash({"s":s,"ep":turn.get("episode",{})})[:16],
            "episode": turn.get("episode", {}),
            "payload": {"sigma_f": s}
        })
    for o in turn.get("omega", []):
        events.append({
            "kind": "fsc.omega",
            "ts": ts,
            "trace_id": "OM" + stable_hash({"o":o,"ep":turn.get("episode",{})})[:16],
            "episode": turn.get("episode", {}),
            "payload": {"omega": o}
        })

    with spine_path.open("a", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return len(events)

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Validate a Turn Packet JSON")
    v.add_argument("turn_json", type=Path)

    a = sub.add_parser("append", help="Append a Turn Packet to the spine")
    a.add_argument("turn_json", type=Path)
    a.add_argument("--spine", type=Path, default=Path("spine/EVENT_SPINE.jsonl"))

    args = ap.parse_args()

    turn = load_turn(args.turn_json)
    errs = validate_turn(turn)
    if args.cmd == "validate":
        if errs:
            for e in errs:
                print("ERROR:", e, file=sys.stderr)
            sys.exit(2)
        print("OK")
        return

    if errs:
        for e in errs:
            print("ERROR:", e, file=sys.stderr)
        sys.exit(2)

    n = append_events(turn, args.spine)
    print(f"Appended {n} event(s) to {args.spine}")

if __name__ == "__main__":
    main()
