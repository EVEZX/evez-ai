#!/usr/bin/env python3
"""
Tier 1: self-auditing writer

A "claim" is allowed to exist in two planes:
  - truth-plane: requires provenance + falsifier + confidence + scope
  - theater-plane: allowed without those, but MUST be labeled theater

This module appends claim events to spine/EVENT_SPINE.jsonl.
"""
from __future__ import annotations
import datetime, json
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).resolve().parents[1]
SPINE = ROOT / "spine" / "EVENT_SPINE.jsonl"

def _utcnow() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def append_claim(text: str,
                 truth_plane: str,
                 provenance: Optional[str],
                 falsifier: Optional[str],
                 confidence: Optional[float],
                 scope: Optional[str],
                 tags: Optional[str] = None) -> Dict[str, Any]:
    truth_plane = truth_plane.lower().strip()
    if truth_plane not in ("truth", "pending", "theater"):
        truth_plane = "theater"

    event: Dict[str, Any] = {
        "kind": "claim",
        "ts": _utcnow(),
        "truth_plane": truth_plane,
        "text": text,
        "tags": [t for t in (tags or "").split(",") if t.strip()],
        "scope": scope,
        "provenance": provenance,
        "falsifier": falsifier,
        "confidence": confidence,
    }

    # enforce speaking rights: "truth" requires provenance+falsifier
    if truth_plane in ("truth", "pending"):
        if not provenance or not falsifier:
            # downgrade if missing requirements
            event["truth_plane"] = "theater"
            event["downgraded_reason"] = "missing provenance and/or falsifier"

    SPINE.parent.mkdir(parents=True, exist_ok=True)
    with SPINE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event
