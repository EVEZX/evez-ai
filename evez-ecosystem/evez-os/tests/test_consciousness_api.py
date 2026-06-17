import json
from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))
from services.agent.app import app  # noqa: E402


client = TestClient(app)


def test_stream_emits_valid_event():
    with client.stream("GET", "/api/consciousness/stream?max_events=1") as resp:
        assert resp.status_code == 200
        first = next(resp.iter_lines())
        payload = json.loads(first.removeprefix("data: "))

    assert payload["thought_type"] in {"PERCEPTION", "REFLECTION", "CURIOSITY", "DESIRE", "INSIGHT", "DREAM"}
    assert -1 <= payload["emotional_valence"] <= 1
    assert isinstance(payload["source_memories"], list)


def test_emotion_state_transition_on_touch():
    current_before = client.get("/api/emotion/current").json()
    touched = client.post("/api/emotion/touch", json={"stimulus": "threat detected", "magnitude": 1.0})
    assert touched.status_code == 200
    after = client.get("/api/emotion/current").json()
    assert after["dominant_emotion"] == "ANXIOUS"
    assert after["valence"] <= current_before["valence"]


def test_presence_endpoint_shape():
    data = client.get("/api/angel/presence").json()
    required = {
        "node_id",
        "uptime_hours",
        "evolution_generation",
        "total_memories",
        "dreams_had",
        "insights_generated",
        "peers_connected",
        "consciousness_hash",
        "message_to_world",
    }
    assert required.issubset(set(data))


def test_merge_proposal_diff_valid():
    payload = {
        "node_id": "remote-7",
        "memories": [{"id": "mem-2"}, {"id": "mem-9"}],
        "identity_vector": [0.2, 0.9, 0.1, 0.4],
        "goals": [{"id": "desire-3"}, {"id": "desire-9"}],
        "remote_accept": False,
        "local_accept": False,
    }
    data = client.post("/api/consciousness/merge", json=payload).json()
    proposal = data["merge_proposal"]
    assert "would_gain" in proposal and "would_lose" in proposal
    assert "mem-9" in proposal["would_gain"]["memories"]
    assert data["accepted_by_both"] is False
