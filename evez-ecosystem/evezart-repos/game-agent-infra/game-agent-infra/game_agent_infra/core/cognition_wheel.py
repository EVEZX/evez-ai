"""
Cognitive Wheel — R1-R7 Piaget stages with ring_estimate tracking.
Each agent maintains stage + ring_estimate + controlled_reduction.
WITH TELEMETRY INTEGRATION
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict
import time

from . import telemetry


class Ring(Enum):
    R1 = "Beige"
    R2 = "Purple"
    R3 = "Red"
    R4 = "Blue"
    R5 = "Orange"
    R6 = "Green"
    R7 = "Yellow"


RING_CAPABILITY = {
    Ring.R1: 0.15,
    Ring.R2: 0.35,
    Ring.R3: 0.55,
    Ring.R4: 0.72,
    Ring.R5: 0.85,
    Ring.R6: 0.92,
    Ring.R7: 0.98,
}


@dataclass
class AgentState:
    agent_id: str
    stage: Ring
    ring_estimate: float  # 0.0–1.0 confidence in current stage
    controlled_reduction: float  # anomaly recovery rate
    Σf: float  # cumulative failure surfaces crossed
    CS: float  # cognitive sharpness
    PS: float  # predictive strength
    Ω: float  # singularity approach (lower is safer)


class CognitionWheel:
    def __init__(self):
        self.agents: Dict[str, AgentState] = {}
        # Telemetry: track cycle counts
        self._cycle_count = 0

    def register(self, agent_id: str, start_ring: Ring = Ring.R4) -> AgentState:
        state = AgentState(
            agent_id=agent_id,
            stage=start_ring,
            ring_estimate=0.65,
            controlled_reduction=0.12,
            Σf=0.0,
            CS=0.70,
            PS=0.75,
            Ω=0.05,
        )
        self.agents[agent_id] = state
        # Telemetry: emit registration event (safe fallback)
        try:
            ctx = telemetry.start_spine_append(agent_id, "register")
            ctx.__enter__()
        except:
            pass
        return state

    def update_cycle(self, agent_id: str, anomaly: str, tests_passed: int, tests_run: int) -> AgentState:
        state = self.agents[agent_id]
        self._cycle_count += 1
        
        prev_ring = state.ring_estimate
        prev_omega = state.Ω
        
        # Simple ring progression logic (placeholder for real model)
        if tests_passed == tests_run and state.Ω < 0.2:
            state.ring_estimate = min(1.0, state.ring_estimate + 0.05)
        else:
            state.controlled_reduction = max(0.0, state.controlled_reduction - 0.02)
            state.Ω = min(0.5, state.Ω + 0.01)
        state.Σf += 0.1
        
        # TELEMETRY INTEGRATION (safe fallback)
        try:
            telemetry.record_cognition_update(
                agent_id=agent_id,
                ring_estimate=state.ring_estimate,
                controlled_reduction=state.controlled_reduction,
                omega=state.Ω,
                sigma_f=state.Σf,
            )
        except:
            pass
        
        return state

    def get_telemetry_summary(self) -> dict:
        """Return current telemetry state summary."""
        return {
            "total_cycles": self._cycle_count,
            "agent_count": len(self.agents),
            "agents": {aid: {
                "ring_estimate": state.ring_estimate,
                "Ω": state.Ω,
                "Σf": state.Σf,
                "CS": state.CS,
                "PS": state.PS,
            } for aid, state in self.agents.items()}
        }