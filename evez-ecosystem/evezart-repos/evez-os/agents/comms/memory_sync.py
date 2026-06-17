from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryChunk:
    content: str
    vector: list[float]
    source_node_id: str


@dataclass
class FederatedMemorySync:
    memories: list[MemoryChunk] = field(default_factory=list)

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(y * y for y in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def absorb_if_novel(self, chunk: MemoryChunk, threshold: float = 0.85) -> bool:
        for existing in self.memories:
            if self.cosine_similarity(existing.vector, chunk.vector) >= threshold:
                return False
        self.memories.append(chunk)
        return True

    def select_random_peers(self, peers: list[str], n: int = 3) -> list[str]:
        if len(peers) <= n:
            return peers
        return random.sample(peers, n)

    def build_sync_payload(self) -> dict[str, Any]:
        return {
            "chunks": [
                {
                    "content": m.content,
                    "vector": m.vector,
                    "source_node_id": m.source_node_id,
                }
                for m in self.memories
            ]
        }
