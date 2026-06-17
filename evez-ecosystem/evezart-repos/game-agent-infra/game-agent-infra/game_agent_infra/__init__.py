"""
Game Agent Infra — Reusable cognitive infrastructure package.
Import this in any EVEZ-related repository for consistent:
- Immutable Event Spine
- Cognition Wheel (R1-R7)
- Failure Surface Cartography (FSC)
- Deterministic Simulation + Rollback
- OpenTelemetry hooks
- Self-maintenance protocols
"""

from .core.spine import AppendOnlySpine
from .core.cognition_wheel import CognitionWheel, Ring, AgentState
from .core.fsc import FSC, FSCCycle
from .core.simulation import SimulationEngine, Snapshot, Projection
from .core.test_harness import ReplayTestHarness
from .core.telemetry import (
    start_spine_append,
    start_fsc_cycle,
    record_cognition_update,
)

__version__ = "0.1.0"
__all__ = [
    "AppendOnlySpine",
    "CognitionWheel",
    "Ring",
    "AgentState",
    "FSC",
    "FSCCycle",
    "SimulationEngine",
    "Snapshot",
    "Projection",
    "ReplayTestHarness",
]