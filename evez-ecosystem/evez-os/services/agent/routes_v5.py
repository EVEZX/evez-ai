"""
EVEZ OS Agent v5 — FastAPI routes
Endpoints: pending actions, OpenGraph browse/promote, plan audit.
"""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .tool_protocol import validate_plan, RiskTier
from .pending_actions import create_pending, get_pending, confirm_action, reject_action
from .opengraph import write_edge, query_edges, promote_edge

router = APIRouter()


@router.get("/agent/pending")
def list_pending(session_id: str, status: str = Query(default="pending")):
    actions = get_pending(session_id=session_id, status=status)
    return {"pending": [a.to_dict() for a in actions]}


class ConfirmRequest(BaseModel):
    action_id: str
    session_id: str


@router.post("/agent/confirm")
def confirm(req: ConfirmRequest):
    def _executor(tool: str, args: dict) -> dict:
        return {"status": "executed", "tool": tool, "args": args}
    action = confirm_action(req.action_id, _executor)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found or already processed")
    return {"status": action.status, "action": action.to_dict()}


@router.post("/agent/reject")
def reject(req: BaseModel):
    from .pending_actions import reject_action as _reject
    action = _reject(req.action_id)  # type: ignore
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return {"status": action.status}


@router.get("/edges")
def list_edges(status: str = Query(default="any"), session_id: Optional[str] = None):
    edges = query_edges(status=status, session_id=session_id)
    return {"edges": [e.to_dict() for e in edges], "count": len(edges)}


class EdgeWriteRequest(BaseModel):
    source_id: str
    target_id: str
    edge_type: str
    confidence: float = 1.0
    evidence_ref: str = ""
    session_id: str = ""


@router.post("/edges")
def create_edge(req: EdgeWriteRequest):
    edge = write_edge(
        source_id=req.source_id, target_id=req.target_id, edge_type=req.edge_type,
        confidence=req.confidence, evidence_ref=req.evidence_ref, session_id=req.session_id,
        status="fact" if req.confidence >= 0.85 else "hypothesis"
    )
    return {"edge": edge.to_dict()}


@router.post("/edges/{edge_id}/promote")
def promote(edge_id: str):
    edge = promote_edge(edge_id)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    return {"edge": edge.to_dict()}


class PlanValidateRequest(BaseModel):
    plan: list[dict]
    session_id: str = ""
    anchors: dict = {}


@router.post("/plan/validate")
def validate_plan_endpoint(req: PlanValidateRequest):
    valid_steps, audit = validate_plan(req.plan, anchors=req.anchors, session_id=req.session_id)
    return {
        "valid_step_count": len(valid_steps),
        "total_steps": len(req.plan),
        "audit": [a.model_dump() for a in audit],
        "has_quarantined": any(a.quarantined for a in audit),
        "quarantined_steps": [a.model_dump() for a in audit if a.quarantined],
    }
