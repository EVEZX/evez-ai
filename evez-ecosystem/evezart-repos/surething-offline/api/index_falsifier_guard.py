#!/usr/bin/env python3
"""
EVEZ Operator API — falsifier-guarded drop-in candidate for the live ingress path.

Purpose:
- preserve the current route surface from api/index.py
- add a Constitutional Rule #2 guard for event-like payloads
- make the active ingress fix reviewable without pretending the durable cutover is already live

Suggested local run:
    uvicorn api.index_falsifier_guard:app --port 7777
"""

from __future__ import annotations
import hashlib, json, unicodedata, math
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="EVEZ Operator API",
    description="EVEZ behavioral OS — callable by any AI via MCP or HTTP",
    version="1.0.1",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_spine: list[dict] = []


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _normalize(obj: Any, float_paths: set[str], path: str = "") -> Any:
    if isinstance(obj, str):
        return nfc(obj)
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise ValueError(f"Poison float at {path}")
        if path in float_paths:
            v = round(obj, 6)
            return 0.0 if v == 0.0 else v
        raise TypeError(f"Float at non-declared path {path}")
    if isinstance(obj, int):
        return obj
    if isinstance(obj, dict):
        return {nfc(k): _normalize(v, float_paths, f"{path}.{k}") for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_normalize(v, float_paths, f"{path}[{i}]") for i, v in enumerate(obj)]
    if obj is None:
        return None
    raise TypeError(f"Unsupported type at {path}: {type(obj)}")


def canonicalize(obj: dict, float_paths: list[str] | None = None) -> tuple[str, str]:
    fp = set(float_paths or [])
    normalized = _normalize(obj, fp)
    jcs = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(jcs.encode("utf-8")).hexdigest()
    return jcs, digest


def _make_event(event_type: str, lane: str, payload: dict, parent_hash: str | None) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    base = {
        "event_type": event_type,
        "lane": lane,
        "payload": payload,
        "timestamp": ts,
        "height": len(_spine),
        "parent_event_hash": parent_hash or "",
    }
    evidence_obj = {k: v for k, v in base.items() if k != "parent_event_hash"}
    _, evidence_hash = canonicalize(evidence_obj)
    base["evidence_hash"] = evidence_hash
    _, event_hash = canonicalize(base)
    base["event_hash"] = event_hash
    return base


def _enforce_falsifier_guard(payload: dict) -> None:
    kind = str(payload.get("kind", "") or "")
    falsifier = payload.get("falsifier")
    if kind.endswith(".event") and not falsifier:
        raise HTTPException(
            400,
            f"Constitutional Rule #2 violation: event payload missing falsifier field. kind={kind}",
        )


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "evez-operator-api",
        "version": "1.0.1",
        "spine_height": len(_spine),
        "docs": "/docs",
        "tools": "/tools",
        "falsifier_guard": "active",
    }


@app.get("/tools")
def list_tools():
    return {
        "schema_version": "1.0",
        "name": "evez-operator",
        "description": "EVEZ behavioral operating system tools",
        "tools": [
            {
                "name": "spine_event",
                "description": "Add typed event to EVEZ spine",
                "inputSchema": {
                    "type": "object",
                    "required": ["event_type", "lane", "payload"],
                    "properties": {
                        "event_type": {"type": "string", "enum": ["observation", "transformation", "claim", "test", "decision", "linkage"]},
                        "lane": {"type": "string", "enum": ["empirical", "documentary", "metaphysical"]},
                        "payload": {"type": "object"},
                        "parent_event_hash": {"type": "string"},
                    },
                },
            },
            {
                "name": "spine_verify",
                "description": "Verify SHA-256 chain integrity",
                "inputSchema": {"type": "object", "properties": {"from_height": {"type": "integer", "default": 0}}},
            },
            {
                "name": "contradiction_check",
                "description": "List active unsat cores",
                "inputSchema": {"type": "object", "properties": {"scope": {"type": "string", "default": "all"}}},
            },
            {
                "name": "fire_anchor_payload",
                "description": "Build Base Sepolia calldata for FIRE event",
                "inputSchema": {
                    "type": "object",
                    "required": ["fire_number", "evidence_hash"],
                    "properties": {
                        "fire_number": {"type": "integer"},
                        "evidence_hash": {"type": "string"},
                        "round": {"type": "integer"},
                        "v_score": {"type": "number"},
                    },
                },
            },
            {
                "name": "canonicalize",
                "description": "Normalize + JCS + SHA-256 any JSON object",
                "inputSchema": {
                    "type": "object",
                    "required": ["input"],
                    "properties": {
                        "input": {"type": "object"},
                        "float_paths": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            {"name": "deploy_status", "description": "All EVEZ service health", "inputSchema": {"type": "object", "properties": {}}},
        ],
    }


class SpineEventRequest(BaseModel):
    event_type: str
    lane: str
    payload: dict
    parent_event_hash: Optional[str] = None


@app.post("/spine/event")
def add_spine_event(req: SpineEventRequest):
    VALID_TYPES = {"observation", "transformation", "claim", "test", "decision", "linkage"}
    VALID_LANES = {"empirical", "documentary", "metaphysical"}
    if req.event_type not in VALID_TYPES:
        raise HTTPException(400, f"Invalid event_type: {req.event_type}")
    if req.lane not in VALID_LANES:
        raise HTTPException(400, f"Invalid lane: {req.lane}")

    _enforce_falsifier_guard(req.payload)

    parent = req.parent_event_hash or (_spine[-1]["event_hash"] if _spine else None)
    event = _make_event(req.event_type, req.lane, req.payload, parent)
    _spine.append(event)
    return {"ok": True, "event_hash": event["event_hash"], "evidence_hash": event["evidence_hash"], "height": event["height"]}


@app.get("/spine/verify")
def verify_spine(from_height: int = 0):
    for i in range(from_height + 1, len(_spine)):
        expected = _spine[i - 1]["event_hash"]
        actual = _spine[i].get("parent_event_hash", "")
        if expected != actual:
            return {"valid": False, "broken_at": i, "expected": expected, "got": actual}
    return {"valid": True, "checked": len(_spine) - from_height, "tip": _spine[-1]["event_hash"] if _spine else None}


@app.get("/spine/events")
def get_spine(limit: int = 20, offset: int = 0):
    return {"events": _spine[offset : offset + limit], "total": len(_spine)}


class CanonicalizeRequest(BaseModel):
    input: dict
    float_paths: list[str] = []


@app.post("/canonicalize")
def canonicalize_endpoint(req: CanonicalizeRequest):
    try:
        jcs, digest = canonicalize(req.input, req.float_paths)
        return {"jcs": jcs, "sha256": digest, "bytes": len(jcs)}
    except (ValueError, TypeError) as e:
        raise HTTPException(400, str(e))


@app.get("/contradictions")
def get_contradictions(scope: str = "all"):
    cores = [
        {"id": "unsat-001", "scope": "revenue", "priority": "HIGH", "description": "Railway evez-os undeployed — Stripe webhooks dead", "resolution": "railway up in evez-os repo", "test": "HTTP GET https://evez-os.railway.app/health → 200"},
        {"id": "unsat-002", "scope": "fire", "priority": "MEDIUM", "description": "FIRE#125 unanchored — no funded wallet configured", "resolution": "Set WALLET_PRIVATE_KEY + ALCHEMY_API_KEY", "test": "eth_getBalance on wallet > 0.001 ETH"},
        {"id": "unsat-003", "scope": "contacts", "priority": "LOW", "description": "daniel@goodfire.ai hard-bounced, no valid Goodfire contact", "resolution": "Find contact via goodfire.ai/team or LinkedIn", "test": "SMTP RCPT TO → 250 OK"},
    ]
    if scope != "all":
        cores = [c for c in cores if c["scope"] == scope]
    return {"unsat_cores": cores, "count": len(cores)}


@app.post("/fire/anchor")
def fire_anchor(fire_number: int, evidence_hash: str, round: int = 0, v_score: float = 0.0):
    payload = {
        "evidence_hash": evidence_hash,
        "fire_number": fire_number,
        "round": round,
        "system": "EVEZ_OS",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "v_score": v_score,
    }
    jcs, digest = canonicalize(payload, float_paths=[".v_score"])
    calldata = "0x" + jcs.encode("utf-8").hex()
    return {"fire_number": fire_number, "anchor_hash": digest, "calldata": calldata, "calldata_length_bytes": len(jcs), "network": "base-sepolia"}


@app.get("/deploy/status")
def deploy_status():
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "services": {
            "railway_evez_os": {"status": "UNDEPLOYED", "action": "railway up", "priority": "CRITICAL"},
            "vercel_mcp_server": {"status": "THIS_SERVER", "url": "https://evez-operator.vercel.app"},
            "alchemy_base_sepolia": {"status": "READ_ONLY", "action": "needs WALLET_PRIVATE_KEY"},
            "backendless_spine": {"status": "UNCONFIGURED"},
            "local_openclaw": {"status": "LOCAL", "port": 18789},
        },
    }
