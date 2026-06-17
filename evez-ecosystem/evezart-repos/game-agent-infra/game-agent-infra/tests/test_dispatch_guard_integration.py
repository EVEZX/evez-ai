#!/usr/bin/env python3
"""
Integration test: Dispatch Guard + Review Queue + Ledger
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).parent.parent / "tools"


def create_test_queue(queue_path: Path):
    queue = [{
        "review_id": "RVW-TEST-001",
        "task_id": "TASK-001",
        "repo": "evez-autonomous-ledger",
        "action_type": "execute_agent",
        "payload_hash": "sha256:abc123",
        "requested_by": "A001_perception_witness",
        "status": "approved",
        "reviewer": "CAIN_A002",
    }]
    queue_path.write_text(json.dumps(queue, indent=2), encoding="utf-8")
    return queue[0]


def run_bridge(queue_path, ledger_path, review_id):
    result = subprocess.run(
        ["python3", str(BASE / "review_to_ledger_bridge.py"), review_id,
         "--queue", str(queue_path), "--ledger", str(ledger_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Bridge failed: {result.stderr}")
    return json.loads(result.stdout)


def run_guard(queue_path, ledger_path, review_id):
    result = subprocess.run(
        ["python3", str(BASE / "dispatch_guard.py"), review_id,
         "--queue", str(queue_path), "--ledger", str(ledger_path)],
        capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def test_happy_path():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        queue_path = td / "review_queue.json"
        ledger_path = td / "meme_events.jsonl"

        review_item = create_test_queue(queue_path)
        review_id = review_item["review_id"]

        bridge_event = run_bridge(queue_path, ledger_path, review_id)
        assert bridge_event["event_type"] == "review_approved"
        assert bridge_event["event_hash"] is not None

        guard_result = run_guard(queue_path, ledger_path, review_id)
        assert guard_result["cleared"] is True
        print("✓ test_happy_path PASSED")


def test_guard_blocks_unapproved():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        queue_path = td / "review_queue.json"
        ledger_path = td / "meme_events.jsonl"

        queue = [{"review_id": "RVW-TEST-002", "status": "pending"}]
        queue_path.write_text(json.dumps(queue, indent=2), encoding="utf-8")

        guard_result = run_guard(queue_path, ledger_path, "RVW-TEST-002")
        assert guard_result["denied"] is True
        assert guard_result["reason_code"] == "REVIEW_NOT_APPROVED"
        print("✓ test_guard_blocks_unapproved PASSED")


def test_guard_blocks_missing_ledger():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        queue_path = td / "review_queue.json"
        ledger_path = td / "meme_events.jsonl"

        review_item = create_test_queue(queue_path)
        review_id = review_item["review_id"]

        guard_result = run_guard(queue_path, ledger_path, review_id)
        assert guard_result["denied"] is True
        assert guard_result["reason_code"] in ("LEDGER_MISSING", "LEDGER_EVENT_MISSING")
        print("✓ test_guard_blocks_missing_ledger PASSED")


def test_guard_blocks_tampered_hash():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        queue_path = td / "review_queue.json"
        ledger_path = td / "meme_events.jsonl"

        review_item = create_test_queue(queue_path)
        review_id = review_item["review_id"]

        run_bridge(queue_path, ledger_path, review_id)

        ledger_data = ledger_path.read_text(encoding="utf-8")
        ledger_json = json.loads(ledger_data)
        ledger_json["event_hash"] = "sha256:corrupted"
        ledger_path.write_text(json.dumps(ledger_json), encoding="utf-8")

        guard_result = run_guard(queue_path, ledger_path, review_id)
        assert guard_result["denied"] is True
        assert guard_result["reason_code"] == "HASH_INVALID"
        print("✓ test_guard_blocks_tampered_hash PASSED")


def main():
    print("=" * 70)
    print("INTEGRATION TEST: Dispatch Guard + Review Queue + Ledger")
    print("=" * 70)

    try:
        test_happy_path()
        test_guard_blocks_unapproved()
        test_guard_blocks_missing_ledger()
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