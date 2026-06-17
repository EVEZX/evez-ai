"""
EVEZ Agent Trust API — FICO for AI Agents
FastAPI service that scores AI agents using spectral trust analysis.
Connects to the EVEZ Docker stack (OpenTree, OpenGraph, VectorStore, Spine).
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import sys, os, json, time

sys.path.insert(0, os.path.dirname(__file__))
from agent_trust_engine import (
    SpectralTrustEngine, AgentProfile, AgentAction, ActionType, RiskTier
)

app = FastAPI(
    title="EVEZ Agent Trust API",
    description="Spectral credit scoring for AI agents. FICO for AI. The eigenspectrum sees what metrics can't.",
    version="1.0.0",
)

engine = SpectralTrustEngine()

# ── Request/Response Models ──────────────────────────────────────────────

class ActionInput(BaseModel):
    action_type: str
    timestamp: Optional[float] = None
    task_id: Optional[str] = None
    tool_name: Optional[str] = None
    duration_ms: Optional[int] = None
    success: Optional[bool] = None
    error_type: Optional[str] = None
    provenance_hash: Optional[str] = None
    metadata: Optional[Dict] = None

class ScoreRequest(BaseModel):
    agent_id: str
    name: Optional[str] = None
    version: Optional[str] = None
    capabilities: Optional[List[str]] = None
    actions: List[ActionInput]

class BatchScoreRequest(BaseModel):
    agents: List[ScoreRequest]

# ── Endpoints ────────────────────────────────────────────────────────────

@app.post("/v1/score")
def score_agent(req: ScoreRequest):
    """Score a single AI agent. Returns spectral trust score with risk breakdown."""
    try:
        profile = AgentProfile(
            agent_id=req.agent_id,
            name=req.name,
            version=req.version,
            capabilities=req.capabilities or [],
        )
        for a in req.actions:
            profile.actions.append(AgentAction(
                action_type=ActionType(a.action_type),
                timestamp=a.timestamp or time.time(),
                task_id=a.task_id,
                tool_name=a.tool_name,
                duration_ms=a.duration_ms,
                success=a.success,
                error_type=a.error_type,
                provenance_hash=a.provenance_hash,
                metadata=a.metadata or {},
            ))
        result = engine.score_agent(profile)
        if result.get("score") is None:
            raise HTTPException(400, result.get("error", "Insufficient data"))
        return result
    except ValueError as e:
        raise HTTPException(400, f"Invalid action_type: {e}")

@app.post("/v1/score/batch")
def score_batch(req: BatchScoreRequest):
    """Score multiple agents at once."""
    results = []
    for agent_req in req.agents:
        try:
            r = score_agent(agent_req)
            results.append(r)
        except HTTPException as e:
            results.append({"agent_id": agent_req.agent_id, "error": e.detail})
    return {"results": results, "count": len(results)}

@app.get("/v1/score/{agent_id}")
def get_score(agent_id: str):
    """Retrieve a previously computed score."""
    result = engine.get_score(agent_id)
    if not result:
        raise HTTPException(404, "Agent not scored yet")
    return result

@app.get("/v1/leaderboard")
def get_leaderboard(top_n: int = 20):
    """Top agents by trust score."""
    return {"leaderboard": engine.get_leaderboard(top_n)}

@app.get("/v1/tiers")
def get_tiers():
    """Risk tier definitions."""
    return {
        "tiers": [
            {"tier": "PLATINUM", "min_score": 800, "description": "Ultra-reliable, provenance-verified agents"},
            {"tier": "GOLD", "min_score": 700, "description": "High-reliability agents with proven track records"},
            {"tier": "SILVER", "min_score": 600, "description": "Reliable agents with some risk factors"},
            {"tier": "BRONZE", "min_score": 500, "description": "Functional agents with notable risks"},
            {"tier": "HIGH_RISK", "min_score": 400, "description": "Agents with significant reliability concerns"},
            {"tier": "UNTRUSTED", "min_score": 300, "description": "Agents that should not be trusted for critical tasks"},
        ]
    }

@app.get("/v1/factors")
def get_factors():
    """Trust factor definitions and weights."""
    return {
        "factors": {
            k: {"weight": v["weight"], "label": v["label"], "description": v["desc"]}
            for k, v in SpectralTrustEngine.TRUST_FACTORS.items()
        }
    }

@app.get("/health")
def health():
    return {"status": "ok", "engine": "spectral_trust", "version": "1.0.0", "scored_agents": len(engine.scored_agents)}
