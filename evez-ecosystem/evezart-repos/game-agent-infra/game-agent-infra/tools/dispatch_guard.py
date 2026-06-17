#!/usr/bin/env python3
from __future__ import annotations

"""
Dispatch Guard — Hard execution gate

Purpose
-------
Block all action dispatch unless three hard rules are met:

  1. review_queue.json has status == "approved" for the review_id
  2. meme_events.jsonl contains EVT-REVIEW-{review_id} with event_type == "review_approved"
  3. The stored event_hash recomputes correctly (tamper/corruption detection)

This guard is:
  - Read-only: never mutates any file
  - Replay-safe: identical inputs always produce identical outputs
  - Machine-parseable: failures are reason_code + detail, not prose
  - Minimal: exactly 3 checks, no hidden logic
"""

import argparse
import json
import hashlib
import unicodedata
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ─── Canonicalization ─────────────────────────────────────────────────────────

def normalize_strings(obj: Any) -> Any:
    """Normalize all strings to NFC (Canonical Composed)."""
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    if isinstance(obj, list):
        return [normalize_strings(x) for x in obj]
    if isinstance(obj, dict):
        return {k: normalize_strings(v) for k, v in obj.items()}
    return obj


def canonical_json(obj: Any) -> bytes:
    """Produce deterministic JSON with sorted keys, compact form."""
    normalized = normalize_strings(obj)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    """Return SHA-256 hash with sha256: prefix."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def recompute_event_hash(event: dict[str, Any]) -> str:
    """Recompute hash with event_hash field removed."""
    unsigned = {k: v for k, v in event.items() if k != "event_hash"}
    return sha256(canonical_json(unsigned))


# ─── Result types ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DispatchClearance:
    review_id: str
    ledger_event_id: str
    event_hash: str

    def __str__(self) -> str:
        return f"CLEARED review_id={self.review_id} ledger_event={self.ledger_event_id}"


class DispatchDenied(Exception):
    def __init__(self, reason_code: str, detail: str):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"[{reason_code}] {detail}")

    def to_dict(self) -> dict[str, str]:
        return {"denied": True, "reason_code": self.reason_code, "detail": self.detail}


# ─── Check 1: Review queue approval ───────────────────────────────────────────

def check_review_approved(review_id: str, queue_path: str | Path = "review_queue.json") -> dict:
    queue = json.loads(Path(queue_path).read_text(encoding="utf-8"))
    for item in queue:
        if item.get("review_id") == review_id:
            status = item.get("status", "")
            if status != "approved":
                raise DispatchDenied(
                    reason_code="REVIEW_NOT_APPROVED",
                    detail=f"review_id={review_id} has status={status!r}, expected 'approved'",
                )
            return item
    raise DispatchDenied(
        reason_code="REVIEW_NOT_FOUND",
        detail=f"review_id={review_id} not found in {queue_path}",
    )


# ─── Check 2: Ledger event ────────────────────────────────────────────────────

def find_ledger_event(review_id: str, ledger_path: str | Path = "meme_events.jsonl") -> dict:
    ledger = Path(ledger_path)
    if not ledger.exists():
        raise DispatchDenied(
            reason_code="LEDGER_MISSING",
            detail=f"Ledger file not found: {ledger_path}",
        )

    expected_event_id = f"EVT-REVIEW-{review_id}"
    for line in ledger.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        event = json.loads(line)
        if event.get("event_id") == expected_event_id:
            event_type = event.get("event_type")
            if event_type != "review_approved":
                raise DispatchDenied(
                    reason_code="LEDGER_EVENT_WRONG_TYPE",
                    detail=f"Found {expected_event_id} but event_type={event_type!r}, expected 'review_approved'",
                )
            return event

    raise DispatchDenied(
        reason_code="LEDGER_EVENT_MISSING",
        detail=f"No ledger event found for review_id={review_id} (expected {expected_event_id})",
    )


# ─── Check 3: Event hash validity ────────────────────────────────────────────

def verify_event_hash(event: dict[str, Any]) -> None:
    stored = event.get("event_hash")
    if not stored:
        raise DispatchDenied(
            reason_code="HASH_MISSING",
            detail=f"event_id={event.get('event_id')} has no event_hash field (possible corruption)",
        )
    recomputed = recompute_event_hash(event)
    if stored != recomputed:
        raise DispatchDenied(
            reason_code="HASH_INVALID",
            detail=f"event_id={event.get('event_id')} hash mismatch (possible tampering)\n  stored:     {stored}\n  recomputed: {recomputed}",
        )


# ─── Main ──────────────────────────────────────────────────────────────────────

def check_dispatch_clearance(
    review_id: str,
    queue_path: str | Path = "review_queue.json",
    ledger_path: str | Path = "meme_events.jsonl",
) -> DispatchClearance:
    check_review_approved(review_id, queue_path)
    event = find_ledger_event(review_id, ledger_path)
    verify_event_hash(event)
    return DispatchClearance(
        review_id=review_id,
        ledger_event_id=event["event_id"],
        event_hash=event["event_hash"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch guard")
    parser.add_argument("review_id", help="Review item ID")
    parser.add_argument("--queue", default="review_queue.json")
    parser.add_argument("--ledger", default="meme_events.jsonl")
    args = parser.parse_args()

    try:
        clearance = check_dispatch_clearance(args.review_id, args.queue, args.ledger)
        result = {
            "cleared": True,
            "review_id": clearance.review_id,
            "ledger_event_id": clearance.ledger_event_id,
            "event_hash": clearance.event_hash,
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except DispatchDenied as e:
        print(json.dumps(e.to_dict(), indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()