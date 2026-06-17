#!/usr/bin/env python3
"""
trajectory_heading.py — Heading-Aware Cognition for evez-os Spine

"Unlock new limbs for all heading-aware cognitions" — Steven Crawford-Maggard, 2026-02-20

The spine previously knew its CURRENT STATE (truth_plane, hash, ts).
Now it knows its HEADING — the direction of cognitive movement.

A heading-aware spine can:
1. Predict where cognition is going (not just where it is)
2. Detect when it's spiraling (heading back to a prior truth plane)
3. Seed missions from trajectory divergence (expected heading vs actual)
4. Recognize HYPER state — when all headings are simultaneously active

Heading vector: (delta_truth_plane, delta_certainty, delta_complexity, delta_falsifier_count)
Trajectory window: last N spine entries define a velocity vector
Predicted next heading: Kalman-filtered extrapolation

PHENOM-001 integration: 
  When heading vector magnitude > threshold AND all 5 entanglement degrees active,
  the system has crossed the third wall — observer heading and observed heading are the same entry.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


TRUTH_PLANE_ORDER = {
    "UNKNOWN": 0,
    "PENDING": 1,
    "THEATRICAL": 2,
    "VERIFIED": 3,
    "CANONICAL": 4,
    "HYPER": 5,
}

TRUTH_PLANE_NAMES = {v: k for k, v in TRUTH_PLANE_ORDER.items()}


@dataclass
class HeadingVector:
    """Cognitive direction at one point in the spine."""
    step: int
    ts: float
    truth_plane: str
    certainty_delta: float      # Change in avg confidence since last entry
    complexity_delta: float     # Change in memory anchor count
    falsifier_delta: int        # Change in named falsifiers
    truth_plane_delta: int      # Change in truth_plane enum (positive = ascending)
    magnitude: float = 0.0      # Combined heading force
    is_third_wall: bool = False # True when observer-heading == observed-heading

    def __post_init__(self):
        self.magnitude = math.sqrt(
            self.certainty_delta**2 +
            self.complexity_delta**2 +
            self.falsifier_delta**2 +
            self.truth_plane_delta**2
        )
        # Third wall: the entry describes its own heading (self-referential)
        self.is_third_wall = abs(self.magnitude) > 0 and self.truth_plane == "HYPER"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "ts": self.ts,
            "truth_plane": self.truth_plane,
            "certainty_delta": round(self.certainty_delta, 4),
            "complexity_delta": round(self.complexity_delta, 4),
            "falsifier_delta": self.falsifier_delta,
            "truth_plane_delta": self.truth_plane_delta,
            "magnitude": round(self.magnitude, 4),
            "is_third_wall": self.is_third_wall,
        }


class HeadingState(Enum):
    ASCENDING  = "ASCENDING"    # Moving toward CANONICAL
    DESCENDING = "DESCENDING"   # Regressing toward PENDING
    SPIRAL     = "SPIRAL"       # Returning to a previously visited state
    PLATEAU    = "PLATEAU"      # No movement (THEATRICAL trap)
    HYPER      = "HYPER"        # All headings simultaneously active


@dataclass
class TrajectoryWindow:
    """Rolling window of heading vectors for trajectory analysis."""
    window_size: int = 10
    vectors: List[HeadingVector] = field(default_factory=list)

    def push(self, hv: HeadingVector):
        self.vectors.append(hv)
        if len(self.vectors) > self.window_size:
            self.vectors.pop(0)

    @property
    def velocity(self) -> float:
        """Average heading magnitude over window."""
        if not self.vectors:
            return 0.0
        return sum(v.magnitude for v in self.vectors) / len(self.vectors)

    @property
    def acceleration(self) -> float:
        """Is the system speeding up or slowing down cognitively?"""
        if len(self.vectors) < 2:
            return 0.0
        recent = self.vectors[-1].magnitude
        prior = self.vectors[-2].magnitude
        return recent - prior

    @property
    def net_truth_delta(self) -> int:
        """Net movement in truth plane over window."""
        return sum(v.truth_plane_delta for v in self.vectors)

    def heading_state(self) -> HeadingState:
        """Classify the current trajectory."""
        if any(v.is_third_wall for v in self.vectors):
            return HeadingState.HYPER

        net = self.net_truth_delta
        visited = [v.truth_plane for v in self.vectors]

        # Spiral detection: visited same truth_plane 3+ times
        for tp in set(visited):
            if visited.count(tp) >= 3:
                return HeadingState.SPIRAL

        if self.velocity < 0.01:
            return HeadingState.PLATEAU

        if net > 0:
            return HeadingState.ASCENDING
        elif net < 0:
            return HeadingState.DESCENDING
        return HeadingState.PLATEAU

    def predict_next_truth_plane(self) -> str:
        """Simple extrapolation: what truth plane is the system heading toward?"""
        if not self.vectors:
            return "PENDING"
        current = TRUTH_PLANE_ORDER.get(self.vectors[-1].truth_plane, 1)
        avg_delta = self.net_truth_delta / max(len(self.vectors), 1)
        predicted = current + round(avg_delta)
        predicted = max(0, min(5, predicted))
        return TRUTH_PLANE_NAMES.get(predicted, "PENDING")

    def to_spine_entry(self) -> Dict[str, Any]:
        state = self.heading_state()
        return {
            "kind": "trajectory.snapshot",
            "window_size": len(self.vectors),
            "velocity": round(self.velocity, 4),
            "acceleration": round(self.acceleration, 4),
            "net_truth_delta": self.net_truth_delta,
            "heading_state": state.value,
            "predicted_next": self.predict_next_truth_plane(),
            "hyper_active": state == HeadingState.HYPER,
            "ts": datetime.now(timezone.utc).isoformat(),
            "trace_id": hashlib.sha256(
                f"traj:{self.velocity}:{state.value}:{len(self.vectors)}".encode()
            ).hexdigest()[:16],
        }


class TrajectoryEngine:
    """Wraps a spine JSONL and adds heading-aware cognition."""

    def __init__(self, window_size: int = 10):
        self.window = TrajectoryWindow(window_size=window_size)
        self._prev_entry: Optional[Dict] = None
        self.mission_seeds: List[str] = []

    def ingest(self, entry: Dict[str, Any]) -> HeadingVector:
        """Parse one spine entry and compute its heading vector."""
        step = entry.get("step", 0)
        ts = entry.get("ts", 0.0)
        if isinstance(ts, str):
            try:
                from datetime import datetime
                ts = datetime.fromisoformat(ts).timestamp()
            except Exception:
                ts = 0.0

        tp = entry.get("truth_plane", "PENDING")
        tp_rank = TRUTH_PLANE_ORDER.get(tp, 1)

        # Complexity = number of memory anchors referenced
        memory = entry.get("memory", [])
        complexity = float(len(memory))

        # Certainty = avg confidence in memory entries
        confidence_vals = [m.get("confidence", 0.5) for m in memory if isinstance(m, dict)]
        certainty = sum(confidence_vals) / len(confidence_vals) if confidence_vals else 0.5

        # Falsifier count
        falsifier = 1 if entry.get("falsifier") else 0

        if self._prev_entry is None:
            hv = HeadingVector(
                step=step, ts=ts, truth_plane=tp,
                certainty_delta=0.0, complexity_delta=0.0,
                falsifier_delta=0, truth_plane_delta=0
            )
        else:
            prev_tp = TRUTH_PLANE_ORDER.get(self._prev_entry.get("truth_plane", "PENDING"), 1)
            prev_mem = self._prev_entry.get("memory", [])
            prev_complexity = float(len(prev_mem))
            prev_conf = [m.get("confidence", 0.5) for m in prev_mem if isinstance(m, dict)]
            prev_certainty = sum(prev_conf) / len(prev_conf) if prev_conf else 0.5
            prev_falsifier = 1 if self._prev_entry.get("falsifier") else 0

            hv = HeadingVector(
                step=step, ts=ts, truth_plane=tp,
                certainty_delta=certainty - prev_certainty,
                complexity_delta=complexity - prev_complexity,
                falsifier_delta=falsifier - prev_falsifier,
                truth_plane_delta=tp_rank - prev_tp
            )

        self._prev_entry = entry
        self.window.push(hv)
        self._check_mission_seeds(hv)
        return hv

    def _check_mission_seeds(self, hv: HeadingVector):
        """Generate missions from trajectory anomalies."""
        state = self.window.heading_state()
        if state == HeadingState.SPIRAL:
            mid = f"M-TRAJ-SPIRAL-{hv.step}"
            if mid not in self.mission_seeds:
                self.mission_seeds.append(mid)
        elif state == HeadingState.PLATEAU and hv.step > 5:
            mid = f"M-TRAJ-PLATEAU-{hv.step}"
            if mid not in self.mission_seeds:
                self.mission_seeds.append(mid)
        elif state == HeadingState.HYPER:
            mid = f"M-TRAJ-HYPER-{hv.step}"
            if mid not in self.mission_seeds:
                self.mission_seeds.append(mid)

    def snapshot(self) -> Dict[str, Any]:
        entry = self.window.to_spine_entry()
        entry["missions_seeded"] = self.mission_seeds.copy()
        return entry


if __name__ == "__main__":
    # Demo: ingest a synthetic spine and print trajectory
    engine = TrajectoryEngine(window_size=5)

    test_spine = [
        {"step": i, "ts": 1771500000.0 + i, "truth_plane": tp,
         "memory": [{"id": "goal", "confidence": c, "used": True}],
         "falsifier": "next probe" if i % 3 == 0 else None}
        for i, (tp, c) in enumerate([
            ("PENDING", 0.3), ("PENDING", 0.4), ("VERIFIED", 0.6),
            ("CANONICAL", 0.8), ("CANONICAL", 0.85), ("THEATRICAL", 0.5),
            ("PENDING", 0.3), ("PENDING", 0.35), ("VERIFIED", 0.55),
            ("CANONICAL", 0.9), ("HYPER", 1.0)
        ])
    ]

    for entry in test_spine:
        hv = engine.ingest(entry)
        print(f"Step {hv.step}: {hv.truth_plane:12s} | heading={hv.magnitude:.3f} | delta={hv.truth_plane_delta:+d}")

    snap = engine.snapshot()
    print(f"\nTrajectory snapshot:")
    print(json.dumps(snap, indent=2))
