from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ingest_isolation():
    payload = {
        "event_id": "iso_001",
        "source": "esiu",
        "severity": "high",
        "description": "test isolation",
        "decision": {
            "mode": "quarantine",
            "actions": ["disable_workflow"],
            "principles": ["preserve_evidence"],
        },
    }
    r = client.post("/api/telemetry/isolation", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "accepted"
    assert data["event_id"] == "iso_001"

    r2 = client.get("/api/telemetry/isolation/iso_001")
    assert r2.status_code == 200
    body = r2.json()
    assert body["event_id"] == "iso_001"
    assert body["decision"]["mode"] == "quarantine"
