"""RQNS Agent — Contextual Bandit with hot-swappable thresholds"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rqns.core.interfaces import (
    RQNSAgent, DetectionResult, RQNSJob, AllocationDecision, BackendType
)
from typing import Tuple, Dict
import numpy as np
import json
from pathlib import Path

class ContextualBanditAgent(RQNSAgent):
    def __init__(self):
        self.complexity_bins = np.linspace(10, 50, 41)
        self.confidence_bins = np.linspace(0, 1.5, 16)
        self.n_actions = 4
        self.Q = np.zeros((len(self.complexity_bins)-1, len(self.confidence_bins)-1, self.n_actions))
        self.counts = np.zeros_like(self.Q)
        self.epsilon = 0.1
        self.alpha = 0.1
        self.gamma = 0.99

        self.delegation_thresholds = {
            BackendType.LOCAL_RESOLVE: 22.0,
            BackendType.QUANTUM_IONQ: 28.6,
            BackendType.HYBRID_HPC: 30.0,
            BackendType.ANNEALING_DWAVE: float('inf')
        }

    def _discretize(self, complexity, confidence):
        c_bin = np.digitize([complexity], self.complexity_bins)[0] - 1
        f_bin = np.digitize([confidence], self.confidence_bins)[0] - 1
        c_bin = np.clip(c_bin, 0, len(self.complexity_bins)-2)
        f_bin = np.clip(f_bin, 0, len(self.confidence_bins)-2)
        return c_bin, f_bin

    def select_action(self, state):
        c_bin, f_bin = state
        if np.random.rand() < self.epsilon:
            return np.random.randint(self.n_actions)
        return int(np.argmax(self.Q[c_bin, f_bin]))

    def get_backend_from_action(self, action):
        return [BackendType.LOCAL_RESOLVE, BackendType.QUANTUM_IONQ,
                BackendType.HYBRID_HPC, BackendType.ANNEALING_DWAVE][action]

    def update(self, state, action, reward):
        c_bin, f_bin = state
        old_q = self.Q[c_bin, f_bin, action]
        self.Q[c_bin, f_bin, action] += self.alpha * (reward + self.gamma * np.max(self.Q[c_bin, f_bin]) - old_q)
        self.counts[c_bin, f_bin, action] += 1

    def analyze_anomaly(self, detection):
        c, conf = detection.complexity, detection.confidence
        state = self._discretize(c, conf)
        action_idx = self.select_action(state)
        backend = self.get_backend_from_action(action_idx)

        decision = AllocationDecision(
            backend=backend,
            route_to_t3=backend != BackendType.LOCAL_RESOLVE,
            estimated_latency=self._estimate_latency(backend, c),
            qubits_required=self._estimate_qubits(backend, c)
        )
        job = RQNSJob(job_id=str(np.random.randint(100000)), detection=detection, allocation=decision)
        job.state = state
        job.action = action_idx
        return job, decision

    def _estimate_latency(self, backend, complexity):
        mapping = {BackendType.LOCAL_RESOLVE: 3.15, BackendType.QUANTUM_IONQ: 6.45,
                    BackendType.HYBRID_HPC: 28.25, BackendType.ANNEALING_DWAVE: 123.25}
        base = mapping.get(backend, 50.0)
        return base * (1 + (complexity - 20) / 50)

    def _estimate_qubits(self, backend, complexity):
        if backend == BackendType.QUANTUM_IONQ: return int(18 + complexity * 0.8)
        if backend == BackendType.ANNEALING_DWAVE: return int(complexity * 1.5)
        return 0

    def hot_swap_thresholds(self, new_thresholds):
        self.delegation_thresholds.update(new_thresholds)
        print(f"[RQNS Agent] Hot-swapped thresholds → {new_thresholds}")
