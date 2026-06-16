"""Solver Client — Routes to quantum backends (mock for now, real D-Wave when available)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rqns.core.interfaces import RQNSJob, QuantumResult, BackendType
import numpy as np

class ConcreteSolverClient:
    def solve(self, job):
        if job.allocation.backend == BackendType.ANNEALING_DWAVE:
            # Would use D-Wave here when dwave-system is installed
            energy = -job.detection.complexity * 1.8 + np.random.normal(0, 2)
            latency = 123000 + np.random.exponential(20000)
        elif job.allocation.backend == BackendType.QUANTUM_IONQ:
            energy = -job.detection.complexity * 2.1 + np.random.normal(0, 1.5)
            latency = 6450 + np.random.exponential(3000)
        elif job.allocation.backend == BackendType.HYBRID_HPC:
            energy = -job.detection.complexity * 1.5 + np.random.normal(0, 1)
            latency = 28250 + np.random.exponential(5000)
        else:
            energy = -job.detection.complexity * 0.8
            latency = job.allocation.estimated_latency * 1000

        return QuantumResult(
            job_id=job.job_id,
            success=True,
            backend=job.allocation.backend.value,
            solution_energy=energy,
            latency_ms=latency / 1000
        )
