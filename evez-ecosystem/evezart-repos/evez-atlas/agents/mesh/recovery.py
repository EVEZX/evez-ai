from __future__ import annotations

import asyncio
import base64
import gzip
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional

from agents.mesh.registry import MeshRegistry

LOGGER = logging.getLogger(__name__)

PRECEDENCE = {
    "ipfs_web3_storage": 0,
    "github_gist": 1,
    "archive_org": 2,
    "pastebin": 3,
}


class MeshRecoveryDaemon:
    def __init__(self, registry: MeshRegistry, event_bus: Any, restore_fn: Any) -> None:
        self.registry = registry
        self.event_bus = event_bus
        self.restore_fn = restore_fn
        self.local_only_mode = False

    @staticmethod
    def _decode_and_validate(blob: str) -> Optional[Dict[str, Any]]:
        try:
            raw = gzip.decompress(base64.b64decode(blob.encode("utf-8")))
            payload = json.loads(raw)
            checksum = payload.pop("sha3_512_checksum")
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            expected = hashlib.sha3_512(canonical).hexdigest()
            if checksum != expected:
                return None
            payload["sha3_512_checksum"] = checksum
            return payload
        except Exception:
            return None

    async def recover_once(self) -> Optional[Dict[str, Any]]:
        candidates = []
        for peer in self.registry.peers:
            blob = await peer.pull_fn()
            if not blob:
                continue
            payload = self._decode_and_validate(blob)
            if not payload:
                continue
            candidates.append((peer.name, payload))

        if not candidates:
            self.local_only_mode = True
            return None

        self.local_only_mode = False
        candidates.sort(
            key=lambda item: (
                item[1].get("timestamp_ns", 0),
                -PRECEDENCE.get(item[0], 999),
            ),
            reverse=True,
        )
        source_peer, recovered = candidates[0]
        self.restore_fn(recovered)
        divergence = max(0, time.time() - (recovered.get("timestamp_ns", 0) / 1_000_000_000))
        self.event_bus.emit(
            "mesh_recovered",
            {
                "source_peer": source_peer,
                "recovered_version": recovered.get("agent_version", "unknown"),
                "divergence_seconds": divergence,
            },
        )
        return recovered

    async def recover_on_startup(self) -> None:
        recovered = await self.recover_once()
        if recovered is not None:
            return

        LOGGER.warning("No peers reachable, entering LOCAL_ONLY mode")
        while self.local_only_mode:
            await asyncio.sleep(60)
            recovered = await self.recover_once()
            if recovered is not None:
                break
