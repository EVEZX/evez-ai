import base64
import gzip
import hashlib
import json

import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.mesh.pusher import ImmortalStatePusher
from agents.mesh.recovery import MeshRecoveryDaemon
from agents.mesh.registry import MeshPeer, MeshRegistry


class FakeBus:
    def __init__(self):
        self.events = []

    def emit(self, event, payload):
        self.events.append((event, payload))


@pytest.mark.asyncio
async def test_pushes_to_all_peers():
    calls = []

    async def push_ok(payload):
        calls.append(payload)
        return True

    async def pull_none():
        return None

    peers = [
        MeshPeer("p1", "e1", push_ok, pull_none, 1),
        MeshPeer("p2", "e2", push_ok, pull_none, 2),
        MeshPeer("p3", "e3", push_ok, pull_none, 3),
    ]

    registry = MeshRegistry(peers=peers)
    pusher = ImmortalStatePusher(
        registry=registry,
        state_provider=lambda: {
            "agent_version": "1.0",
            "temporal_chain_tip": "tip",
            "memory_snapshot": {},
            "gnn_topology": {},
            "eban_state": {},
            "lban_state": {},
            "wormhole_blob": {},
        },
    )

    event = await pusher.push_once()

    assert len(calls) >= 3
    assert event.success_count == 3


@pytest.mark.asyncio
async def test_recovery_selects_newest_valid_blob():
    def encode(version, ts):
        payload = {
            "agent_version": version,
            "temporal_chain_tip": "tip",
            "memory_snapshot": {},
            "gnn_topology": {},
            "eban_state": {},
            "lban_state": {},
            "wormhole_blob": {},
            "timestamp_ns": ts,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        payload["sha3_512_checksum"] = hashlib.sha3_512(canonical).hexdigest()
        return base64.b64encode(gzip.compress(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))).decode("utf-8")

    async def push_ok(_payload):
        return True

    newest_blob = encode("new", 200)
    older_blob = encode("old", 100)

    async def pull_newest():
        return newest_blob

    async def pull_old():
        return older_blob

    registry = MeshRegistry(
        peers=[
            MeshPeer("github_gist", "e1", push_ok, pull_old, 2),
            MeshPeer("ipfs_web3_storage", "e2", push_ok, pull_newest, 1),
        ]
    )

    restored = {}
    bus = FakeBus()
    daemon = MeshRecoveryDaemon(registry=registry, event_bus=bus, restore_fn=lambda payload: restored.update(payload))

    recovered = await daemon.recover_once()
    assert recovered is not None
    assert restored["agent_version"] == "new"
    assert bus.events[0][1]["source_peer"] == "ipfs_web3_storage"


@pytest.mark.asyncio
async def test_degraded_alert_fires_when_under_two_successes():
    alerts = []

    async def push_fail(_payload):
        return False

    async def push_ok(_payload):
        return True

    async def pull_none():
        return None

    registry = MeshRegistry(
        peers=[
            MeshPeer("p1", "e1", push_fail, pull_none, 1),
            MeshPeer("p2", "e2", push_ok, pull_none, 2),
            MeshPeer("p3", "e3", push_fail, pull_none, 3),
        ]
    )

    pusher = ImmortalStatePusher(
        registry=registry,
        state_provider=lambda: {
            "agent_version": "1.0",
            "temporal_chain_tip": "tip",
            "memory_snapshot": {},
            "gnn_topology": {},
            "eban_state": {},
            "lban_state": {},
            "wormhole_blob": {},
        },
        alert_fn=alerts.append,
    )

    event = await pusher.push_once()

    assert event.success_count == 1
    assert alerts == ["immortality mesh degraded"]
