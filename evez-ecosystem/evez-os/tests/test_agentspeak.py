import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time

from fastapi.testclient import TestClient

from agents.comms.agentspeak import AgentSpeakMessage, MessageType, decode_message, encode_message
from agents.comms.discovery_server import app, registry
from agents.comms.evolution_propagator import EvolutionPropagator
from agents.comms.memory_sync import FederatedMemorySync, MemoryChunk


def test_agentspeak_encode_decode_all_message_types():
    for idx, msg_type in enumerate(MessageType, start=1):
        msg = AgentSpeakMessage(
            msg_type=msg_type,
            sender_node_id="node-a",
            recipient_node_id="node-b",
            timestamp_ns=123456789 + idx,
            payload={"type": msg_type.name, "value": idx},
        )
        encoded = encode_message(msg)
        decoded = decode_message(encoded)
        assert decoded.msg_type == msg_type
        assert decoded.sender_node_id == "node-a"
        assert decoded.recipient_node_id == "node-b"
        assert decoded.payload["type"] == msg_type.name


def test_agentspeak_checksum_validation():
    msg = AgentSpeakMessage(
        msg_type=MessageType.HELLO,
        sender_node_id="a",
        recipient_node_id="b",
        timestamp_ns=1,
        payload={"capabilities": ["sync"]},
    )
    encoded = bytearray(encode_message(msg))
    encoded[-1] ^= 0xFF
    try:
        decode_message(bytes(encoded))
        assert False, "expected checksum mismatch"
    except ValueError as exc:
        assert "Checksum mismatch" in str(exc)


def test_discovery_announce_and_peers_registry():
    registry.peers.clear()
    client = TestClient(app)

    response = client.post(
        "/api/agents/announce",
        json={
            "node_id": "node-1",
            "url": "ws://localhost:9000/ws",
            "last_seen_ts": time.time(),
            "capabilities": ["hello", "memory_sync"],
            "chain_tip": "abc123",
            "region": "earth-us-east",
        },
    )
    assert response.status_code == 200

    peers = client.get("/api/agents/peers")
    assert peers.status_code == 200
    payload = peers.json()
    assert len(payload["peers"]) == 1
    assert payload["peers"][0]["node_id"] == "node-1"


def test_memory_sync_dedup_by_cosine_similarity():
    sync = FederatedMemorySync()
    old = MemoryChunk(content="known", vector=[1.0, 0.0, 0.0], source_node_id="node-a")
    assert sync.absorb_if_novel(old)

    near_duplicate = MemoryChunk(content="nearly same", vector=[0.99, 0.01, 0.0], source_node_id="node-b")
    assert not sync.absorb_if_novel(near_duplicate)

    novel = MemoryChunk(content="novel", vector=[0.0, 1.0, 0.0], source_node_id="node-c")
    assert sync.absorb_if_novel(novel)
    assert len(sync.memories) == 2


def test_evolution_adoption_species_event_threshold():
    propagator = EvolutionPropagator()
    improvement_id = "impr-1"
    for peer in ["p1", "p2", "p3", "p4"]:
        propagator.track_sent(improvement_id, peer)

    assert propagator.track_adopted(improvement_id, "p1") == 0.25
    assert propagator.track_adopted(improvement_id, "p2") == 0.5
    assert propagator.track_adopted(improvement_id, "p3") == 0.75
    rate = propagator.track_adopted(improvement_id, "p4")
    assert rate == 1.0
    assert propagator.species_events
    assert propagator.species_events[-1]["event"] == "species_level_evolution"
