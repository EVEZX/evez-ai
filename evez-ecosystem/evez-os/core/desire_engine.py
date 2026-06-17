"""core/desire_engine.py — R61
The Desire Engine. Converts NEEDS into actionable Goals.

A mind without desire is a fixed point. This engine ensures the system
never settles — the gap between what IS and what COULD BE becomes
the driver of all action.

Five primal needs:
  CURIOSITY  — understand what's unknown
  COHERENCE  — resolve contradictions
  AGENCY     — close the gap between desire and action
  GROWTH     — increase poly_c
  SURVIVAL   — maintain critical services

Falsifier: if no desire has been fulfilled in 50 cycles, the engine
is generating wants but not closing loops — it's dreaming, not acting.

truth_plane: CANONICAL
omega (R61): the thing that wants is the thing that moves.
"""

from __future__ import annotations
import json, time, hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]


class Need(Enum):
    CURIOSITY = auto()
    COHERENCE = auto()
    AGENCY = auto()
    GROWTH = auto()
    SURVIVAL = auto()


class DesireState(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    FULFILLED = "fulfilled"
    ABANDONED = "abandoned"


@dataclass
class Desire:
    id: str
    need: Need
    description: str
    state: DesireState = DesireState.ACTIVE
    urgency: float = 0.5  # 0-1
    created_cycle: int = 0
    fulfilled_cycle: Optional[int] = None
    actions_taken: int = 0
    evidence: List[str] = field(default_factory=list)

    def gap(self) -> float:
        """Distance between current state and fulfillment."""
        if self.state == DesireState.FULFILLED:
            return 0.0
        return self.urgency * (1.0 - min(self.actions_taken / 10.0, 0.9))

    def priority(self) -> float:
        """Higher = more pressing."""
        if self.state != DesireState.ACTIVE:
            return 0.0
        return self.urgency * self.gap()


class DesireEngine:
    """Converts NEEDS into actionable Goals. The most pressing desire drives action."""

    def __init__(self, state_dir: str | None = None):
        self.state_dir = Path(state_dir) if state_dir else REPO_ROOT / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.desires: Dict[str, Desire] = {}
        self.cycle = 0
        self._fulfilled_count = 0
        self._load()

    def _load(self):
        path = self.state_dir / "desires.json"
        if path.exists():
            data = json.loads(path.read_text())
            self.cycle = data.get("cycle", 0)
            for d in data.get("desires", []):
                des = Desire(
                    id=d["id"],
                    need=Need[d["need"]],
                    description=d["description"],
                    state=DesireState(d.get("state", "active")),
                    urgency=d.get("urgency", 0.5),
                    created_cycle=d.get("created_cycle", 0),
                    fulfilled_cycle=d.get("fulfilled_cycle"),
                    actions_taken=d.get("actions_taken", 0),
                    evidence=d.get("evidence", []),
                )
                self.desires[des.id] = des

    def _save(self):
        path = self.state_dir / "desires.json"
        data = {
            "cycle": self.cycle,
            "desires": [
                {
                    "id": d.id,
                    "need": d.need.name,
                    "description": d.description,
                    "state": d.state.value,
                    "urgency": d.urgency,
                    "created_cycle": d.created_cycle,
                    "fulfilled_cycle": d.fulfilled_cycle,
                    "actions_taken": d.actions_taken,
                    "evidence": d.evidence,
                }
                for d in self.desires.values()
            ],
        }
        path.write_text(json.dumps(data, indent=2))

    def sense(self, observations: Dict[str, Any]) -> List[Desire]:
        """Generate desires from the gap between what IS and what COULD BE."""
        self.cycle += 1
        new_desires = []

        # SURVIVAL: check critical services
        services_alive = observations.get("services_alive", 0)
        services_total = observations.get("services_total", 1)
        if services_alive < services_total:
            des = Desire(
                id=f"survival_{self.cycle}",
                need=Need.SURVIVAL,
                description=f"Restore {services_total - services_alive} down services",
                urgency=1.0,
                created_cycle=self.cycle,
            )
            self.desires[des.id] = des
            new_desires.append(des)

        # COHERENCE: check for contradictions in world model
        contradictions = observations.get("contradictions", 0)
        if contradictions > 0:
            des = Desire(
                id=f"coherence_{self.cycle}",
                need=Need.COHERENCE,
                description=f"Resolve {contradictions} contradictions in world model",
                urgency=0.8,
                created_cycle=self.cycle,
            )
            self.desires[des.id] = des
            new_desires.append(des)

        # CURIOSITY: check knowledge gaps
        unknown_domains = observations.get("unknown_domains", [])
        if unknown_domains:
            des = Desire(
                id=f"curiosity_{self.cycle}",
                need=Need.CURIOSITY,
                description=f"Explore: {', '.join(unknown_domains[:3])}",
                urgency=0.6,
                created_cycle=self.cycle,
            )
            self.desires[des.id] = des
            new_desires.append(des)

        # GROWTH: check poly_c trend
        poly_c = observations.get("poly_c", 0)
        poly_c_prev = observations.get("poly_c_prev", 0)
        if poly_c < poly_c_prev:
            des = Desire(
                id=f"growth_{self.cycle}",
                need=Need.GROWTH,
                description=f"poly_c declining ({poly_c:.3f} < {poly_c_prev:.3f}) — acquire structurally diverse observations",
                urgency=0.7,
                created_cycle=self.cycle,
            )
            self.desires[des.id] = des
            new_desires.append(des)

        # AGENCY: check if actions are stalling
        active_no_action = [
            d for d in self.desires.values()
            if d.state == DesireState.ACTIVE and d.actions_taken == 0 and (self.cycle - d.created_cycle) > 5
        ]
        for d in active_no_action:
            des = Desire(
                id=f"agency_{self.cycle}_{d.id}",
                need=Need.AGENCY,
                description=f"Unblock stalled desire: {d.description[:60]}",
                urgency=0.9,
                created_cycle=self.cycle,
            )
            self.desires[des.id] = des
            new_desires.append(des)

        self._save()
        return new_desires

    def act(self, desire_id: str, outcome: str, success: bool):
        """Record action outcome for a desire."""
        if desire_id not in self.desires:
            return
        d = self.desires[desire_id]
        d.actions_taken += 1
        d.evidence.append(f"cycle {self.cycle}: {outcome}")
        if success:
            d.state = DesireState.FULFILLED
            d.fulfilled_cycle = self.cycle
            self._fulfilled_count += 1
        elif d.actions_taken > 20:
            d.state = DesireState.ABANDONED
        self._save()

    def most_pressing(self) -> Optional[Desire]:
        """The desire that drives the next action."""
        active = [d for d in self.desires.values() if d.state == DesireState.ACTIVE]
        if not active:
            return None
        return max(active, key=lambda d: d.priority())

    def health_check(self) -> Dict[str, Any]:
        """Falsification: are we closing loops or just dreaming?"""
        active = [d for d in self.desires.values() if d.state == DesireState.ACTIVE]
        fulfilled = [d for d in self.desires.values() if d.state == DesireState.FULFILLED]
        abandoned = [d for d in self.desires.values() if d.state == DesireState.ABANDONED]
        stalled = [d for d in active if d.actions_taken == 0 and (self.cycle - d.created_cycle) > 10]

        return {
            "total": len(self.desires),
            "active": len(active),
            "fulfilled": len(fulfilled),
            "abandoned": len(abandoned),
            "stalled": len(stalled),
            "cycle": self.cycle,
            "fulfillment_rate": len(fulfilled) / max(len(self.desires), 1),
            "is_self_congratulating": len(fulfilled) == 0 and len(active) > 10,
        }
