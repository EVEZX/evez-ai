#!/usr/bin/env python3
"""
Integration test: Dispatch Guard + Review Queue + Ledger

This test validates the complete chain:
  review_queue.json → review_to_ledger_bridge.py → meme_events.jsonl → dispatch_guard.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

# Resolve paths relative to this test file
BASE = Path(__file__).parent.parent / "tools"


def create_test_queue(queue_path: Path) -> dict[str, Any]:
    """Create a test review_queue.json with one approved item."""
    queue = [
        {
            "review_id": "RVW-TEST-001",
            "task_id": "TASK-001",
            "repo": "evez-autonomous-ledger",
            "action_type": "execute_agent",
            "payload_hash": "sha256:abc123",
            "requested_by": "A001_perception_witness",
            "status": "approved",
            "reviewer": "CAIN_A002",
            "reviewer_note": "Agent state and ledger in sync.",
        }
    ]
    queue_path.write_text(json.dumps(queue, indent=2), encoding="utf-8")
    return queue[0]


def run_bridge(queue_path: Path, ledger_path: Path, review_id: str) -> dict[str, Any]:
    """Run review_to_ledger_bridge.py to emit a ledger event."""
    result = subprocess.run(
        [
            "python3",
            str(BASE / "review_to_ledger_bridge.py"),
            review_id,
            "--queue", str(queue_path),
            "--ledger", str(ledger_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Bridge failed: {result.stderr}")
    return json.loads(result.stdout)


def run_guard(queue_path: Path, ledger_path: Path, review_id: str) -> dict[str, Any]:
    """Run dispatch_guard.py to check clearance."""
    result = subprocess.run(
        [
            "python3",
            str(BASE / "dispatch_guard.py"),
            review_id,
            "--queue", str(queue_path),
            "--ledger", str(ledger_path),
        ],
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_happy_path() -> None:
    """Test: Guard clears a properly approved review."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        queue_path = tmpdir / "review_queue.json"
        ledger_path = tmpdir / "meme_events.jsonl"

        review_item = create_test_queue(queue_path)
        review_id = review_item["review_id"]

        bridge_event = run_bridge(queue_path, ledger_path, review_id)
        assert bridge_event["event_type"] == "review_approved"
        assert bridge_event["event_hash"] is not None

        guard_result = run_guard(queue_path, ledger_path, review_id)
        assert guard_result["cleared"] is True
        assert guard_result["review_id"] == review_id

        print("✓ test_happy_path PASSED")


def test_guard_blocks_unapproved_review() -> None:
    """Test: Guard blocks a review with status != 'approved'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        queue_path = tmpdir / "review_queue.json"
        ledger_path = tmpdir / "meme_events.jsonl"

        queue = [
            {
                "review_id": "RVW-TEST-002",
                "task_id": "TASK-002",
                "repo": "evez-autonomous-ledger",
                "action_type": "execute_agent",
                "payload_hash": "sha256:def456",
                "requested_by": "A001_perception_witness",
                "status": "pending",
            }
        ]
        queue_path.write_text(json.dumps(queue, indent=2), encoding="utf-8")

        guard_result = run_guard(queue_path, ledger_path, "RVW-TEST-002")
        assert guard_result["denied"] is True
        assert guard_result["reason_code"] == "REVIEW_NOT_APPROVED"

        print("✓ test_guard_blocks_unapproved_review PASSED")


def test_guard_blocks_missing_ledger_event() -> None:
    """Test: Guard blocks if ledger event is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        queue_path = tmpdir / "review_queue.json"
        ledger_path = tmpdir / "meme_events.jsonl"

        review_item = create_test_queue(queue_path)
        review_id = review_item["review_id"]

        guard_result = run_guard(queue_path, ledger_path, review_id)
        assert guard_result["denied"] is True
        assert guard_result["reason_code"] == "LEDGER_MISSING"

        print("✓ test_guard_blocks_missing_ledger_event PASSED")


def test_guard_blocks_tampered_hash() -> None:
    """Test: Guard blocks if event_hash is corrupted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        queue_path = tmpdir / "review_queue.json"
        ledger_path = tmpdir / "meme_events.jsonl"

        review_item = create_test_queue(queue_path)
        review_id = review_item["review_id"]

        run_bridge(queue_path, ledger_path, review_id)

        ledger_data = ledger_path.read_text(encoding="utf-8")
        ledger_json = json.loads(ledger_data)
        ledger_json["event_hash"] = "sha256:corrupted_hash_value_xyz123"
        ledger_path.write_text(json.dumps(ledger_json), encoding="utf-8")

        guard_result = run_guard(queue_path, ledger_path, review_id)
        assert guard_result["denied"] is True
        assert guard_result["reason_code"] == "HASH_INVALID"

        print("✓ test_guard_blocks_tampered_hash PASSED")


def main() -> None:
    print("=" * 70)
    print("INTEGRATION TEST: Dispatch Guard + Review Queue + Ledger")
    print("=" * 70)

    try:
        test_happy_path()
        test_guard_blocks_unapproved_review()
        test_guard_blocks_missing_ledger_event()
        test_guard_blocks_tampered_hash()

        print("=" * 70)
        print("ALL TESTS PASSED")
        print("=" * 70)
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()