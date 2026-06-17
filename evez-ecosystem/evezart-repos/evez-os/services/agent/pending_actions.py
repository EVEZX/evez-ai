"""
EVEZ OS — Pending Actions (Quarantine Lane)
High-risk writes quarantined here as hypotheses pending explicit confirmation.
"""
from __future__ import annotations
import time
import uuid
from typing import Any, Callable, Literal, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class PendingAction:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    tool: str = ""
    args: dict = field(default_factory=dict)
    why: str = ""
    risk_tier: str = "high"
    status: Literal["pending", "confirmed", "rejected"] = "pending"
    created_at: float = field(default_factory=time.time)
    confirmed_at: Optional[float] = None
    result: Optional[dict] = None

    def to_dict(self) -> dict:
        return asdict(self)


_store: dict[str, PendingAction] = {}


def create_pending(session_id: str, tool: str, args: dict, why: str = "", risk_tier: str = "high") -> PendingAction:
    action = PendingAction(session_id=session_id, tool=tool, args=args, why=why, risk_tier=risk_tier)
    _store[action.id] = action
    return action


def get_pending(session_id: str, status: str = "pending") -> list[PendingAction]:
    return [a for a in _store.values() if a.session_id == session_id and (status == "any" or a.status == status)]


def confirm_action(action_id: str, executor: Callable[[str, dict], dict]) -> Optional[PendingAction]:
    action = _store.get(action_id)
    if not action or action.status != "pending":
        return None
    try:
        result = executor(action.tool, action.args)
        action.status = "confirmed"
        action.confirmed_at = time.time()
        action.result = result
    except Exception as e:
        action.status = "rejected"
        action.result = {"error": str(e)}
    return action


def reject_action(action_id: str) -> Optional[PendingAction]:
    action = _store.get(action_id)
    if not action or action.status != "pending":
        return None
    action.status = "rejected"
    return action


"""
Postgres DDL:
CREATE TABLE IF NOT EXISTS pending_actions (
    id UUID PRIMARY KEY, session_id TEXT NOT NULL, tool TEXT NOT NULL,
    args JSONB NOT NULL, why TEXT, risk_tier TEXT DEFAULT 'high',
    status TEXT DEFAULT 'pending', created_at DOUBLE PRECISION,
    confirmed_at DOUBLE PRECISION, result JSONB
);
CREATE INDEX IF NOT EXISTS idx_pa_session ON pending_actions(session_id, status);
"""
