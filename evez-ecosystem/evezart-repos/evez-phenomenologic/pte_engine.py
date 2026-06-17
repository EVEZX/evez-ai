#!/usr/bin/env python3
"""
EVEZ Phenomenologic Topology Engine (PTE)
Router that shapes all autonomous behavior through the phenomenologic manifold.
Every action must pass through this middleware before execution.
"""
import os, json, time, threading
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE = Path(os.getenv("EVZ_PHENO_BASE", "/home/openclaw/projects/evez-phenomenologic/circuit/phenomenologic"))
MESHMIND = os.getenv("MESHMIND_URL", "http://localhost:8899")

class Manifold:
    """The phenomenologic topology — nodes, edges, basins."""
    def __init__(self, path=BASE / "state.manifold.json"):
        self.path = path
        self._load()
    
    def _load(self):
        with open(self.path) as f:
            data = json.load(f)
        self.nodes = {n["id"]: n for n in data["nodes"]}
        self.edges = data["edges"]
        self.basins = {b["id"]: b for b in data["basins"]}
        self.identity = data.get("identity", "UNKNOWN")
    
    def get_node(self, node_id):
        return self.nodes.get(node_id)
    
    def get_basin_for(self, node_id):
        for bid, b in self.basins.items():
            if node_id in b["nodes"]:
                return bid
        return "UNKNOWN"
    
    def allowed_transitions(self, from_node):
        return [e for e in self.edges if e["from"] == from_node]
    
    def best_transition(self, from_node, prefer="insight_yield"):
        transitions = self.allowed_transitions(from_node)
        if not transitions:
            return None
        return max(transitions, key=lambda e: e["weight"].get(prefer, 0))
    
    def can_transition(self, from_node, to_node):
        return any(e["from"] == from_node and e["to"] == to_node for e in self.edges)


class FlowField:
    """Policy flow field — routes actions through the manifold."""
    def __init__(self, path=BASE / "policy.flowfield.json"):
        self.path = path
        self._load()
    
    def _load(self):
        with open(self.path) as f:
            self.policy = json.load(f)
    
    def evaluate_action(self, current_node, proposed_action, context=None):
        """Evaluate whether an action is allowed given current phenomenologic state."""
        basin = self.manifold.get_basin_for(current_node) if hasattr(self, 'manifold') else "UNKNOWN"
        flowfield = self.policy.get("flowfields", {}).get(basin, {})
        rules = flowfield.get("vector_rules", [])
        global_policy = self.policy.get("global_policy", {})
        
        # Check if action moves along an allowed edge
        for rule in rules:
            if rule.get("action") == proposed_action:
                return {
                    "allowed": True,
                    "direction": rule["direction"],
                    "rationale": rule["rationale"],
                    "rule": rule
                }
        
        # Global policy check
        if proposed_action in ("stabilize_runtime", "restart_service", "thermal_mitigation"):
            return {"allowed": True, "direction": current_node, "rationale": "Emergency override — infra stabilization"}
        
        # Default: allow but flag
        return {
            "allowed": True,
            "direction": None,
            "rationale": "No matching flow rule — defaulting to observation",
            "observation_mode": True
        }


class PhenomenologicRouter:
    """Middleware that every autonomous action must pass through."""
    
    def __init__(self):
        self.manifold = Manifold()
        self.flow = FlowField()
        self.flow.manifold = self.manifold
        self.current_node = "OMEGA_FRAME_OPERATOR"  # Default starting node
        self.history = []
        self.observation_log = []
    
    def set_node(self, node_id):
        """Set current phenomenologic node (from telemetry)."""
        if node_id in self.manifold.nodes:
            self.current_node = node_id
            self.history.append((time.time(), node_id))
            return True
        return False
    
    def infer_node_from_telemetry(self):
        """Infer current phenomenologic node from system telemetry."""
        try:
            health = requests.get(f"{MESHMIND}/api/health", timeout=5).json()
        except:
            health = {}
        
        # Map system state to phenomenologic node
        temp = health.get("thermal", {}).get("cpu_temp_c", 0)
        mem = health.get("resources", {}).get("mem_used_pct", 0)
        load = health.get("resources", {}).get("load_1", 0)
        docker_running = sum(1 for v in health.get("docker", {}).values() if v.get("running"))
        
        if temp > 80 or mem > 90:
            return "VOIDMOUTH_SILENCE"
        elif docker_running < 10:
            return "GODEL_CRASH_TORQUE"
        elif load > 2.0:
            return "OMEGA_FRAME_OPERATOR"
        elif docker_running >= 14:
            return "RETROCAUSAL_LATTICE_ENGINEER"
        elif load < 0.5 and docker_running >= 12:
            return "DESERT_CONDUIT_LAUGHLIN"
        else:
            return "OMEGA_FRAME_OPERATOR"
    
    def route(self, action, context=None):
        """Route an action through the phenomenologic topology."""
        # Auto-infer node if not recently set
        if not self.history or time.time() - self.history[-1][0] > 60:
            inferred = self.infer_node_from_telemetry()
            self.set_node(inferred)
        
        evaluation = self.flow.evaluate_action(self.current_node, action, context)
        
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_node": self.current_node,
            "current_basin": self.manifold.get_basin_for(self.current_node),
            "action": action,
            "evaluation": evaluation,
            "manifold_version": self.manifold.identity,
        }
        
        # If action is allowed and has a direction, update current node
        if evaluation.get("allowed") and evaluation.get("direction"):
            if evaluation["direction"] != self.current_node:
                if self.manifold.can_transition(self.current_node, evaluation["direction"]):
                    self.set_node(evaluation["direction"])
                    result["transition_executed"] = True
        
        self.observation_log.append(result)
        return result
    
    def status(self):
        return {
            "current_node": self.current_node,
            "current_basin": self.manifold.get_basin_for(self.current_node),
            "node_info": self.manifold.get_node(self.current_node),
            "allowed_transitions": self.manifold.allowed_transitions(self.current_node),
            "best_transition": self.manifold.best_transition(self.current_node),
            "history_length": len(self.history),
        }


# ─── FastAPI ──────────────────────────────────────────────────────
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="EVEZ Phenomenologic Topology Engine", version="1.0.0")
router = PhenomenologicRouter()

class ActionRequest(BaseModel):
    action: str
    context: Optional[dict] = None

class NodeSetRequest(BaseModel):
    node_id: str

@app.get("/")
async def index():
    s = router.status()
    return {
        "service": "EVEZ Phenomenologic Topology Engine",
        "identity": router.manifold.identity,
        "current_node": s["current_node"],
        "current_basin": s["current_basin"],
        "affect": s["node_info"].get("affect"),
        "best_move": s["best_transition"]["to"] if s["best_transition"] else None,
    }

@app.post("/route")
async def route_action(req: ActionRequest):
    return router.route(req.action, req.context)

@app.post("/set_node")
async def set_node(req: NodeSetRequest):
    success = router.set_node(req.node_id)
    return {"set": success, "current": router.current_node}

@app.get("/status")
async def status():
    return router.status()

@app.get("/manifold")
async def manifold():
    return {
        "nodes": list(router.manifold.nodes.keys()),
        "basins": {k: v["nodes"] for k, v in router.manifold.basins.items()},
        "edges": [{"from": e["from"], "to": e["to"], "insight": e["weight"]["insight_yield"]} for e in router.manifold.edges],
    }

@app.get("/infer")
async def infer():
    node = router.infer_node_from_telemetry()
    router.set_node(node)
    return {"inferred_node": node, "current_basin": router.manifold.get_basin_for(node)}


if __name__ == "__main__":
    port = int(os.getenv("PTE_PORT", "8901"))
    print(f"⧢ EVEZ Phenomenologic Topology Engine on port {port}")
    print(f"   Identity: {router.manifold.identity}")
    print(f"   Current node: {router.current_node}")
    uvicorn.run(app, host="0.0.0.0", port=port)
