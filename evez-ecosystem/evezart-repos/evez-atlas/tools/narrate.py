#!/usr/bin/env python3
"""
Trace-driven narrator for EVEZ ARG / Game Agent Infra.

- Reads spine/EVENT_SPINE.jsonl (immutable event spine)
- Reads spine/ARG_SPINE.jsonl (diegetic drops, lenses, X-rays)
- Emits an in-universe narration that is *constrained by provenance*:
  it will never claim something happened unless a trace event supports it.
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                # keep going; spine must be resilient
                continue
    return out


def tail_jsonl(path: str, start_offset: int = 0) -> Iterable[Dict[str, Any]]:
    """Yield new JSON objects appended to a JSONL file."""
    with open(path, "r", encoding="utf-8") as f:
        # seek to start_offset lines
        for _ in range(start_offset):
            if not f.readline():
                break
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                time.sleep(0.25)
                f.seek(pos)
                continue
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def classify_lobby(evt: Dict[str, Any]) -> str:
    """Map events to lobbies (truth-planes)."""
    t = (evt.get("type") or "").lower()
    if t in ("fsc_cycle", "fsc", "collapse_cycle"):
        return "FSC_FORGE"
    if t in ("arg_drop", "xray_drop", "lense_drop", "lens_drop"):
        return "XRAY_ROOM"
    # heuristics by fields
    if "bgp" in json.dumps(evt).lower() or "asn" in json.dumps(evt).lower():
        return "PUBLIC_INTERNET"
    if "dns" in json.dumps(evt).lower() or "resolver" in json.dumps(evt).lower():
        return "PUBLIC_INTERNET"
    if "tls" in json.dumps(evt).lower() or "cert" in json.dumps(evt).lower():
        return "PUBLIC_INTERNET"
    if "matchmaking" in json.dumps(evt).lower() or "rollback" in json.dumps(evt).lower() or "ws" in json.dumps(evt).lower():
        return "GAME_BACKEND"
    # default mixed reality
    return "MIXED_REALITY"


def _clean(s: str) -> str:
    return " ".join((s or "").split())


def render_narration(evt: Dict[str, Any], mode: str = "spicy") -> str:
    lobby = classify_lobby(evt)
    t = evt.get("type") or "event"
    ts = _clean(evt.get("timestamp") or _utcnow())

    # tone controls (no slurs, no hate; profanity is allowed but not aimed at the user)
    if mode == "clean":
        spice = {"f": "", "a": "", "s": "", "b": ""}
    else:
        spice = {"f": "fuck", "a": "ass", "s": "shit", "b": "bullshit"}

    tone_bits = {
        "forensic": "" if mode == "clean" else "no fucking vibes, no mystical shortcuts",
        "internet": "" if mode == "clean" else "the internet does not care about your story",
        "backend": "" if mode == "clean" else "authority beats feelings, every damn time",
    }

    # build narration constrained by fields
    if lobby == "XRAY_ROOM":
        lens = _clean(evt.get("lens") or evt.get("lense") or "unknown-lens")
        title = _clean(evt.get("title") or evt.get("id") or "drop")
        content = _clean(evt.get("content") or evt.get("text") or "")
        prov = evt.get("provenance") or []
        prov_txt = f" provenance={len(prov)}" if prov else ""
        return (
            f"[{ts}] XRAY_ROOM::{lens} — {title}{prov_txt}\n"
            f"{content}\n"
        )

    if lobby == "FSC_FORGE":
        anomaly = _clean(evt.get("anomaly") or "unknown anomaly")
        sigma = evt.get("sigma_f") or evt.get("Sigma_f") or []
        omega = _clean(evt.get("omega") or evt.get("Omega") or "")
        measures = evt.get("measures") or {}
        # keep it visceral but factual
        return (
            f"[{ts}] FSC_FORGE — compression applied. the model cracked first at Σf={sigma}. "
            f"Ω survived as '{omega}'.\n"
            f"measures: dsr={measures.get('delta_surprise_residue',0)} dc={measures.get('delta_compression',0)} "
            f"stability={measures.get('stability',0)} transfer={measures.get('transfer',0)} "
            f"boundary={measures.get('boundary_clarity',0)} exploit={measures.get('exploit_resistance',0)}\n"
            f"anomaly: {anomaly}\n"
        )

    if lobby == "PUBLIC_INTERNET":
        summary = _clean(evt.get("summary") or evt.get("note") or evt.get("message") or "")
        if not summary:
            summary = _clean(json.dumps(evt)[:240])
        return (
            f"[{ts}] PUBLIC_INTERNET — the world argues about truth at line-rate. "
            f"you do not get one reality, you get convergence. {tone_bits['internet']}\n"
            f"{summary}\n"
        )

    if lobby == "GAME_BACKEND":
        summary = _clean(evt.get("summary") or evt.get("note") or evt.get("message") or "")
        if not summary:
            summary = _clean(json.dumps(evt)[:240])
        return (
            f"[{ts}] GAME_BACKEND — prediction makes it feel instant; authority makes it real. "
            f"rollback is the price tag. {tone_bits['backend']}\n"
            f"{summary}\n"
        )

    # mixed reality default
    summary = _clean(evt.get("summary") or evt.get("note") or evt.get("message") or "")
    if not summary:
        summary = _clean(json.dumps(evt)[:240])
    return (
        f"[{ts}] MIXED_REALITY — multiple layers impersonate each other. "
        f"your job is to stop trusting vibes and start trusting probes. {tone_bits['forensic']}\n"
        f"{summary}\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Trace-driven narrator for the EVEZ ARG stack.")
    ap.add_argument("--repo", default=".", help="Path to repo root (default: .)")
    ap.add_argument("--mode", choices=["clean", "spicy"], default="spicy", help="Narration tone.")
    ap.add_argument("--tail", action="store_true", help="Tail the spines and narrate live.")
    ap.add_argument("--last", type=int, default=20, help="Narrate last N events from EVENT_SPINE (default 20).")
    ap.add_argument("--out", default="", help="Write narration transcript to a file (append).")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    event_spine = os.path.join(repo, "spine", "EVENT_SPINE.jsonl")
    arg_spine = os.path.join(repo, "spine", "ARG_SPINE.jsonl")

    out_fh = None
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        out_fh = open(args.out, "a", encoding="utf-8")

    def emit(s: str):
        sys.stdout.write(s + ("\n" if not s.endswith("\n") else ""))
        sys.stdout.flush()
        if out_fh:
            out_fh.write(s + ("\n" if not s.endswith("\n") else ""))
            out_fh.flush()

    if not args.tail:
        evts = read_jsonl(event_spine)[-args.last:]
        drops = read_jsonl(arg_spine)[-max(0, args.last // 2):]
        # weave: interleave by timestamp if possible
        all_items = evts + drops
        def _ts(x):
            return x.get("timestamp") or ""
        all_items.sort(key=_ts)
        for e in all_items:
            emit(render_narration(e, mode=args.mode))
        if out_fh:
            out_fh.close()
        return 0

    # tail mode: narrate arg drops and events as they come in
    # start at end of existing file
    existing_events = read_jsonl(event_spine)
    existing_drops = read_jsonl(arg_spine)
    emit(f"[{_utcnow()}] narrator online. tailing spines.\n")

    # start tail generators
    ev_gen = tail_jsonl(event_spine, start_offset=len(existing_events))
    dr_gen = tail_jsonl(arg_spine, start_offset=len(existing_drops))

    # naive multiplex: poll in a round-robin
    while True:
        try:
            e = next(ev_gen)
            emit(render_narration(e, mode=args.mode))
        except StopIteration:
            pass
        except Exception:
            pass
        try:
            d = next(dr_gen)
            emit(render_narration(d, mode=args.mode))
        except StopIteration:
            pass
        except Exception:
            pass

    # unreachable
    # if out_fh: out_fh.close()
    # return 0


if __name__ == "__main__":
    raise SystemExit(main())
