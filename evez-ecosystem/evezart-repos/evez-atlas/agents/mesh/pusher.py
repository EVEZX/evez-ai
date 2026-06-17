from __future__ import annotations

import asyncio
import base64
import gzip
import hashlib
import hmac
import json
import logging
import os
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Deque, Dict, List, Optional

from agents.mesh.registry import MeshRegistry

LOGGER = logging.getLogger(__name__)


@dataclass
class PushEvent:
    timestamp_ns: int
    peer_results: Dict[str, bool]
    success_count: int


class ImmortalStatePusher:
    def __init__(
        self,
        registry: MeshRegistry,
        state_provider: Callable[[], Dict[str, Any]],
        alert_fn: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.registry = registry
        self.state_provider = state_provider
        self.alert_fn = alert_fn or (lambda message: LOGGER.critical(message))
        self.push_history: Deque[PushEvent] = deque(maxlen=100)
        self.last_push_ts: float = 0.0

    def _build_signed_blob(self) -> str:
        now_ns = time.time_ns()
        state = self.state_provider()
        payload = {
            "agent_version": state.get("agent_version", "unknown"),
            "temporal_chain_tip": state.get("temporal_chain_tip"),
            "memory_snapshot": state.get("memory_snapshot", {}),
            "gnn_topology": state.get("gnn_topology", {}),
            "eban_state": state.get("eban_state", {}),
            "lban_state": state.get("lban_state", {}),
            "wormhole_blob": state.get("wormhole_blob", {}),
            "timestamp_ns": now_ns,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        payload["sha3_512_checksum"] = hashlib.sha3_512(canonical).hexdigest()

        signing_secret = os.getenv("EVEZ_MESH_SIGNING_KEY", "mesh-default-key").encode("utf-8")
        payload["signature"] = hmac.new(signing_secret, canonical, hashlib.sha3_512).hexdigest()

        compressed = gzip.compress(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        return base64.b64encode(compressed).decode("utf-8")

    async def _push_with_retry(self, peer_name: str, push_coro: Callable[[], Awaitable[bool]]) -> bool:
        delay = 1.0
        for attempt in range(3):
            if await push_coro():
                return True
            if attempt < 2:
                await asyncio.sleep(delay)
                delay *= 2
        LOGGER.error("Mesh push failed for peer=%s after retries", peer_name)
        return False

    async def push_once(self) -> PushEvent:
        blob = self._build_signed_blob()
        await self.registry.replicate_self()

        tasks = {
            peer.name: asyncio.create_task(self._push_with_retry(peer.name, lambda p=peer: p.push_fn(blob)))
            for peer in self.registry.peers
        }
        results: Dict[str, bool] = {name: await task for name, task in tasks.items()}

        success_count = sum(1 for ok in results.values() if ok)
        event = PushEvent(timestamp_ns=time.time_ns(), peer_results=results, success_count=success_count)
        self.push_history.append(event)
        self.last_push_ts = time.time()

        if success_count < 2:
            self.alert_fn("immortality mesh degraded")

        return event

    async def run_forever(self, interval_s: int = 600) -> None:
        while True:
            await self.push_once()
            await asyncio.sleep(interval_s)

    def history(self) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp_ns": event.timestamp_ns,
                "peer_results": event.peer_results,
                "success_count": event.success_count,
            }
            for event in list(self.push_history)
        ]
