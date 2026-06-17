import importlib.util
import json
import os
from pathlib import Path

from fastapi.testclient import TestClient


os.environ.setdefault("SECRET_KEY", "test-secret")


def load_server_module():
    module_path = Path(__file__).resolve().parents[2] / "api" / "causal-chain-server.py"
    spec = importlib.util.spec_from_file_location("causal_chain_server", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_client():
    server = load_server_module()
    jubilee = __import__("src.api.jubilee_endpoints", fromlist=["repository"])
    ledger_path = Path(jubilee.repository.path)
    ledger_path.write_text("{}", encoding="utf-8")
    return TestClient(server.app), jubilee, ledger_path


def test_add_debt_requires_api_key():
    client, _jubilee, _path = get_client()
    response = client.post("/jubilee/add-debt", json={"account_id": "acct_123", "amount": 25})
    assert response.status_code == 401
    payload = response.json()["detail"]
    assert payload["code"] == "unauthorized"
    assert payload["message"] == "Missing API key"


def test_add_debt_rejects_invalid_api_key():
    client, _jubilee, _path = get_client()
    response = client.post(
        "/jubilee/add-debt",
        headers={"X-API-Key": "invalid"},
        json={"account_id": "acct_123", "amount": 25},
    )
    assert response.status_code == 401
    payload = response.json()["detail"]
    assert payload["code"] == "unauthorized"


def test_add_debt_validates_payload_and_persists():
    client, _jubilee, ledger_path = get_client()
    response = client.post(
        "/jubilee/add-debt",
        headers={"X-API-Key": "tier1_builder"},
        json={"account_id": "acct_123", "amount": 25.5},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["new_debt"] == 25.5

    stored = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert stored == {"acct_123": 25.5}


def test_add_debt_rejects_invalid_account_format():
    client, _jubilee, _path = get_client()
    response = client.post(
        "/jubilee/add-debt",
        headers={"X-API-Key": "tier1_builder"},
        json={"account_id": "bad account!", "amount": 25},
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("account_id" in str(item["loc"]) for item in errors)


def test_forgive_requires_api_key_and_updates_balance():
    client, _jubilee, _path = get_client()
    client.post(
        "/jubilee/add-debt",
        headers={"X-API-Key": "tier1_builder"},
        json={"account_id": "acct_123", "amount": 30},
    )

    response = client.post(
        "/jubilee/forgive",
        headers={"X-API-Key": "tier1_builder"},
        json={"account_id": "acct_123", "debt_amount": 10, "quantum_mode": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["old_debt"] == 30.0
    assert payload["new_debt"] == 20.0
    assert payload["mechanism"] == "classical_reduction"
