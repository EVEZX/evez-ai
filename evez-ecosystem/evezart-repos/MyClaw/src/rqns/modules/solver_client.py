"""
Solver Client v2 — Quantum Backend Router
============================================
Maps anomaly features to QUBO for D-Wave annealing.
Other backends get mock results until real hardware is provisioned.
When Oracle ARM arrives (24GB free), local QUBO solving becomes possible.
"""
from rqns.core.interfaces import RQNSJob, QuantumResult, BackendType
import numpy as np

class ConcreteSolverClient:
    def __init__(self):
        self.solve_count = 0

    def _map_to_qubo(self, features: dict) -> np.ndarray:
        spike_count = features.get("spike_count", 10)
        complexity = features.get("complexity", 25.0)
        n_vars = min(50, int(complexity * 1.2))

        # QUBO: minimize anomaly severity with spike clustering penalty
        Q = np.zeros((n_vars, n_vars))
        for i in range(n_vars):
            Q[i, i] = -1.0 + 0.05 * i
        for i in range(n_vars):
            for j in range(i+1, min(i+5, n_vars)):
                Q[i, j] = 0.8 if (i % 7 < 3) else -0.3
        return Q

    def solve(self, job: RQNSJob) -> QuantumResult:
        self.solve_count += 1
        
        if job.allocation.backend == BackendType.ANNEALING_DWAVE:
            # Simulate D-Wave annealing (real integration needs dwave-system)
            Q = self._map_to_qubo(job.detection.features)
            n = Q.shape[0]
            # Simple simulated annealing as placeholder
            samples = np.random.randint(0, 2, (100, n))
            energies = [x @ Q @ x for x in samples]
            best_idx = np.argmin(energies)
            energy = energies[best_idx]
            latency = 123000 + np.random.exponential(20000)
            success = True
        elif job.allocation.backend == BackendType.QUANTUM_IONQ:
            # Simulate IonQ gate-model execution
            energy = -job.detection.complexity * 1.8 + np.random.normal(0, 2)
            latency = 6450 + np.random.exponential(1000)
            success = True
        elif job.allocation.backend == BackendType.HYBRID_HPC:
            # Simulate HPC hybrid
            energy = -job.detection.complexity * 1.5 + np.random.normal(0, 5)
            latency = 28250 + np.random.exponential(5000)
            success = np.random.rand() > 0.05  # 95% success rate
        else:
            # Local resolve
            energy = -job.detection.complexity * 1.2
            latency = job.allocation.estimated_latency * 1000
            success = True

        return QuantumResult(
            job_id=job.job_id,
            success=success,
            backend=job.allocation.backend.value,
            solution_energy=float(energy),
            latency_ms=float(latency / 1000)
        )
