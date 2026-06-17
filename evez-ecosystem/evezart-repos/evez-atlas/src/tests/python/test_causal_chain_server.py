import importlib.util
import json
import os
from pathlib import Path

from fastapi.testclient import TestClient


def load_server_module():
    module_path = Path(__file__).resolve().parents[2] / "api" / "causal-chain-server.py"
    spec = importlib.util.spec_from_file_location("causal_chain_server", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def setup_module(module):
    os.environ["SECRET_KEY"] = "test-secret"


def get_client():
    server = load_server_module()
    return TestClient(server.app), server


def test_tier0_redaction():
    client, _server = get_client()
    response = client.post(
        "/resolve-awareness",
        headers={"X-API-Key": "tier0_public"},
        json={"output_id": "output-001"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "stable"
    assert "builder" not in payload
    assert "trace" not in payload
    assert "metadata" not in payload


def test_tier3_full_access():
    client, _server = get_client()
    response = client.post(
        "/resolve-awareness",
        headers={"X-API-Key": "tier3_director"},
        json={"output_id": "output-001"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "stable"
    assert payload["builder"] == "omega-lab"
    assert payload["trace"] == ["node-a", "node-b", "node-c"]
    assert payload["metadata"]["region"] == "orion"


def test_invalid_api_key():
    client, _server = get_client()
    response = client.post(
        "/resolve-awareness",
        headers={"X-API-Key": "invalid"},
        json={"output_id": "output-001"},
    )
    assert response.status_code == 401


def test_audit_logging(tmp_path):
    client, server = get_client()
    audit_path = Path(server.AUDIT_LOG_PATH)
    audit_path.write_text("")

    response = client.post(
        "/resolve-awareness",
        headers={"X-API-Key": "tier1_builder"},
        json={"output_id": "output-001"},
    )
    assert response.status_code == 200

    response = client.get(
        "/legion-status",
        headers={"X-API-Key": "tier1_builder"},
    )
    assert response.status_code == 200

    lines = audit_path.read_text().strip().splitlines()
    assert len(lines) == 2
    first_entry = json.loads(lines[0])
    assert first_entry["endpoint"] == "/resolve-awareness"


def test_hmac_signature():
    client, server = get_client()
    response = client.post(
        "/resolve-awareness",
        headers={"X-API-Key": "tier2_admin"},
        json={"output_id": "output-002"},
    )
    assert response.status_code == 200
    payload = response.json()
    signature = payload.pop("signature")
    expected = server.hmac_sign(payload)
    assert signature == expected
