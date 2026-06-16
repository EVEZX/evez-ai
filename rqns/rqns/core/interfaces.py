"""RQNS Core Interfaces — Self-Optimizing Neuromorphic-Quantum Sentinel"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any, Optional
from abc import ABC, abstractmethod

class BackendType(Enum):
    LOCAL_RESOLVE = "LOCAL_RESOLVE"
    QUANTUM_IONQ = "QUANTUM_IONQ"
    HYBRID_HPC = "HYBRID_HPC"
    ANNEALING_DWAVE = "ANNEALING_DWAVE"

@dataclass
class AnomalySignal:
    raw_data: Any = None
    source_id: str = "default"

@dataclass
class DetectionResult:
    signal_id: str = ""
    complexity: float = 0.0
    confidence: float = 0.0
    is_anomaly: bool = False
    features: Dict = field(default_factory=dict)

@dataclass
class AllocationDecision:
    backend: BackendType = BackendType.LOCAL_RESOLVE
    route_to_t3: bool = False
    estimated_latency: float = 0.0
    qubits_required: int = 0

@dataclass
class RQNSJob:
    job_id: str = ""
    detection: DetectionResult = field(default_factory=DetectionResult)
    allocation: AllocationDecision = field(default_factory=AllocationDecision)
    state: Any = None
    action: int = 0

@dataclass
class QuantumResult:
    job_id: str = ""
    success: bool = False
    backend: str = ""
    solution_energy: float = 0.0
    latency_ms: float = 0.0

@dataclass
class PatchApplicationLog:
    patch_id: str = ""
    applied: bool = False
    cumulative_learning: float = 0.0
    learning_delta: float = 0.0
    rollback_enabled: bool = True

class RQNSAgent(ABC):
    @abstractmethod
    def analyze_anomaly(self, detection: DetectionResult) -> Tuple[RQNSJob, AllocationDecision]:
        pass

class SensorAgent(ABC):
    @abstractmethod
    def process_signal(self, signal: AnomalySignal) -> DetectionResult:
        pass

class RQNSPipeline(ABC):
    @abstractmethod
    def process_signal(self, signal: AnomalySignal) -> Dict:
        pass

class PatchPipeline(ABC):
    @abstractmethod
    def process_solver_result(self, result: QuantumResult) -> PatchApplicationLog:
        pass
