"""Spine module — append-only event log operations.
Bridge module for tools/evez.py (v1.2.0 Visual Cognition Layer).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]

HASH_ALG = "sha256"
GENESIS_HASH = "0" * 64  # Genesis block hash — all zeros



@dataclass
class LintResult:
    ok: int = 0
    warnings: int = 0
    violations: int = 0
    root_hash: Optional[str] = None
    messages: List[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return self.violations == 0


def read_events(path: Path, limit: int = 0) -> List[Dict[str, Any]]:
    """Read spine events from JSONL file."""
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if limit > 0:
        events = events[-limit:]
    return events


def append_event(path: Path, event: Dict[str, Any]) -> Dict[str, Any]:
    """Append event to spine with auto-generated hash and timestamp.
    Args: path first, event second (matching tools/evez.py calling convention).
    Returns: event dict with 'hash' key added.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if "ts" not in event:
        event["ts"] = datetime.now(timezone.utc).isoformat()

    raw = json.dumps(event, sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256(raw.encode()).hexdigest()
    event["hash"] = h

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def lint(path: Path, limit: int = 200) -> LintResult:
    """Lint spine for integrity violations."""
    events = read_events(path, limit)
    result = LintResult()
    hashes = []

    for ev in events:
        kind = ev.get("kind") or ev.get("type") or ""
        h = ev.get("hash", "")
        if h:
            hashes.append(h)

        if kind == "claim":
            tp = (ev.get("truth_plane") or "theater").lower()
            if tp in ("truth", "pending") and (not ev.get("provenance") or not ev.get("falsifier")):
                result.violations += 1
                result.messages.append(f"speaking-rights violation: {ev.get('trace_id', '?')}")
            else:
                result.ok += 1
        elif kind.startswith("probe."):
            if not ev.get("ts") or not ev.get("target"):
                result.violations += 1
                result.messages.append(f"probe missing fields: {ev.get('trace_id', '?')}")
            else:
                result.ok += 1
        else:
            result.ok += 1

    # Compute root hash from all entry hashes
    if hashes:
        combined = "".join(hashes)
        result.root_hash = hashlib.sha256(combined.encode()).hexdigest()
    else:
        result.root_hash = None

    return result
