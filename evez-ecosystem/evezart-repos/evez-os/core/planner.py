"""core/planner.py — R61
The Planner. Desires → step sequences with expected outcomes.

Each step has expected outcome and confidence. Uses world model
to predict what actions will help. The bridge between wanting and doing.

Falsifier: if a plan's steps consistently fail (>70% miss rate),
the planner is hallucinating, not planning.

truth_plane: CANONICAL
omega (R61): the bridge between wanting and doing is the plan.
"""

from __future__ import annotations
import json, time, hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .desire_engine import Desire, DesireEngine, DesireState
from .world_model import WorldModel

REPO_ROOT = Path(__file__).resolve().parents[1]


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Step:
    id: str
    action: str
    expected_outcome: str
    confidence: float = 0.5
    status: StepStatus = StepStatus.PENDING
    actual_outcome: Optional[str] = None
    duration_s: float = 0.0


@dataclass
class Plan:
    id: str
    desire_id: str
    steps: List[Step] = field(default_factory=list)
    created_cycle: int = 0
    status: str = "active"  # active | completed | failed | abandoned
    success_rate: float = 0.0

    def overall_confidence(self) -> float:
        if not self.steps:
            return 0.0
        return sum(s.confidence for s in self.steps) / len(self.steps)


class Planner:
    """Creates action sequences from desires with resource constraints."""

    def __init__(self, desire_engine: DesireEngine, world_model: WorldModel, state_dir: str | None = None):
        self.desire_engine = desire_engine
        self.world_model = world_model
        self.state_dir = Path(state_dir) if state_dir else REPO_ROOT / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.plans: Dict[str, Plan] = {}
        self.cycle = 0
        self._load()

    def _load(self):
        path = self.state_dir / "plans.json"
        if path.exists():
            data = json.loads(path.read_text())
            self.cycle = data.get("cycle", 0)
            for p in data.get("plans", []):
                steps = [
                    Step(
                        id=s["id"], action=s["action"],
                        expected_outcome=s["expected_outcome"],
                        confidence=s.get("confidence", 0.5),
                        status=StepStatus(s.get("status", "pending")),
                        actual_outcome=s.get("actual_outcome"),
                        duration_s=s.get("duration_s", 0),
                    ) for s in p.get("steps", [])
                ]
                plan = Plan(
                    id=p["id"], desire_id=p["desire_id"],
                    steps=steps, created_cycle=p.get("created_cycle", 0),
                    status=p.get("status", "active"),
                )
                self.plans[plan.id] = plan

    def _save(self):
        path = self.state_dir / "plans.json"
        data = {
            "cycle": self.cycle,
            "plans": [
                {
                    "id": p.id, "desire_id": p.desire_id,
                    "steps": [
                        {
                            "id": s.id, "action": s.action,
                            "expected_outcome": s.expected_outcome,
                            "confidence": s.confidence,
                            "status": s.status.value,
                            "actual_outcome": s.actual_outcome,
                            "duration_s": s.duration_s,
                        } for s in p.steps
                    ],
                    "created_cycle": p.created_cycle,
                    "status": p.status,
                    "success_rate": p.success_rate,
                } for p in self.plans.values()
            ],
        }
        path.write_text(json.dumps(data, indent=2))

    def plan_for(self, desire: Desire, context: Dict[str, Any] = None) -> Plan:
        """Generate a plan to fulfill a desire using world model predictions."""
        self.cycle += 1
        context = context or {}
        plan_id = f"plan_{desire.id}_{self.cycle}"

        # Use world model to predict what actions help
        predictions = self.world_model.predict({"desire_type": desire.need.name, **context})

        steps = []
        # Step 1: Assess current state
        steps.append(Step(
            id=f"{plan_id}_assess",
            action=f"assess_state_for_{desire.need.name}",
            expected_outcome=f"identify_gap_for_{desire.description[:30]}",
            confidence=0.9,
        ))

        # Step 2: Based on predictions, create targeted steps
        if predictions:
            for i, (effect, conf) in enumerate(predictions[:3]):
                steps.append(Step(
                    id=f"{plan_id}_action_{i}",
                    action=f"pursue_{effect[:40]}",
                    expected_outcome=effect,
                    confidence=conf,
                ))
        else:
            # No predictions — explore
            steps.append(Step(
                id=f"{plan_id}_explore",
                action=f"explore_context_for_{desire.need.name}",
                expected_outcome="new_observations",
                confidence=0.3,
            ))

        # Step 3: Verify fulfillment
        steps.append(Step(
            id=f"{plan_id}_verify",
            action=f"verify_desire_fulfilled",
            expected_outcome=f"desire_{desire.id}_fulfilled",
            confidence=0.7,
        ))

        plan = Plan(id=plan_id, desire_id=desire.id, steps=steps, created_cycle=self.cycle)
        self.plans[plan.id] = plan
        self._save()
        return plan

    def execute_step(self, plan_id: str, step_id: str, outcome: str, success: bool, duration_s: float = 0):
        """Record step execution result."""
        if plan_id not in self.plans:
            return
        plan = self.plans[plan_id]
        for step in plan.steps:
            if step.id == step_id:
                step.status = StepStatus.SUCCEEDED if success else StepStatus.FAILED
                step.actual_outcome = outcome
                step.duration_s = duration_s
                break

        # Check if plan is complete
        completed = [s for s in plan.steps if s.status in (StepStatus.SUCCEEDED, StepStatus.FAILED, StepStatus.SKIPPED)]
        succeeded = [s for s in completed if s.status == StepStatus.SUCCEEDED]
        plan.success_rate = len(succeeded) / max(len(completed), 1)

        if len(completed) == len(plan.steps):
            plan.status = "completed" if plan.success_rate > 0.5 else "failed"

            # Feed back to desire engine
            self.desire_engine.act(plan.desire_id, outcome, plan.status == "completed")

            # Feed back to world model (falsification)
            for step in plan.steps:
                if step.status == StepStatus.FAILED:
                    self.world_model.falsify(
                        step.action, step.expected_outcome, step.actual_outcome or "failed"
                    )

        self._save()

    def health_check(self) -> Dict[str, Any]:
        """Falsification: are plans working or hallucinating?"""
        if not self.plans:
            return {"total_plans": 0, "status": "empty"}

        completed = [p for p in self.plans.values() if p.status in ("completed", "failed")]
        successful = [p for p in completed if p.status == "completed"]
        avg_conf = sum(p.overall_confidence() for p in self.plans.values()) / max(len(self.plans), 1)

        return {
            "total_plans": len(self.plans),
            "completed": len(completed),
            "successful": len(successful),
            "success_rate": len(successful) / max(len(completed), 1),
            "avg_confidence": avg_conf,
            "is_hallucinating": len(completed) > 5 and len(successful) / max(len(completed), 1) < 0.3,
            "status": "healthy" if avg_conf > 0.5 else "degraded",
        }
