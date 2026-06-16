"""RQNS Orchestrator — Full pipeline: Sensor → Agent → Solver → Patch → Steering"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rqns.core.interfaces import RQNSPipeline, AnomalySignal
from rqns.modules.sensor_agent import ConcreteSensorAgent
from rqns.modules.rqns_agent import ContextualBanditAgent
from rqns.modules.solver_client import ConcreteSolverClient
from rqns.modules.patch_pipeline import ConcretePatchPipeline
from rqns.steering_controller import SteeringController

class ConcreteRQNSPipeline(RQNSPipeline):
    def __init__(self):
        self.sensor = ConcreteSensorAgent()
        self.agent = ContextualBanditAgent()
        self.solver = ConcreteSolverClient()
        self.patcher = ConcretePatchPipeline(self.agent)
        self.steering = SteeringController()

    def process_signal(self, signal):
        detection = self.sensor.process_signal(signal)
        job, decision = self.agent.analyze_anomaly(detection)

        if decision.route_to_t3:
            result = self.solver.solve(job)
            patch_log = self.patcher.process_solver_result(result)
            energy = result.solution_energy
            latency = result.latency_ms
            # Update agent with reward
            reward = -latency / 1000.0 - abs(energy) * 0.01
            self.agent.update(job.state, job.action, reward)
        else:
            energy = -detection.complexity * 0.3
            latency = decision.estimated_latency
            patch_log = None

        steer = self.steering.update(latency, energy)

        return {
            "signal_id": signal.source_id,
            "complexity": detection.complexity,
            "confidence": detection.confidence,
            "is_anomaly": detection.is_anomaly,
            "backend": decision.backend.value,
            "route_to_t3": decision.route_to_t3,
            "latency_ms": latency,
            "energy": energy,
            "learning": self.patcher.cumulative_learning,
            "wasserstein": steer.get('wasserstein', 0),
            "force_offload": steer.get('force_offload', False)
        }
