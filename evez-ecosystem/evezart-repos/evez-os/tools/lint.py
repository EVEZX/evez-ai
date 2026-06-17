#!/usr/bin/env python3
"""
Lint the spine for speaking-rights violations.

Rules (minimal):
  - kind=="claim" in truth/pending must have provenance+falsifier, else violation
  - kind startswith "probe." must have target and ts
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

ROOT = Path(__file__).resolve().parents[1]
SPINE = ROOT / "spine" / "EVENT_SPINE.jsonl"

def lint(limit: int = 200) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if not SPINE.exists():
        return [], [{"error":"spine missing", "rule":"spine.exists"}]
    lines = SPINE.read_text(encoding="utf-8").splitlines()
    recent = lines[-limit:] if limit and len(lines) > limit else lines
    ok: List[Dict[str, Any]] = []
    bad: List[Dict[str, Any]] = []
    for i, ln in enumerate(recent):
        try:
            ev = json.loads(ln)
        except Exception:
            bad.append({"error":"invalid json", "line": ln[:200]})
            continue
        kind = ev.get("kind") or ev.get("type") or ""
        if kind == "claim":
            tp = (ev.get("truth_plane") or "theater").lower()
            if tp in ("truth","pending") and (not ev.get("provenance") or not ev.get("falsifier")):
                bad.append({"error":"speaking-rights violation", "rule":"claim.truth_requires_prov_fals", "event":ev})
            else:
                ok.append(ev)
        elif kind.startswith("probe."):
            if not ev.get("ts") or not ev.get("target"):
                bad.append({"error":"probe missing fields", "rule":"probe.requires_ts_target", "event":ev})
            else:
                ok.append(ev)
        else:
            ok.append(ev)
    return ok, bad
