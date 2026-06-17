"""evezos.object_store — deterministic typed-node object projection."""
import hashlib, json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    type: str
    id: str
    attrs: dict = field(default_factory=dict)

    def serialize(self) -> dict:
        return {"type": self.type, "id": self.id, "attrs": self.attrs}

    def sha256(self) -> str:
        canon = json.dumps(self.serialize(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canon.encode()).hexdigest()


class ObjectStore:
    def __init__(self):
        self._nodes: dict[str, Node] = {}

    def upsert(self, node: Node):
        self._nodes[node.id] = node

    def get(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def project(self) -> list[dict]:
        return sorted([n.serialize() for n in self._nodes.values()], key=lambda x: x["id"])

    def store_sha(self) -> str:
        canon = json.dumps(self.project(), separators=(",", ":"))
        return hashlib.sha256(canon.encode()).hexdigest()
