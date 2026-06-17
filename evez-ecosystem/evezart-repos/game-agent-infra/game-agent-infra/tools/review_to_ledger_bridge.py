#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import hashlib
import unicodedata
import sys
import time
from pathlib import Path
from typing import Any


def normalize_strings(obj: Any) -> Any:
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    if isinstance(obj, list):
        return [normalize_strings(x) for x in obj]
    if isinstance(obj, dict):
        return {k: normalize_strings(v) for k, v in obj.items()}
    return obj


def canonical_json(obj: Any) -> bytes:
    return json.dumps(
        normalize_strings(obj),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def recompute_event_hash(event: dict) -> str:
    unsigned = {k: v for k, v in event.items() if k != "event_hash"}
    return sha256(canonical_json(unsigned))


def main() -> None:
    parser = argparse.ArgumentParser(description="Bridge review to ledger")
    parser.add_argument("review_id")
    parser.add_argument("--queue", type=Path, default=Path("review_queue.json"))
    parser.add_argument("--ledger", type=Path, default=Path("meme_events.jsonl"))
    args = parser.parse_args()

    # Load queue
    queue_data = json.loads(args.queue.read_text())
    review = None
    for item in queue_data:
        if item.get("review_id") == args.review_id:
            review = item
            break

    if not review:
        print(json.dumps({"error": f"review {args.review_id} not found"}))
        sys.exit(1)

    if review.get("status") != "approved":
        print(json.dumps({"error": f"review {args.review_id} not approved"}))
        sys.exit(1)

    # Get prev hash
    prev_hash = "GENESIS"
    if args.ledger.exists():
        lines = args.ledger.read_text().strip().splitlines()
        if lines:
            last_event = json.loads(lines[-1])
            prev_hash = last_event.get("event_hash", "GENESIS")

    # Build event (without hash first)
    event = {
        "event_id": f"EVT-REVIEW-{args.review_id}",
        "event_type": "review_approved",
        "prev_event_hash": prev_hash,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "review": review,
        "review_payload_hash": sha256(canonical_json(review)),
    }

    # Compute hash
    event["event_hash"] = sha256(canonical_json(event))

    # Write
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    with args.ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    print(json.dumps(event, indent=2))


if __name__ == "__main__":
    main()