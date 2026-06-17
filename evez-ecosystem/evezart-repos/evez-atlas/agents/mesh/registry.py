from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from time import time
from typing import Any, Awaitable, Callable, Dict, List, Optional
from urllib import request


PushFn = Callable[[str], Awaitable[bool]]
PullFn = Callable[[], Awaitable[Optional[str]]]


async def _http_post(endpoint: str, payload: str) -> bool:
    def _send() -> bool:
        req = request.Request(
            endpoint,
            data=payload.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300

    try:
        return await asyncio.to_thread(_send)
    except Exception:
        return False


async def _http_get(endpoint: str) -> Optional[str]:
    def _fetch() -> Optional[str]:
        req = request.Request(endpoint, method="GET")
        with request.urlopen(req, timeout=10) as resp:
            if not (200 <= resp.status < 300):
                return None
            return resp.read().decode("utf-8")

    try:
        return await asyncio.to_thread(_fetch)
    except Exception:
        return None


@dataclass
class MeshPeer:
    name: str
    endpoint: str
    push_fn: PushFn
    pull_fn: PullFn
    priority: int
    last_sync_ts: float = 0.0
    sync_interval_s: int = 600

    def to_bootstrap_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "priority": self.priority,
            "last_sync_ts": self.last_sync_ts,
            "sync_interval_s": self.sync_interval_s,
        }


@dataclass
class MeshRegistry:
    peers: List[MeshPeer] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.peers:
            self.peers = self.default_peers()

    @staticmethod
    def default_peers() -> List[MeshPeer]:
        providers = [
            ("github_gist", "https://api.github.com/gists", 2),
            ("pastebin", "https://pastebin.com/api/api_post.php", 4),
            ("ipfs_web3_storage", "https://up.web3.storage", 1),
            ("archive_org", "https://s3.us.archive.org", 3),
        ]

        peers: List[MeshPeer] = []
        for name, endpoint, priority in providers:
            peers.append(
                MeshPeer(
                    name=name,
                    endpoint=endpoint,
                    push_fn=lambda payload, ep=endpoint: _http_post(ep, payload),
                    pull_fn=lambda ep=endpoint: _http_get(ep),
                    priority=priority,
                )
            )
        return peers

    def add_peer(self, peer: MeshPeer) -> None:
        if any(existing.endpoint == peer.endpoint for existing in self.peers):
            return
        self.peers.append(peer)
        self.peers.sort(key=lambda p: p.priority)

    def serialize(self) -> str:
        payload = {
            "updated_at": time(),
            "peers": [peer.to_bootstrap_dict() for peer in self.peers],
        }
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)

    async def replicate_self(self) -> Dict[str, bool]:
        serialized = self.serialize()
        results: Dict[str, bool] = {}
        for peer in self.peers:
            ok = await peer.push_fn(serialized)
            if ok:
                peer.last_sync_ts = time()
            results[peer.name] = ok
        return results
