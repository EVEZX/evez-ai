"""
RQNS v2 Core Interfaces — Domain-of-Domains Event-Sourced Kernel
================================================================
Every change is an EVENT. Every domain is a PROJECTION over the event log.
Never delete. Only append. The manifold builds itself.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import time

class BackendType(Enum):
    LOCAL_RESOLVE = "LOCAL_RESOLVE"
    QUANTUM_IONQ = "QUANTUM_IONQ"
    HYBRID_HPC = "HYBRID_HPC"
    ANNEALING_DWAVE = "ANNEALING_DWAVE"

@dataclass
class AnomalySignal:
    source_id: str = ""
    metric: str = ""
    value: float = 0.0
    threshold: float = 1.0
    timestamp: float = field(default_factory=time.time)
    raw_data: Any = None

@dataclass
class DetectionResult:
    signal_id: str = ""
    complexity: float = 0.0
    confidence: float = 0.0
    is_anomaly: bool = False
    features: Dict[str, Any] = field(default_factory=dict)

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

# ── Abstract bases ──────────────────────────────────────────
class SensorAgent(ABC):
    @abstractmethod
    def process_signal(self, signal: AnomalySignal) -> DetectionResult:
        ...

class RQNSAgent(ABC):
    @abstractmethod
    def analyze_anomaly(self, detection: DetectionResult):
        ...

class PatchPipeline(ABC):
    @abstractmethod
    def process_solver_result(self, result: QuantumResult) -> PatchApplicationLog:
        ...

class RQNSPipeline(ABC):
    @abstractmethod
    def process_signal(self, signal: AnomalySignal):
        ...

# ── Event Spine (append-only, the kernel) ───────────────────
@dataclass
class Event:
    event_id: str = ""
    event_type: str = ""
    domain: str = ""
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    prev_hash: str = ""

# ── Domain Projections ──────────────────────────────────────
class DomainProjection(ABC):
    """A projection over the event log. Each domain sees events its own way."""
    @abstractmethod
    def apply(self, event: Event):
        ...
    
    @abstractmethod
    def state(self) -> Dict[str, Any]:
        ...

# ── Qualia (quantized measurement events) ───────────────────
@dataclass
class QualiaMeasurement:
    measurement_id: str = ""
    time: float = 0.0
    domain: str = ""
    context: str = ""
    intensity: float = 0.0
    tags: List[str] = field(default_factory=list)

# ── DomainScript (meta-circular compute) ─────────────────────
@dataclass
class DomainScriptDefinition:
    script_id: str = ""
    name: str = ""
    code: str = ""
    version: int = 1
    author: str = "EVEZ-OS"
    created: float = field(default_factory=time.time)

# ── Safety ───────────────────────────────────────────────────
class CapabilityCage:
    """Hard safety envelope. Konami, but caged."""
    ALLOWED_PRIMITIVES = frozenset([
        "open_url", "click", "type", "submit", "scroll", 
        "summarize", "read", "measure", "append_event",
        "project", "grover_amplify", "tdse_step"
    ])
    
    def check(self, action: str) -> bool:
        return action in self.ALLOWED_PRIMITIVES

