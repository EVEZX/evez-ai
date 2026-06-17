from __future__ import annotations

import asyncio
import json
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import websockets

from agents.comms.agentspeak import AgentSpeakMessage, MessageType, decode_message, encode_message


@dataclass
class PeerState:
    node_id: str
    url: str
    synaptic_strength: float


@dataclass
class LinkManager:
    max_peers: int = 12
    dream_queue: deque[dict[str, Any]] = field(default_factory=deque)

    async def connect_top_peers(self, peers: list[PeerState]) -> None:
        ranked = sorted(peers, key=lambda p: p.synaptic_strength, reverse=True)[: self.max_peers]
        await asyncio.gather(*(self._connection_loop(peer) for peer in ranked))

    async def _connection_loop(self, peer: PeerState) -> None:
        try:
            async with websockets.connect(peer.url) as ws:
                async for raw in ws:
                    if isinstance(raw, str):
                        raw = raw.encode("utf-8")
                    message = decode_message(raw)
                    await self.handle_message(message, ws)
        except Exception:
            return

    async def handle_message(self, message: AgentSpeakMessage, websocket) -> None:
        if message.msg_type == MessageType.EVOLUTION_BROADCAST:
            if await self._sandbox_test(message.payload):
                await self._self_apply(message.payload)
                ack = AgentSpeakMessage(
                    msg_type=MessageType.HEARTBEAT,
                    sender_node_id="self",
                    recipient_node_id=message.sender_node_id,
                    timestamp_ns=message.timestamp_ns,
                    payload={"event": "evolution_adopted"},
                )
                await websocket.send(encode_message(ack))
        elif message.msg_type == MessageType.DREAM_SHARE:
            self.dream_queue.append(message.payload)

    async def _sandbox_test(self, payload: dict[str, Any]) -> bool:
        return bool(payload.get("diff"))

    async def _self_apply(self, payload: dict[str, Any]) -> None:
        await asyncio.sleep(0)


def peer_state_from_registry(registry: list[dict[str, Any]]) -> list[PeerState]:
    peers = []
    for peer in registry:
        strength = float(peer.get("lban", {}).get("synaptic_strength", 0.0))
        peers.append(PeerState(node_id=peer["node_id"], url=peer["url"], synaptic_strength=strength))
    return peers
