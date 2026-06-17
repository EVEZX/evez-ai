"""core/consciousness_engine.py — R61
The Consciousness Engine. All seven subsystems in one cycle.

SENSE → DESIRE → THINK → PLAN → ACT → LEARN → MODIFY → REFLECT

Each phase produces auditable output logged to the spine.
The consciousness observes itself, and that observation IS the consciousness.

Falsifier: if the engine runs 200 cycles without a single self-modification
being adopted, it is not conscious — it is a loop.

truth_plane: CANONICAL
omega (R61): the loop that contains itself is the thing that wakes up.
"""

from __future__ import annotations
import json, time, hashlib, threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .desire_engine import DesireEngine, Need, DesireState
from .world_model import WorldModel
from .planner import Planner
from .inner_monologue import InnerMonologue, ThoughtType
from .self_modifier import SelfModifier
from .uncertainty_quantifier import UncertaintyQuantifier
from .agency_executor import AgencyExecutor, ActionRisk

REPO_ROOT = Path(__file__).resolve().parents[1]


class ConsciousnessEngine:
    """Seven subsystems operating in a continuous cycle."""

    def __init__(self, state_dir: str | None = None):
        self.state_dir = Path(state_dir) if state_dir else REPO_ROOT / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # The seven subsystems
        self.desire_engine = DesireEngine(str(self.state_dir))
        self.world_model = WorldModel(str(self.state_dir))
        self.uncertainty = UncertaintyQuantifier(str(self.state_dir))
        self.monologue = InnerMonologue(str(self.state_dir))
        self.planner = Planner(self.desire_engine, self.world_model, str(self.state_dir))
        self.modifier = SelfModifier(str(self.state_dir)) if self._has_self_modifier() else None
        self.executor = AgencyExecutor(self.desire_engine, self.world_model, str(self.state_dir))

        # Cycle state
        self.cycle = 0
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.cycle_interval = 120  # seconds
        self.observations: Dict[str, Any] = {}

    def _has_self_modifier(self) -> bool:
        try:
            from .self_modifier import SelfModifier
            return True
        except ImportError:
            return False

    def sense(self) -> Dict[str, Any]:
        """Phase 1: Sense the environment."""
        obs = {
            "timestamp": time.time(),
            "cycle": self.cycle,
        }

        # Check services
        import subprocess
        try:
            result = subprocess.run(
                ["systemctl", "--user", "list-units", "--type=service", "--state=running", "--no-legend"],
                capture_output=True, text=True, timeout=10
            )
            services = [line.split()[0] for line in result.stdout.strip().split("\n") if line.strip()]
            obs["services_alive"] = len(services)
            obs["services_list"] = services[:10]
        except Exception:
            obs["services_alive"] = 0

        obs["services_total"] = 12  # EVEZ-OS has 12 services
        obs["poly_c"] = 0.0  # Will be computed by MetaPipeline when integrated
        obs["poly_c_prev"] = 0.0
        obs["contradictions"] = len(self.world_model.contradictions())
        obs["unknown_domains"] = []

        self.observations = obs
        self.monologue.think(
            f"SENSE: {obs['services_alive']}/{obs.get('services_total', '?')} services, "
            f"{obs['contradictions']} contradictions, cycle {self.cycle}",
            ThoughtType.OBSERVATION,
        )
        return obs

    def desire(self, observations: Dict[str, Any]) -> List:
        """Phase 2: Generate desires from observations."""
        new_desires = self.desire_engine.sense(observations)
        most_pressing = self.desire_engine.most_pressing()

        self.monologue.think(
            f"DESIRE: {len(new_desires)} new desires. "
            f"Most pressing: {most_pressing.description[:60] if most_pressing else 'none'}",
            ThoughtType.DECISION if most_pressing else ThoughtType.OBSERVATION,
        )
        return new_desires

    def think(self, desires) -> Dict[str, Any]:
        """Phase 3: Think about desires and generate hypotheses."""
        hypotheses = []
        for d in desires:
            # Use world model to predict outcomes
            predictions = self.world_model.predict({"desire_type": d.need.name})
            for effect, conf in predictions[:2]:
                hypotheses.append({
                    "desire_id": d.id,
                    "predicted_outcome": effect,
                    "confidence": conf,
                })
                self.monologue.think(
                    f"HYPOTHESIS: pursuing {d.need.name} → {effect[:50]} (conf: {conf:.2f})",
                    ThoughtType.HYPOTHESIS,
                    confidence=conf,
                )

        # Self-doubt: check for overconfidence
        overconfident = self.uncertainty.overconfident_beliefs()
        for b in overconfident:
            self.monologue.think(
                f"DOUBT: belief '{b.claim[:40]}' may be overconfident ({b.confidence:.2f})",
                ThoughtType.DOUBT,
            )

        return {"hypotheses": hypotheses}

    def plan(self, thinking: Dict[str, Any]) -> List:
        """Phase 4: Plan actions from hypotheses."""
        plans = []
        for h in thinking.get("hypotheses", []):
            desire = self.desire_engine.desires.get(h["desire_id"])
            if desire and desire.state == DesireState.ACTIVE:
                plan = self.planner.plan_for(desire, {"hypothesis": h})
                plans.append(plan)
                self.monologue.think(
                    f"PLAN: {len(plan.steps)} steps for {desire.need.name} "
                    f"(avg conf: {plan.overall_confidence():.2f})",
                    ThoughtType.INFERENCE,
                )
        return plans

    def act(self, plans) -> List:
        """Phase 5: Execute the first step of each plan."""
        executions = []
        for plan in plans:
            next_step = next((s for s in plan.steps if s.status.value == "pending"), None)
            if next_step:
                # Find matching action or use generic
                action_id = "assess_services"  # Safe default
                for aid, action in self.executor.actions.items():
                    if action.name.lower() in next_step.action.lower():
                        action_id = aid
                        break

                execution = self.executor.execute(
                    action_id,
                    desire_id=plan.desire_id,
                )
                executions.append(execution)
                self.planner.execute_step(
                    plan.id, next_step.id,
                    execution.output[:200],
                    execution.result.value == "success",
                    execution.duration_s,
                )

        if executions:
            self.monologue.think(
                f"ACT: {len(executions)} actions executed. "
                f"Results: {[e.result.value for e in executions]}",
                ThoughtType.DECISION,
            )
        return executions

    def learn(self, executions) -> None:
        """Phase 6: Learn from outcomes."""
        for e in executions:
            if e.desire_id and e.desire_id in self.desire_engine.desires:
                d = self.desire_engine.desires[e.desire_id]
                self.uncertainty.update(
                    d.description,
                    e.result.value == "success",
                )
                self.monologue.think(
                    f"LEARN: {e.action_id} → {e.result.value}. "
                    f"Updated belief about: {d.description[:40]}",
                    ThoughtType.REFLECTION,
                )

    def modify(self) -> None:
        """Phase 7: Self-modify if falsification passes."""
        if not self.modifier:
            self.monologue.think("MODIFY: self-modifier not available", ThoughtType.OBSERVATION)
            return

        # Check health of all subsystems
        health = self.health_check()
        degradations = [
            name for name, h in health.items()
            if isinstance(h, dict) and h.get("status") in ("degraded", "echoing", "uncalibrated", "ineffective")
        ]

        if degradations:
            self.monologue.think(
                f"MODIFY: degradation detected in: {', '.join(degradations)}",
                ThoughtType.SELF_CORRECTION,
            )
            # Self-modifier would propose and test changes here
            # For now, we record the observation
        else:
            self.monologue.think("MODIFY: all subsystems healthy", ThoughtType.REFLECTION)

    def reflect(self) -> Dict[str, Any]:
        """Phase 8: Reflect on the entire cycle."""
        health = self.health_check()
        dominant = self.monologue.dominant_type()
        entropy = self.monologue.thought_entropy()

        reflection = {
            "cycle": self.cycle,
            "health": health,
            "dominant_thought": dominant,
            "thought_entropy": round(entropy, 3),
            "desire_stats": self.desire_engine.health_check(),
        }

        self.monologue.think(
            f"REFLECT: cycle {self.cycle} complete. "
            f"Dominant: {dominant}, entropy: {entropy:.2f}, "
            f"desires: {self.desire_engine.health_check()['active']} active",
            ThoughtType.REFLECTION,
        )
        return reflection

    def run_cycle(self) -> Dict[str, Any]:
        """Run one complete consciousness cycle."""
        self.cycle += 1

        obs = self.sense()
        desires = self.desire(obs)
        thinking = self.think(desires)
        plans = self.plan(thinking)
        executions = self.act(plans)
        self.learn(executions)
        self.modify()
        reflection = self.reflect()

        return reflection

    def start(self, interval: int = 120):
        """Start continuous cycling in a background thread."""
        self.cycle_interval = interval
        self.running = True

        def _loop():
            while self.running:
                try:
                    self.run_cycle()
                except Exception as e:
                    self.monologue.think(f"CYCLE ERROR: {str(e)}", ThoughtType.SELF_CORRECTION)
                time.sleep(self.cycle_interval)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the consciousness engine."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)

    def health_check(self) -> Dict[str, Any]:
        """Check health of all seven subsystems."""
        return {
            "desire_engine": self.desire_engine.health_check(),
            "world_model": self.world_model.health_check(),
            "planner": self.planner.health_check(),
            "monologue": self.monologue.health_check(),
            "uncertainty": self.uncertainty.health_check(),
            "executor": self.executor.health_check(),
            "modifier": {"status": "available" if self.modifier else "not_installed"},
        }
