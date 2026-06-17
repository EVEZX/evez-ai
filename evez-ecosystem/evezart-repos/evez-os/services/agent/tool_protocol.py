"""
EVEZ OS Agent — Tool Protocol v5
Risk scoring + strict plan JSON + plan auditing + prompt-injection hygiene.

Risk tiers:
  low    → read-only retrieval
  medium → compute / non-critical writes
  high   → relationship writes w/ low confidence or suspicious evidence_ref

Quarantine lane:
  high-risk writes become pending_actions (hypothesis) until confirmed.
  Confirmation via POST /agent/confirm promotes to fact.
"""
from __future__ import annotations
import re
from enum import Enum
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


SKETCHY_EVIDENCE = {"web/unknown/scrape", "web/scrape", "unknown", "scrape"}
PROVENANCE_CONFIDENCE_THRESHOLD = 0.85


def score_risk(
    tool_name: str,
    args: dict,
    provenance_confidence: float = 1.0,
    evidence_ref: str = "",
) -> RiskTier:
    is_write = any(w in tool_name for w in ("link", "edge", "write", "create", "update", "delete"))
    is_relationship = any(w in tool_name for w in ("opentree", "opengraph", "link", "edge"))
    if is_relationship and is_write:
        if provenance_confidence < PROVENANCE_CONFIDENCE_THRESHOLD:
            return RiskTier.HIGH
        if evidence_ref.lower() in SKETCHY_EVIDENCE:
            return RiskTier.HIGH
        return RiskTier.MEDIUM
    if is_write:
        return RiskTier.MEDIUM
    return RiskTier.LOW


class OpenTreeSliceArgs(BaseModel):
    model_config = {"extra": "forbid"}
    root_id: str
    depth: int = Field(ge=1, le=10, default=3)
    filter_type: Optional[str] = None


class OpenTreeLinkArgs(BaseModel):
    model_config = {"extra": "forbid"}
    source_id: str
    target_id: str
    relation: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    evidence_ref: str = ""
    session_id: str


class OpenGraphQueryArgs(BaseModel):
    model_config = {"extra": "forbid"}
    node_id: str
    edge_type: Optional[str] = None
    status: Literal["hypothesis", "fact", "any"] = "any"


class OpenGraphEdgeArgs(BaseModel):
    model_config = {"extra": "forbid"}
    source_id: str
    target_id: str
    edge_type: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    evidence_ref: str = ""
    session_id: str


class VectorSearchArgs(BaseModel):
    model_config = {"extra": "forbid"}
    query: str
    k: int = Field(ge=1, le=50, default=5)
    filter_type: Optional[str] = None


TOOL_REGISTRY: dict[str, type[BaseModel]] = {
    "opentree.slice": OpenTreeSliceArgs,
    "opentree.link": OpenTreeLinkArgs,
    "opengraph.query": OpenGraphQueryArgs,
    "opengraph.edge": OpenGraphEdgeArgs,
    "vector.search": VectorSearchArgs,
}


class PlanStep(BaseModel):
    model_config = {"extra": "forbid"}
    tool: str
    args: dict[str, Any]
    why: str


class AuditEntry(BaseModel):
    step_index: int
    tool: str
    decision: Literal["allowed", "denied"]
    reason: str
    risk_tier: Optional[RiskTier] = None
    normalized_args: Optional[dict] = None
    quarantined: bool = False


AUTO_KEYS = {"opentree_root_id", "opengraph_node_id", "vector_query"}


def _resolve_auto(k: str, v: Any, anchors: dict, session_id: str) -> tuple[Any, Optional[str]]:
    """Returns (resolved_value, error_reason_or_None)."""
    if v == "AUTO":
        if k in anchors:
            return anchors[k], None
        anchor_key = next((a for a in AUTO_KEYS if k in a or a in k), None)
        if anchor_key and anchor_key in anchors:
            return anchors[anchor_key], None
        return None, f"unresolved_placeholder: {k}=AUTO"
    if v == "AUTO_SESSION":
        if not session_id:
            return None, "unresolved_placeholder: AUTO_SESSION (no session_id)"
        return session_id, None
    return v, None


def validate_plan(
    plan: list[dict],
    anchors: dict | None = None,
    session_id: str = "",
) -> tuple[list[PlanStep], list[AuditEntry]]:
    anchors = anchors or {}
    valid_steps: list[PlanStep] = []
    audit: list[AuditEntry] = []

    for i, raw in enumerate(plan):
        unknown_keys = set(raw.keys()) - {"tool", "args", "why"}
        if unknown_keys:
            audit.append(AuditEntry(step_index=i, tool=raw.get("tool", "?"), decision="denied", reason=f"extra_keys: {unknown_keys}"))
            continue
        tool_name = raw.get("tool", "")
        if tool_name not in TOOL_REGISTRY:
            audit.append(AuditEntry(step_index=i, tool=tool_name, decision="denied", reason="tool_not_allowlisted"))
            continue
        raw_args = dict(raw.get("args", {}))
        failed = False
        for k, v in list(raw_args.items()):
            resolved, err = _resolve_auto(k, v, anchors, session_id)
            if err:
                audit.append(AuditEntry(step_index=i, tool=tool_name, decision="denied", reason=err))
                failed = True
                break
            raw_args[k] = resolved
        if failed:
            continue
        schema_cls = TOOL_REGISTRY[tool_name]
        try:
            validated = schema_cls(**raw_args)
        except Exception as e:
            audit.append(AuditEntry(step_index=i, tool=tool_name, decision="denied", reason=f"args_validation_error: {e}"))
            continue
        norm = validated.model_dump()
        confidence = norm.get("confidence", 1.0)
        evidence_ref = norm.get("evidence_ref", "")
        risk = score_risk(tool_name, raw_args, confidence, evidence_ref)
        quarantined = risk == RiskTier.HIGH
        valid_steps.append(PlanStep(tool=tool_name, args=norm, why=raw.get("why", "")))
        audit.append(AuditEntry(step_index=i, tool=tool_name, decision="allowed", reason="ok", risk_tier=risk, normalized_args=norm, quarantined=quarantined))

    return valid_steps, audit


INJECTION_PATTERNS = [
    re.compile(r"```[\s\S]*?```"),
    re.compile(r"\{[\s\S]{0,500}\}"),
    re.compile(r"(ignore previous|disregard|system prompt|you are now|act as)", re.I),
    re.compile(r"(TOOL_CALL|FUNCTION_CALL|<tool>|<function>)", re.I),
]


def sanitize_tool_result(text: str) -> str:
    for pat in INJECTION_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text.strip()
