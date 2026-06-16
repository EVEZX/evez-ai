"""Patch Pipeline — Hot-swapping learning feedback"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rqns.core.interfaces import PatchPipeline, QuantumResult, PatchApplicationLog
from rqns.modules.rqns_agent import ContextualBanditAgent
import uuid, numpy as np

class ConcretePatchPipeline(PatchPipeline):
    def __init__(self, rqns_agent):
        self.agent = rqns_agent
        self.cumulative_learning = 0.0
        self.history = []

    def process_solver_result(self, result):
        applied = result.success and result.backend != "LOCAL_RESOLVE"
        delta = 0.05 if applied else -0.02
        self.cumulative_learning += delta
        self.history.append((result.solution_energy, result.latency_ms, applied))
        if len(self.history) > 50:
            self.history.pop(0)

        if abs(self.cumulative_learning - round(self.cumulative_learning)) < 0.01:
            self._trigger_recalibration()

        return PatchApplicationLog(
            patch_id=str(uuid.uuid4())[:8],
            applied=applied,
            cumulative_learning=self.cumulative_learning,
            learning_delta=delta,
            rollback_enabled=True
        )

    def _trigger_recalibration(self):
        recent = self.history[-20:]
        if not recent: return
        success_rate = sum(1 for _, _, a in recent if a) / len(recent)
        shift = (success_rate - 0.7) * 5.0
        new_thresholds = {k: max(15.0, v + shift) for k, v in self.agent.delegation_thresholds.items()}
        self.agent.hot_swap_thresholds(new_thresholds)
