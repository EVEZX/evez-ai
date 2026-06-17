from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field


class AgentAnnouncement(BaseModel):
    node_id: str
    url: str
    last_seen_ts: float | None = None
    capabilities: list[str] = Field(default_factory=list)
    chain_tip: str
    region: str


@dataclass
class PeerRegistry:
    peers: dict[str, dict[str, Any]] = field(default_factory=dict)

    def announce(self, payload: AgentAnnouncement) -> dict[str, Any]:
        now = payload.last_seen_ts or time.time()
        self.peers[payload.node_id] = {
            "node_id": payload.node_id,
            "url": payload.url,
            "last_seen_ts": now,
            "capabilities": payload.capabilities,
            "chain_tip": payload.chain_tip,
            "region": payload.region,
        }
        return self.peers[payload.node_id]

    def all_peers(self) -> list[dict[str, Any]]:
        return list(self.peers.values())


registry = PeerRegistry()
app = FastAPI(title="EvezBrain Discovery Server")


@app.post("/api/agents/announce")
def announce(payload: AgentAnnouncement) -> dict[str, Any]:
    return {"ok": True, "peer": registry.announce(payload)}


@app.get("/api/agents/peers")
def peers() -> dict[str, Any]:
    return {"peers": registry.all_peers()}


async def announce_periodically(
    my_announce_url: str,
    discovery_targets: list[str],
    payload_factory,
    interval_s: int = 300,
) -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            payload = payload_factory()
            for target in discovery_targets:
                try:
                    await client.post(f"{target.rstrip('/')}/api/agents/announce", json=payload)
                except Exception:
                    continue
            await asyncio.sleep(interval_s)
