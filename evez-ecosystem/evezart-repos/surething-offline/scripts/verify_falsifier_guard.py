#!/usr/bin/env python3
"""
Standalone verification script for api/index_falsifier_guard.py.

Runs two checks against the drop-in guarded operator ingress candidate:
1. Reject `.event` payloads with missing/null falsifier
2. Accept `.event` payloads with a valid falsifier

Usage:
    python scripts/verify_falsifier_guard.py
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.index_falsifier_guard import app


def main() -> int:
    client = TestClient(app)

    bad = client.post(
        "/spine/event",
        json={
            "event_type": "claim",
            "lane": "empirical",
            "payload": {
                "kind": "demo.event",
                "subject": "queue-health",
                "status": "degraded",
                "falsifier": None,
            },
        },
    )
    assert bad.status_code == 400, bad.text
    assert "missing falsifier field" in bad.text, bad.text

    good = client.post(
        "/spine/event",
        json={
            "event_type": "claim",
            "lane": "empirical",
            "payload": {
                "kind": "demo.event",
                "subject": "queue-health",
                "status": "degraded",
                "falsifier": "tx_id:demo-123",
            },
        },
    )
    assert good.status_code == 200, good.text
    body = good.json()
    assert body["ok"] is True
    assert isinstance(body["event_hash"], str) and body["event_hash"]
    assert isinstance(body["evidence_hash"], str) and body["evidence_hash"]
    assert body["height"] == 0

    print("falsifier guard verification: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
