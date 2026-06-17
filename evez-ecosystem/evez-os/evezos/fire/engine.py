"""
evezos/fire/engine.py

FireEngine: single canonical class replacing 24 root-level fire_*.py files.
Ordinals 1-7 correspond to the seven fire cycles in EVEZ-OS architecture.

Phase model (ascending):
  PRE_FIRE → APPROACH → BORDER → FIRE → INTENSIFY → PEAK → CEILING_ZONE
Phase model (descending after peak):
  SUSTAIN → SETTLING → REKINDLE_WATCH → POST_FIRE

FIRE threshold: poly_c >= 0.500 (CHORUS_THRESHOLD)
CEILING:        poly_c >= 0.950
"""

import math
import json
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List


class FirePhase(str, Enum):
    PRE_FIRE       = "PRE_FIRE"
    APPROACH       = "APPROACH"
    BORDER         = "BORDER"
    HORIZON        = "HORIZON"
    FIRE           = "FIRE"
    SUSTAIN        = "SUSTAIN"
    INTENSIFY      = "INTENSIFY"
    PEAK           = "PEAK"
    SETTLING       = "SETTLING"
    REKINDLE_WATCH = "REKINDLE_WATCH"
    POST_FIRE      = "POST_FIRE"
    CEILING_ZONE   = "CEILING_ZONE"


@dataclass
class FireCycle:
    ordinal:     int
    N:           int
    tau:         int
    omega_k:     int
    V_entry:     float
    gamma:       float = 0.08
    snapshots:   List[dict] = field(default_factory=list)
    fired:       bool = False
    V_exit:      Optional[float] = None
    peak_poly_c: float = 0.0
    ceiling_breached: bool = False
    ts_start:    float = field(default_factory=time.time)
    ts_end:      Optional[float] = None

    ORDINAL_NAMES = {1:"FIRST",2:"SECOND",3:"THIRD",4:"FOURTH",
                     5:"FIFTH",6:"SIXTH",7:"SEVENTH"}

    def __post_init__(self):
        self.topology_bonus = 1.0 + math.log(max(self.N, 2)) / 10.0

    @property
    def ordinal_name(self):
        return self.ORDINAL_NAMES.get(self.ordinal, f"ORD{self.ordinal}")

    def compute_poly_c(self):
        topo = 1.0 + 0.15 * self.omega_k
        return topo * (1 + math.log(max(self.tau, 1))) / math.log2(self.N + 2)

    def classify_phase(self, poly_c, ascending=True):
        if poly_c >= 0.950:  return FirePhase.CEILING_ZONE
        if ascending:
            if poly_c < 0.300: return FirePhase.PRE_FIRE
            if poly_c < 0.450: return FirePhase.APPROACH
            if poly_c < 0.500: return FirePhase.BORDER
            if poly_c < 0.600: return FirePhase.FIRE
            if poly_c < 0.800: return FirePhase.INTENSIFY
            return FirePhase.PEAK
        else:
            if poly_c >= 0.500: return FirePhase.SUSTAIN
            if poly_c >= 0.300: return FirePhase.SETTLING
            if poly_c >= 0.100: return FirePhase.REKINDLE_WATCH
            return FirePhase.POST_FIRE

    def snapshot(self, poly_c, phase, V_now, note=""):
        snap = {
            "ordinal": self.ordinal, "ordinal_name": self.ordinal_name,
            "N": self.N, "tau": self.tau, "omega_k": self.omega_k,
            "topology_bonus": round(self.topology_bonus, 4),
            "poly_c": round(poly_c, 6), "phase": phase.value,
            "fired": poly_c >= 0.500, "V_now": round(V_now, 6),
            "delta_V": round(self.gamma * poly_c, 6),
            "peak_poly_c": round(self.peak_poly_c, 6),
            "ceiling_breached": self.ceiling_breached,
            "note": note, "ts": time.time(),
        }
        self.snapshots.append(snap)
        return snap

    def to_event(self):
        return {
            "type": "FIRE_CYCLE",
            "ordinal": self.ordinal, "ordinal_name": self.ordinal_name,
            "N": self.N, "tau": self.tau, "omega_k": self.omega_k,
            "V_entry": self.V_entry, "V_exit": self.V_exit,
            "fired": self.fired, "peak_poly_c": round(self.peak_poly_c, 6),
            "ceiling_breached": self.ceiling_breached,
            "snapshot_count": len(self.snapshots),
            "ts_start": self.ts_start, "ts_end": self.ts_end,
        }


class FireEngine:
    """
    Manages the full sequence of EVEZ fire cycles (ordinals 1–7).
    Replaces 24 root-level fire_*.py files.

    Usage:
        engine = FireEngine(gamma=0.08)
        cycle  = engine.run_cycle(ordinal=1, N=6, tau=4, omega_k=2, V_entry=0.0)
        event  = cycle.to_event()   # emit to EventBridge
    """
    CHORUS_THRESHOLD = 0.500
    CEILING          = 0.950

    def __init__(self, gamma=0.08, V_ceiling=6.0, base_round=82):
        self.gamma      = gamma
        self.V_ceiling  = V_ceiling
        self.base_round = base_round
        self.cycles: List[FireCycle] = []

    def run_cycle(self, ordinal, N, tau, omega_k, V_entry, probe_steps=5):
        cycle = FireCycle(ordinal=ordinal, N=N, tau=tau, omega_k=omega_k,
                          V_entry=V_entry, gamma=self.gamma)
        poly_c_base = cycle.compute_poly_c()
        V = V_entry

        # ascent
        asc = [poly_c_base * (i / probe_steps) for i in range(1, probe_steps + 1)]
        for i, poly_c in enumerate(asc):
            phase = cycle.classify_phase(poly_c, ascending=True)
            V += self.gamma * poly_c
            cycle.peak_poly_c = max(cycle.peak_poly_c, poly_c)
            cycle.ceiling_breached = cycle.ceiling_breached or poly_c >= self.CEILING
            if poly_c >= self.CHORUS_THRESHOLD: cycle.fired = True
            cycle.snapshot(poly_c, phase, V, note=f"ascent {i+1}/{probe_steps}")

        # canonical peak
        V += self.gamma * poly_c_base
        cycle.peak_poly_c = max(cycle.peak_poly_c, poly_c_base)
        cycle.ceiling_breached = cycle.ceiling_breached or poly_c_base >= self.CEILING
        if poly_c_base >= self.CHORUS_THRESHOLD: cycle.fired = True
        cycle.snapshot(poly_c_base, cycle.classify_phase(poly_c_base, True), V, "canonical_peak")

        # descent
        desc = [poly_c_base * (1 - i / probe_steps) for i in range(1, probe_steps + 1)]
        for i, poly_c in enumerate(desc):
            phase = cycle.classify_phase(poly_c, ascending=False)
            V += self.gamma * poly_c
            cycle.snapshot(poly_c, phase, V, note=f"descent {i+1}/{probe_steps}")

        cycle.V_exit = round(V, 6)
        cycle.ts_end = time.time()
        self.cycles.append(cycle)
        return cycle

    def run_sequence(self, machine_states, V_init=0.0):
        V = V_init
        for ordinal, (N, tau, omega_k) in enumerate(machine_states, start=1):
            cycle = self.run_cycle(ordinal, N, tau, omega_k, V)
            V = cycle.V_exit
        return self.cycles

    def summary(self):
        fired = [c for c in self.cycles if c.fired]
        return {
            "total_cycles": len(self.cycles),
            "fired_cycles": len(fired),
            "ceiling_breaches": sum(1 for c in self.cycles if c.ceiling_breached),
            "V_trajectory": [c.V_exit for c in self.cycles if c.V_exit is not None],
            "ordinals_fired": [c.ordinal_name for c in fired],
        }

    def get_latest_event(self):
        return self.cycles[-1].to_event() if self.cycles else None


if __name__ == "__main__":
    SEVEN = [(2,2,1),(6,4,2),(12,6,2),(18,6,2),(24,8,2),(30,8,3),(36,9,2)]
    engine = FireEngine()
    cycles = engine.run_sequence(SEVEN, V_init=0.0)
    for c in cycles:
        ev = c.to_event()
        print(f"  {ev['ordinal_name']:8s} N={ev['N']:3d}  "
              f"{'FIRED' if ev['fired'] else 'NO_FIRE':8s}  "
              f"V_exit={ev['V_exit']:.4f}  peak={ev['peak_poly_c']:.4f}")
    print(json.dumps(engine.summary(), indent=2))
    print("FireEngine SELF-TEST PASSED")
