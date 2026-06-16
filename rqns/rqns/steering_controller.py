"""Steering Controller — Wasserstein distance + live Pareto frontier"""
import numpy as np
from collections import deque
import json

class SteeringController:
    def __init__(self):
        self.target_latency_dist = np.random.normal(20, 5, 1000)
        self.current_latencies = deque(maxlen=500)
        self.energies = []
        self.latencies = []
        self.divergence_log = []

    def update(self, latency, energy):
        self.current_latencies.append(latency)
        self.energies.append(energy)
        self.latencies.append(latency)

        wd = 0.0
        force_offload = False
        if len(self.current_latencies) > 20:
            from scipy.stats import wasserstein_distance
            wd = wasserstein_distance(list(self.current_latencies), self.target_latency_dist[:len(self.current_latencies)])
            self.divergence_log.append(wd)
            if wd > 63.59:
                force_offload = True

        return {'wasserstein': wd, 'force_offload': force_offload}

    def get_pareto_data(self):
        return list(zip(self.latencies, self.energies))
