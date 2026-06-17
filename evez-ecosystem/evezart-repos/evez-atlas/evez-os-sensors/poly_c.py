"""
POLY_C — The Actual Computation
poly_c = τ × ω × topo / 2√N

τ (tau)   = temporal decay — how fast signal fades
ω (omega) = weight of the event — intensity × confidence
topo      = topological complexity — Betti vector magnitude
N         = number of observations — normalization by evidence

This was a slogan. Now it's a function.
"""

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class PolyCResult:
    """Result of the poly_c computation."""
    value: float
    tau: float
    omega: float
    topo: float
    n: int
    label: str  # "NULL", "SIGNAL", "FIRE", "CONVERGENCE", "EMERGENCE"

    @property
    def is_significant(self) -> bool:
        return self.value > 0.1

    @property
    def is_fire(self) -> bool:
        return self.value > 0.5

    @property
    def is_emergence(self) -> bool:
        return self.value > 0.8


def poly_c(
    event_age_seconds: float,
    intensity: float,
    confidence: float,
    betti_vector: list[int],
    observation_count: int,
    half_life_seconds: float = 3600.0
) -> PolyCResult:
    """
    Compute poly_c = τ × ω × topo / 2√N

    Parameters:
        event_age_seconds: How long ago the event occurred
        intensity: 0.0-1.0, sensor fire intensity
        confidence: 0.0-1.0, how confident the sensor is
        betti_vector: [b0, b1, b2, ...] topological invariants
        observation_count: Total observations feeding this computation
        half_life_seconds: Temporal decay half-life (default 1 hour)

    Returns:
        PolyCResult with computed value and components
    """
    # τ = e^(-t / half_life) — exponential temporal decay
    # Signal fades. Old events matter less. That's reality.
    tau = math.exp(-event_age_seconds / half_life_seconds)

    # ω = intensity × confidence — weighted signal strength
    # Strong signal we're sure about matters more.
    omega = intensity * confidence

    # topo = ||Betti vector|| — topological complexity
    # More structure = more significant
    topo = math.sqrt(sum(b * b for b in betti_vector)) if betti_vector else 0.0

    # N = max(observation_count, 1) — evidence normalization
    # More observations = more reliable, but diminishing returns
    n = max(observation_count, 1)

    # poly_c = τ × ω × topo / 2√N
    value = (tau * omega * topo) / (2 * math.sqrt(n))

    # Classify the result
    if value > 0.8:
        label = "EMERGENCE"
    elif value > 0.5:
        label = "FIRE"
    elif value > 0.2:
        label = "CONVERGENCE"
    elif value > 0.1:
        label = "SIGNAL"
    else:
        label = "NULL"

    return PolyCResult(
        value=round(value, 8),
        tau=round(tau, 6),
        omega=round(omega, 6),
        topo=round(topo, 6),
        n=n,
        label=label
    )


def poly_c_from_spine_events(events: list[dict], current_time: float) -> PolyCResult:
    """
    Compute poly_c from a list of spine events.
    Aggregates temporal decay across all events.
    """
    if not events:
        return PolyCResult(value=0.0, tau=0.0, omega=0.0, topo=0.0, n=0, label="NULL")

    # Weighted average of tau across events (recent events matter more)
    taus = []
    omegas = []
    for e in events:
        age = current_time - e.get("timestamp", current_time)
        tau = math.exp(-age / 3600.0)
        intensity = e.get("intensity", 0.0)
        taus.append(tau)
        omegas.append(intensity * tau)  # intensity weighted by recency

    tau = sum(taus) / len(taus) if taus else 0.0
    omega = sum(omegas) / len(omegas) if omegas else 0.0

    # Extract betti-like information from payload if available
    betti = []
    for e in events:
        payload = e.get("payload", {})
        if "betti_0" in payload:
            betti.append(payload["betti_0"])
        if "betti_1" in payload:
            betti.append(payload["betti_1"])

    if not betti:
        # Infer topological complexity from event count and variety
        sensors = set(e.get("sensor", "") for e in events)
        fires = set(e.get("fire", "") for e in events)
        betti = [len(sensors), len(fires)]

    topo = math.sqrt(sum(b * b for b in betti))
    n = max(len(events), 1)

    value = (tau * omega * topo) / (2 * math.sqrt(n))

    if value > 0.8:
        label = "EMERGENCE"
    elif value > 0.5:
        label = "FIRE"
    elif value > 0.2:
        label = "CONVERGENCE"
    elif value > 0.1:
        label = "SIGNAL"
    else:
        label = "NULL"

    return PolyCResult(
        value=round(value, 8),
        tau=round(tau, 6),
        omega=round(omega, 6),
        topo=round(topo, 6),
        n=n,
        label=label
    )
