"""
EVEZ OS — OpenGraph edge store with hypothesis/fact quarantine lane.
"""
from __future__ import annotations
import time
import uuid
from typing import Literal, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class OpenGraphEdge:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    edge_type: str = ""
    confidence: float = 1.0
    evidence_ref: str = ""
    session_id: str = ""
    status: Literal["hypothesis", "fact"] = "hypothesis"
    created_at: float = field(default_factory=time.time)
    promoted_at: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


_edges: dict[str, OpenGraphEdge] = {}


def write_edge(source_id: str, target_id: str, edge_type: str,
               confidence: float = 1.0, evidence_ref: str = "",
               session_id: str = "", status: Literal["hypothesis", "fact"] = "hypothesis") -> OpenGraphEdge:
    edge = OpenGraphEdge(source_id=source_id, target_id=target_id, edge_type=edge_type,
                         confidence=confidence, evidence_ref=evidence_ref,
                         session_id=session_id, status=status)
    _edges[edge.id] = edge
    return edge


def query_edges(status: Literal["hypothesis", "fact", "any"] = "any",
                session_id: Optional[str] = None) -> list[OpenGraphEdge]:
    results = list(_edges.values())
    if status != "any":
        results = [e for e in results if e.status == status]
    if session_id:
        results = [e for e in results if e.session_id == session_id]
    return results


def promote_edge(edge_id: str) -> Optional[OpenGraphEdge]:
    edge = _edges.get(edge_id)
    if not edge:
        return None
    edge.status = "fact"
    edge.promoted_at = time.time()
    return edge
