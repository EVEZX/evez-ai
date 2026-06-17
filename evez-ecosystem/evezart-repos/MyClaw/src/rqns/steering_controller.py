"""
Steering Controller v2 — Wasserstein Divergence + Pareto Frontier
===================================================================
Measures drift between current latency distribution and target.
When divergence > 63.59 (critical threshold), forces Tier-3 offload.
Live Pareto frontier: latency vs energy, the engineering trade surface.
"""
import numpy as np
from collections import deque
import json
import hashlib
import time

class SteeringController:
    def __init__(self):
        self.target_latency_dist = np.random.normal(20, 5, 1000)
        self.current_latencies = deque(maxlen=500)
        self.energies = []
        self.latencies = []
        self.divergence_history = []
        self.pareto_frontier = []
        self._force_t3 = False

    def wasserstein_distance(self, p, q):
        """Compute 1D Wasserstein distance (Earth Mover's Distance)."""
        p_sorted = np.sort(p)
        q_sorted = np.sort(q)
        # Interpolate to same length
        min_len = min(len(p_sorted), len(q_sorted))
        if min_len < 2:
            return 0.0
        p_interp = np.interp(np.linspace(0, 1, min_len), 
                              np.linspace(0, 1, len(p_sorted)), p_sorted)
        q_interp = np.interp(np.linspace(0, 1, min_len), 
                              np.linspace(0, 1, len(q_sorted)), q_sorted)
        return float(np.mean(np.abs(p_interp - q_interp)))

    def update(self, latency: float, energy: float):
        self.current_latencies.append(latency)
        self.energies.append(energy)
        self.latencies.append(latency)

        # Update Pareto frontier (dominated solutions)
        self._update_pareto(latency, energy)

        if len(self.current_latencies) > 100:
            wd = self.wasserstein_distance(
                list(self.current_latencies), 
                self.target_latency_dist[:len(self.current_latencies)]
            )
            self.divergence_history.append(wd)
            
            if wd > 63.59:
                self._force_t3 = True
                print(f"[Steering] CRITICAL DIVERGENCE = {wd:.2f} → FORCING TIER-3 OFFLOAD")
            else:
                self._force_t3 = False

    def _update_pareto(self, latency, energy):
        """Maintain the Pareto frontier of non-dominated solutions."""
        point = (latency, energy)
        # Check if this point is dominated
        dominated = False
        for p_lat, p_eng in self.pareto_frontier:
            if p_lat <= latency and p_eng <= energy:
                dominated = True
                break
        if not dominated:
            # Remove any points this new point dominates
            self.pareto_frontier = [
                (l, e) for l, e in self.pareto_frontier
                if not (latency <= l and energy <= e)
            ]
            self.pareto_frontier.append(point)

    def should_force_t3(self) -> bool:
        return self._force_t3

    def state(self):
        return {
            "current_latencies": len(self.current_latencies),
            "pareto_points": len(self.pareto_frontier),
            "divergence": self.divergence_history[-1] if self.divergence_history else 0,
            "force_t3": self._force_t3,
        }
