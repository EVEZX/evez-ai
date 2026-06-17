from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from agents.mesh.registry import MeshPeer, MeshRegistry

GIST_NAME = "evezbrain-mesh-bootstrap"


class PeerDiscoveryBootstrap:
    def __init__(self, registry: MeshRegistry, gist_client: Any, handshake_fn: Any) -> None:
        self.registry = registry
        self.gist_client = gist_client
        self.handshake_fn = handshake_fn

    async def publish_alive_record(self, railway_url: str) -> bool:
        record = {
            "railway_url": railway_url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "instance": os.getenv("RAILWAY_REPLICA_ID", "unknown"),
        }
        return await self.gist_client.upsert_json(GIST_NAME, record)

    async def bootstrap_peers(self) -> List[str]:
        doc = await self.gist_client.read_json(GIST_NAME)
        urls = doc.get("peers", []) if isinstance(doc, dict) else []
        added: List[str] = []
        for url in urls:
            ok = await self.handshake_fn(url)
            if not ok:
                continue
            peer = MeshPeer(
                name=f"railway_{len(self.registry.peers) + 1}",
                endpoint=url,
                push_fn=lambda payload, endpoint=url: self.gist_client.forward_push(endpoint, payload),
                pull_fn=lambda endpoint=url: self.gist_client.forward_pull(endpoint),
                priority=5,
                sync_interval_s=600,
            )
            self.registry.add_peer(peer)
            added.append(url)
        return added
