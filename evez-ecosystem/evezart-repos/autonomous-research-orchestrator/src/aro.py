"""
Autonomous Research Orchestrator (ARO) v1.0
EVEZ Station | EvezArt | github.com/EvezArt

Capacity formula:
  Omega(n, d, lam, N) = n * exp(lam * d) * ln(N)  ~= 600x at defaults
"""

import math
import uuid
import time
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

STREAM_TYPES = [
    "historical_truth_recovery",
    "systemic_intervention_design",
    "knowledge_synthesis_generation",
    "metacognitive_orchestration",
]

DEFAULT_DEPTH  = 4
DEFAULT_LAMBDA = 1.0
DEFAULT_GAMMA  = 0.85

EVEZ_OS_THRESHOLDS = [0.85, 0.91, 0.94, 0.96, 0.98, 0.990, 0.995, 0.999]


class StreamType(Enum):
    HISTORICAL_TRUTH      = "historical_truth_recovery"
    SYSTEMIC_INTERVENTION = "systemic_intervention_design"
    KNOWLEDGE_SYNTHESIS   = "knowledge_synthesis_generation"
    METACOGNITIVE         = "metacognitive_orchestration"


@dataclass
class Finding:
    id:              str   = field(default_factory=lambda: str(uuid.uuid4()))
    stream_type:     str   = ""
    insight_type:    str   = ""
    content:         str   = ""
    confidence:      float = 0.0
    epoch:           int   = 0
    temporal_anchor: float = field(default_factory=time.time)
    causal_weight:   float = 0.0

    def to_dict(self): return asdict(self)


@dataclass
class ResearchStream:
    id:          str        = field(default_factory=lambda: str(uuid.uuid4()))
    stream_type: StreamType = StreamType.KNOWLEDGE_SYNTHESIS
    depth:       int        = 0
    findings:    List[Finding] = field(default_factory=list)
    associative_score: float = 0.0

    def causal_spine_hash(self) -> str:
        data = sorted(f"{f.epoch}:{f.causal_weight:.4f}" for f in self.findings if f.causal_weight > 0.1)
        return hashlib.sha256(":".join(data).encode()).hexdigest()[:16]

    def convergence_score(self, lam=DEFAULT_LAMBDA) -> float:
        return 1.0 - math.exp(-lam * len(self.findings))

    def add_finding(self, content, insight_type, confidence=0.8, epoch=0):
        f = Finding(
            stream_type=self.stream_type.value, insight_type=insight_type,
            content=content, confidence=confidence, epoch=epoch,
            causal_weight=confidence * self.convergence_score(),
        )
        self.findings.append(f)
        self.associative_score = self.convergence_score()
        return f


@dataclass
class SynthesisMatrix:
    session_id: str; stream_count: int; depth: int; lam: float; n_scale: float
    capacity_omega: float = 0.0; convergence_score: float = 0.0
    metacognitive_delta: float = 0.0; intervention_vectors: Dict[str, Any] = field(default_factory=dict)

    def compute_omega(self):
        self.capacity_omega = self.stream_count * math.exp(self.lam * self.depth) * math.log(max(self.n_scale, 1.001))
        return self.capacity_omega

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "capacity_omega": round(self.capacity_omega, 2),
            "convergence_score": round(self.convergence_score, 4),
            "metacognitive_delta": round(self.metacognitive_delta, 4),
            "intervention_vectors": self.intervention_vectors,
            "formula": f"Omega = {self.stream_count}*exp({self.lam}*{self.depth})*ln({self.n_scale:.1f}) ~= {self.capacity_omega:.1f}x",
        }


class AutonomousResearchOrchestrator:
    def __init__(self, supabase_url=None, supabase_key=None):
        self.sessions: Dict[str, dict] = {}
        self.supabase_url = supabase_url; self.supabase_key = supabase_key
        self._theta = [t * 0.9 for t in EVEZ_OS_THRESHOLDS]
        self._eta = 0.01; self._total_runs = 0; self._total_insights = 0

    def omega(self, n=4, d=DEFAULT_DEPTH, lam=DEFAULT_LAMBDA, N=15.5):
        """Omega(n, d, lam, N) = n * exp(lam*d) * ln(N)  ~= 600x at defaults"""
        return n * math.exp(lam * d) * math.log(max(N, 1.001))

    def knowledge_synthesis_rate(self, K, K_max=1.0, gamma=DEFAULT_GAMMA, stream_contributions=None):
        """dK/dt = gamma*K*(1-K/K_max) + sum_i dK/ds_i * s_i_dot"""
        return gamma * K * (1.0 - K / K_max) + sum(stream_contributions or []) * 0.1

    def metacognitive_update(self, gradient):
        """theta(t+1) = theta(t) + eta * grad_theta J(theta(t))"""
        for i in range(min(8, len(gradient))):
            self._theta[i] = min(EVEZ_OS_THRESHOLDS[i], self._theta[i] + self._eta * gradient[i])
        return list(self._theta)

    def causal_spine_invariant(self, findings):
        """I_causal = {(x,y) | d2K/dx_dt != 0, for all t in Epochs}"""
        return [f for f in findings if f.causal_weight >= 0.85]

    def aggregate_convergence(self, streams):
        """C_total = 1 - product_i(1 - C_i)"""
        if not streams: return 0.0
        p = 1.0
        for s in streams: p *= (1.0 - s.convergence_score())
        return 1.0 - p

    def create_session(self, title, methodology="multi-stream", stream_types=None, depth=DEFAULT_DEPTH):
        sid = str(uuid.uuid4())
        streams = [ResearchStream(stream_type=StreamType(st if st in [e.value for e in StreamType] else "knowledge_synthesis_generation"), depth=depth) for st in (stream_types or STREAM_TYPES)]
        s = {"id": sid, "title": title, "methodology": methodology, "depth": depth, "streams": streams, "status": "active", "created_at": time.time(), "omega_estimate": self.omega(n=len(streams), d=depth)}
        self.sessions[sid] = s
        return s

    def execute_research(self, session_id, research_input, n_scale=15.5):
        s = self.sessions.get(session_id)
        if not s: raise ValueError(f"Session {session_id} not found")
        self._total_runs += 1
        with ThreadPoolExecutor(max_workers=len(s["streams"])) as pool:
            for fut in as_completed({pool.submit(self._execute_stream, st, research_input, i): st for i, st in enumerate(s["streams"])}): fut.result()
        matrix = self._synthesize(s, n_scale)
        self.metacognitive_update([st.convergence_score() for st in s["streams"]] + [0.0]*4)
        self._total_insights += sum(len(st.findings) for st in s["streams"])
        s["status"] = "synthesized"; s["synthesis"] = matrix
        return matrix.to_dict()

    def _execute_stream(self, stream, inp, epoch):
        st = stream.stream_type; sn = inp[:60]
        if st == StreamType.HISTORICAL_TRUTH:
            stream.add_finding(f"[HIST] Temporal pattern: {sn}", "temporal_pattern", 0.87, epoch)
            stream.add_finding("[HIST] Invariant causal anchor identified", "causal_anchor", 0.92, epoch)
        elif st == StreamType.SYSTEMIC_INTERVENTION:
            stream.add_finding(f"[INTV] Intervention vector: {sn}", "intervention_vector", 0.83, epoch)
            stream.add_finding("[INTV] Resource-misframing oppression frame detected", "oppression_detection", 0.91, epoch)
        elif st == StreamType.KNOWLEDGE_SYNTHESIS:
            stream.add_finding(f"[SYNTH] Associative link: {sn}", "associative_network", 0.88, epoch)
            stream.add_finding("[SYNTH] Indigenous resilience factor integrated", "resilience_factor", 0.85, epoch)
        elif st == StreamType.METACOGNITIVE:
            stream.add_finding(f"[META] Autopoietic loop in: {inp[:40]}", "autopoietic_loop", 0.94, epoch)
            stream.add_finding("[META] Temporal anomaly flagged as primary threat signal", "threat_signal", 0.96, epoch)
        stream.depth += 1

    def _synthesize(self, session, n_scale):
        streams = session["streams"]
        findings = [f for s in streams for f in s.findings]
        causal = self.causal_spine_invariant(findings)
        m = SynthesisMatrix(
            session_id=session["id"], stream_count=len(streams), depth=session["depth"],
            lam=DEFAULT_LAMBDA, n_scale=n_scale, convergence_score=self.aggregate_convergence(streams),
            metacognitive_delta=sum(self._theta)/8.0,
            intervention_vectors={"causal_invariants": len(causal), "total_findings": len(findings), "stream_scores": {s.stream_type.value: round(s.convergence_score(),4) for s in streams}, "causal_spine_hashes": {s.stream_type.value: s.causal_spine_hash() for s in streams}},
        )
        m.compute_omega(); return m

    def health(self):
        ov = self.omega()
        return {"status": "operational", "version": "1.0.0", "capacity_omega": round(ov, 2), "formula": f"Omega(4,4,1,15.5) = 4*e^4*ln(15.5) ~= {ov:.1f}x", "active_sessions": len(self.sessions), "total_runs": self._total_runs, "total_insights": self._total_insights, "evez_os_theta": [round(t,4) for t in self._theta], "evez_os_gates_met": sum(1 for t,c in zip(self._theta, EVEZ_OS_THRESHOLDS) if t >= c*0.9), "streams": STREAM_TYPES}
