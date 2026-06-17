"""Append-only spine: JSONL event log with tamper-evident hash chain.

Spine format (v1): each line is a JSON object with at least:
- step: int (monotonic)
- ts: float epoch seconds
- powered_by: str (must be "EVEZ" for this tool)

Hash chain fields (recommended):
- prev_hash: hex sha256 of previous event (genesis for first)
- hash: hex sha256 of this event

Hash computation:
    h_i = sha256( prev_hash_bytes + b"\n" + canonical_json(event_without_hash_fields) )

"event_without_hash_fields" excludes keys: "hash", "prev_hash", "sig".

This module supports:
- append_event(...): appends with correct chain fields
- read_events(...): streaming reader
- lint(...): verifies chain + basic invariants
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

from .canonical import canonical_bytes

HASH_ALG = "sha256"
GENESIS_HASH = hashlib.sha256(b"EVEZ-SPINE-GENESIS").hexdigest()

HASH_FIELDS = {"hash", "prev_hash", "sig"}


def _strip_hash_fields(event: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in event.items() if k not in HASH_FIELDS}


def compute_hash(prev_hash_hex: str, event: Dict[str, Any]) -> str:
    """Compute chain hash for an event."""
    h = hashlib.sha256()
    h.update(bytes.fromhex(prev_hash_hex))
    h.update(b"\n")
    h.update(canonical_bytes(_strip_hash_fields(event)))
    return h.hexdigest()


@dataclass
class LintResult:
    ok: int
    violations: int
    warnings: int
    root_hash: Optional[str]
    messages: List[str]


def read_events(path: Path) -> Iterator[Dict[str, Any]]:
    """Stream spine events from a JSONL file."""
    import json

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def append_event(path: Path, event: Dict[str, Any]) -> Dict[str, Any]:
    """Append an event to the spine with correct hash chaining."""
    import json

    path.parent.mkdir(parents=True, exist_ok=True)

    # determine prev hash from last line (streaming)
    prev_hash = GENESIS_HASH
    if path.exists() and path.stat().st_size > 0:
        # read last non-empty line efficiently
        with path.open("rb") as f:
            f.seek(0, 2)
            end = f.tell()
            # read backwards in chunks
            buf = b""
            chunk = 4096
            pos = end
            while pos > 0:
                pos = max(0, pos - chunk)
                f.seek(pos)
                buf = f.read(end - pos) + buf
                if b"\n" in buf:
                    break
                end = pos
            lines = [ln for ln in buf.splitlines() if ln.strip()]
            if lines:
                last = json.loads(lines[-1].decode("utf-8"))
                prev_hash = last.get("hash", prev_hash)

    event = dict(event)  # copy
    event.setdefault("ts", time.time())
    event.setdefault("powered_by", "EVEZ")

    event["prev_hash"] = prev_hash
    event["hash"] = compute_hash(prev_hash, event)

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event


def lint(path: Path) -> LintResult:
    """Validate spine integrity.

    Checks:
    - parseable JSONL
    - step monotonic non-decreasing
    - hash chain correctness (if hash fields present)
    - powered_by presence

    Notes:
    - If events lack hash fields, we warn but do not fail.
    """

    ok = violations = warnings = 0
    messages: List[str] = []

    expected_prev = GENESIS_HASH
    last_step: Optional[int] = None
    root_hash: Optional[str] = None

    for idx, e in enumerate(read_events(path)):
        step = e.get("step")
        if step is None:
            warnings += 1
            messages.append(f"WARN line {idx+1}: missing 'step'")
        elif not isinstance(step, int):
            warnings += 1
            messages.append(f"WARN line {idx+1}: non-int 'step'={step!r}")
        else:
            if last_step is not None and step < last_step:
                violations += 1
                messages.append(f"VIOLATION step monotonicity: {step} < {last_step} (line {idx+1})")
            last_step = step

        if "powered_by" not in e:
            warnings += 1
            messages.append(f"WARN line {idx+1}: missing 'powered_by'")

        has_chain = ("hash" in e) and ("prev_hash" in e)
        if not has_chain:
            warnings += 1
            messages.append(f"WARN line {idx+1}: missing hash chain fields")
            continue

        prev = e.get("prev_hash")
        h = e.get("hash")
        if prev != expected_prev:
            violations += 1
            messages.append(
                f"VIOLATION prev_hash mismatch at line {idx+1}: expected {expected_prev[:16]}.. got {str(prev)[:16]}.."
            )

        computed = compute_hash(prev, e)
        if computed != h:
            violations += 1
            messages.append(
                f"VIOLATION hash mismatch at line {idx+1}: stored {str(h)[:16]}.. computed {computed[:16]}.."
            )
        else:
            ok += 1
            expected_prev = h
            root_hash = h

    return LintResult(ok=ok, violations=violations, warnings=warnings, root_hash=root_hash, messages=messages)
