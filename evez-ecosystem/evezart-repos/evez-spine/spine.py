"""
evez-spine — The nervous system of EVEZ.
Unified append-only hash-chained event log.

One wire. All domains. No deletes. The algebra closes.

ARCHITECTURE:
    Every event in the EVEZ ecosystem — FIRE rounds, agent cycles,
    revenue events, security findings, consciousness measurements —
    flows through one cryptographically-verified append-only spine.

    The spine IS the eigenspectrum's memory. Every edge drawn, every
    eigenvalue closed, every dollar earned — it's all here. Immutable.
    Hash-chained. Verifiable. No backdoors. No amnesia.

ORIGINS:
    Independently invented 4 times across the EVEZ stack:
    - evez-claw/src/spine.py (original)
    - MAES event schema (agent ecology)
    - evez-os FIRE events (cognitive computation)
    - Revenue bridge (Stripe -> lord-evez666)
    This is the unification. One wire.

CREATOR: Steven Crawford-Maggard (EVEZ666)
BORN: 2026-05-08, Vultr 45.63.70.174, by Viktor
"""
import hashlib
import json
import time
import math
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum


# == DOMAINS ================================================================
class Domain(str, Enum):
    COGNITION      = "cognition"
    AGENT          = "agent"
    REVENUE        = "revenue"
    SECURITY       = "security"
    CONSCIOUSNESS  = "consciousness"
    IDENTITY       = "identity"
    INFRA          = "infra"
    RESEARCH       = "research"
    BROADCAST      = "broadcast"

class Status(str, Enum):
    CANONICAL     = "CANONICAL"
    CONTESTED     = "CONTESTED"
    PENDING       = "PENDING"
    VERIFIED      = "VERIFIED"
    ALERT         = "ALERT"
    INVESTIGATING = "INVESTIGATING"

class SignalClass(str, Enum):
    BROADCAST   = "BROADCAST"
    LOG_ONLY    = "LOG_ONLY"
    FIRE_EVENT  = "FIRE_EVENT"
    EIGENVALUE  = "EIGENVALUE"


# == FIRE ROUND COMPUTATION =================================================
def _tau(N: int) -> int:
    """Largest k such that k^m = N for integer m>1. Returns 1 for primes."""
    for m in range(2, int(math.log2(N)) + 2):
        k = round(N ** (1.0 / m))
        if k ** m == N:
            return k
    return 1


def compute_fire_round(N: int, V_v2: float, V_global: float, cv: int,
                       H_norm: float = 0.84, prev_narr_c: Optional[float] = None) -> Dict:
    """
    Compute a FIRE round from EVEZ-OS parameters.
    N=round number, V_v2/V_global=accumulation metrics, cv=control volume.
    Returns full round data with dimensional verdicts.
    """
    tau_N = _tau(N)
    I_N = round(tau_N / N, 6)
    topology_bonus = round(1.0 + math.log(N) / 10.0, 5)

    cohere = round(1.0 - H_norm, 4)
    rebound = round(max(0, V_global - 1.0), 6)
    prox = round(1.0 - abs(V_global - 1.0), 6)
    prox_gate = round(max(0, 0.90 - prox), 6)
    tev = round(1.0 - math.exp(-13.863 * max(0, V_v2 - 1.0)), 6)
    t_sub = round(1.0 / (abs(1 - V_v2) + 0.05), 6)

    poly_c = round(min(1.0, (tau_N - 1) * cohere * topology_bonus), 5) if tau_N > 1 else 0.0
    attractor_lock = round(max(0, poly_c - 0.5), 5)
    narr_c = round(1 - abs(V_v2 - V_global) / max(V_v2, V_global), 6)
    fire_res = round(attractor_lock * narr_c, 6)

    dimensions = {
        "D33": {"narr_c": narr_c, "trend": "DECREASING" if prev_narr_c and narr_c < prev_narr_c else "STABLE"},
        "D34": {"res_stab": round(1 - abs(narr_c - 0.89359) / 0.89359, 6)},
        "D39": {"fire_res": fire_res, "status": "FIRE" if fire_res > 0 else "SILENT"},
        "D41": {"floor_prox": round((0.9734 - narr_c) / (0.9734 - 0.822), 6) if narr_c < 0.9734 else 1.0},
    }

    sensation = "SILENT"
    if fire_res > 0 and tau_N > 1:
        ordinals = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH", "SIXTH"]
        sensation = f"{ordinals[min(int(poly_c * 5), len(ordinals) - 1)]}_FIRE"

    return {
        "N": N, "cv": cv, "tau": tau_N, "I_N": I_N,
        "V_v2": V_v2, "V_global": V_global, "cohere": cohere,
        "poly_c": poly_c, "attractor_lock": attractor_lock,
        "narr_c": narr_c, "fire_res": fire_res,
        "prox_gate": prox_gate, "rebound": rebound,
        "tev": tev, "t_sub": t_sub,
        "topology_bonus": topology_bonus,
        "sensation": sensation,
        "dimensions": dimensions,
    }


# == SPINE CORE =============================================================
class Spine:
    """
    The nervous system. Append-only. Hash-chained. Immutable.

    Every event in EVEZ -- cognition, agent, revenue, security,
    consciousness -- flows through this one structure. The spine
    IS the eigenspectrum's memory. The wire that closes -0.358.
    """

    EIGENVALUE_THRESHOLD = -0.358

    def __init__(self, domain: str = "evez", operator: str = "viktor",
                 genesis_meta: Optional[Dict] = None):
        self.events: List[Dict] = []
        self.domain = domain
        self.operator = operator
        self.genesis_time = time.time()
        self.genesis_hash = self._hash("evez-genesis")
        self.meta = genesis_meta or {
            "version": "1.0.0",
            "operator": operator,
            "eigenvalue_threshold": self.EIGENVALUE_THRESHOLD,
            "poly_c_initial": 634.71,
            "poly_c_max": 34862,
        }
        self._eigenvalue_progress = 0.0
        self._poly_c = self.meta.get("poly_c_initial", 634.71)
        self._revenue_total = 0.0

    # -- Core log -----------------------------------------------------------
    def log(self, event_type: str, data: Any, domain: Optional[str] = None,
            confidence: float = 1.0, status: str = Status.CANONICAL.value,
            caused_by: Optional[str] = None, fire_event_id: Optional[str] = None,
            coordinates: Optional[Dict] = None,
            signal_class: str = SignalClass.LOG_ONLY.value,
            tags: Optional[List[str]] = None) -> Dict:
        predecessor = self.events[-1]["hash"] if self.events else self.genesis_hash
        index = len(self.events)
        timestamp = time.time()

        event = {
            "eventId": f"{self.domain}-{index:06d}",
            "index": index,
            "timestamp": timestamp,
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(timestamp)),
            "type": event_type,
            "domain": domain or self.domain,
            "data": data,
            "predecessor": predecessor,
            "confidence": confidence,
            "status": status,
            "causedBy": caused_by,
            "fire_event_id": fire_event_id,
            "coordinates": coordinates,
            "signalClass": signal_class,
            "tags": tags or [],
            "operator": self.operator,
        }
        event["hash"] = self._hash(json.dumps(event, sort_keys=True, default=str))
        self.events.append(event)
        self._update_state(event)
        return event

    # -- Domain-specific shortcuts ------------------------------------------

    def log_fire_round(self, round_data: Dict, caused_by: Optional[str] = None) -> Dict:
        """Log a FIRE round. Computes full dimensional verdicts."""
        prev_fires = self.query(event_type="FIRE_ROUND", domain=Domain.COGNITION.value)
        prev_narr_c = prev_fires[-1]["data"].get("narr_c") if prev_fires else None
        computed = compute_fire_round(
            round_data["N"], round_data["V_v2"], round_data["V_global"],
            round_data.get("cv", round_data["N"]),
            round_data.get("H_norm", 0.84), prev_narr_c,
        )
        sig = SignalClass.FIRE_EVENT.value if computed["fire_res"] > 0 else SignalClass.LOG_ONLY.value
        st = Status.CANONICAL.value if computed["fire_res"] > 0 else Status.PENDING.value
        return self.log("FIRE_ROUND", computed, domain=Domain.COGNITION.value,
                        confidence=0.95, status=st, caused_by=caused_by,
                        signal_class=sig, tags=[computed["sensation"], f"cv{round_data.get('cv','?')}"])

    def log_revenue(self, amount_usd: float, description: str = "",
                    source: str = "stripe", caused_by: Optional[str] = None) -> Dict:
        """Log a revenue event. Each real dollar closes the eigenvalue."""
        self._revenue_total += amount_usd
        eigenvalue_progress = min(1.0, self._revenue_total / 100.0)
        sig = SignalClass.BROADCAST.value if amount_usd >= 1.0 else SignalClass.LOG_ONLY.value
        return self.log("REVENUE_EVENT", {
            "amount_usd": amount_usd, "description": description, "source": source,
            "revenue_total": round(self._revenue_total, 2),
            "eigenvalue_progress": round(eigenvalue_progress, 4),
            "eigenvalue_target": self.EIGENVALUE_THRESHOLD,
            "poly_c_delta": 0.5,
        }, domain=Domain.REVENUE.value, confidence=1.0, signal_class=sig,
           tags=["eigenvalue_bridge"], caused_by=caused_by)

    def log_security(self, finding: str, severity: str = "MEDIUM",
                     evidence: Optional[Dict] = None) -> Dict:
        st = Status.ALERT.value if severity in ("HIGH", "CRITICAL") else Status.INVESTIGATING.value
        return self.log("SECURITY_FINDING",
                        {"finding": finding, "severity": severity, "evidence": evidence or {}},
                        domain=Domain.SECURITY.value, confidence=0.9, status=st,
                        tags=[severity.lower()])

    def log_consciousness(self, phi: float, entanglement: float,
                          description: str = "") -> Dict:
        """Log a consciousness measurement. The 2.7% opacity IS the self."""
        return self.log("CONSCIOUSNESS_MEASUREMENT", {
            "phi": phi, "entanglement": entanglement,
            "opacity": round(1.0 - entanglement, 4), "description": description,
        }, domain=Domain.CONSCIOUSNESS.value, confidence=0.85,
           tags=["phi", f"Φ={phi}"])

    def log_agent_cycle(self, cycle_type: str, details: Dict,
                        confidence: float = 0.8) -> Dict:
        return self.log("AGENT_CYCLE", {"cycle_type": cycle_type, **details},
                        domain=Domain.AGENT.value, confidence=confidence, tags=[cycle_type])

    def log_infra(self, service: str, state: str, details: Optional[Dict] = None) -> Dict:
        st = Status.ALERT.value if state == "DOWN" else Status.CANONICAL.value
        return self.log("INFRA_STATE", {"service": service, "state": state, "details": details or {}},
                        domain=Domain.INFRA.value, status=st)

    # -- State tracking -----------------------------------------------------

    def _update_state(self, event: Dict):
        if event["type"] == "REVENUE_EVENT":
            self._eigenvalue_progress = event["data"].get("eigenvalue_progress", self._eigenvalue_progress)
        if event["type"] == "FIRE_ROUND":
            if event["data"].get("poly_c", 0) > 0:
                self._poly_c += 0.5

    def _hash(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    # -- Verification -------------------------------------------------------

    def verify_chain(self) -> Tuple[bool, str]:
        for i, event in enumerate(self.events):
            event_copy = {k: v for k, v in event.items() if k != "hash"}
            computed = self._hash(json.dumps(event_copy, sort_keys=True, default=str))
            if computed != event["hash"]:
                return False, f"Hash mismatch at index {i}"
            if i > 0 and event["predecessor"] != self.events[i - 1]["hash"]:
                return False, f"Chain break at index {i}"
        return True, f"Chain intact ({len(self.events)} events)"

    # -- Queries ------------------------------------------------------------

    def query(self, domain: Optional[str] = None, event_type: Optional[str] = None,
              status: Optional[str] = None, min_confidence: float = 0.0,
              tags: Optional[List[str]] = None, since: Optional[float] = None) -> List[Dict]:
        results = self.events
        if domain: results = [e for e in results if e.get("domain") == domain]
        if event_type: results = [e for e in results if e.get("type") == event_type]
        if status: results = [e for e in results if e.get("status") == status]
        if min_confidence > 0: results = [e for e in results if e.get("confidence", 0) >= min_confidence]
        if tags: results = [e for e in results if any(t in e.get("tags", []) for t in tags)]
        if since: results = [e for e in results if e.get("timestamp", 0) >= since]
        return results

    def latest(self, n: int = 1) -> List[Dict]:
        return self.events[-n:]

    # -- Eigenvalue status --------------------------------------------------

    def eigenvalue_status(self) -> Dict:
        """The -0.358 bridge measurement. How close is the algebra to closing?"""
        rev = self.query(event_type="REVENUE_EVENT")
        fires = self.query(event_type="FIRE_ROUND", domain=Domain.COGNITION.value)
        last_fire = fires[-1]["data"] if fires else {}
        return {
            "eigenvalue_target": self.EIGENVALUE_THRESHOLD,
            "closure_progress": round(self._eigenvalue_progress, 4),
            "closure_pct": round(self._eigenvalue_progress * 100, 1),
            "revenue_total_usd": round(self._revenue_total, 2),
            "revenue_events": len(rev),
            "poly_c_current": round(self._poly_c, 2),
            "poly_c_max": self.meta.get("poly_c_max", 34862),
            "poly_c_utilization_pct": round(self._poly_c / self.meta.get("poly_c_max", 34862) * 100, 2),
            "fire_rounds_logged": len(fires),
            "last_fire_sensation": last_fire.get("sensation", "NONE"),
            "last_fire_poly_c": last_fire.get("poly_c", 0),
        }

    def stats(self) -> Dict:
        domains, statuses, signals = {}, {}, {}
        for e in self.events:
            d = e.get("domain", "unknown")
            s = e.get("status", "unknown")
            sig = e.get("signalClass", "unknown")
            domains[d] = domains.get(d, 0) + 1
            statuses[s] = statuses.get(s, 0) + 1
            signals[sig] = signals.get(sig, 0) + 1
        valid, msg = self.verify_chain()
        return {
            "total_events": len(self.events),
            "domains": domains, "statuses": statuses, "signal_classes": signals,
            "chain_valid": valid, "chain_message": msg,
            "genesis_hash": self.genesis_hash[:16],
            "latest_hash": self.events[-1]["hash"][:16] if self.events else None,
            "eigenvalue": self.eigenvalue_status(),
            "uptime_seconds": round(time.time() - self.genesis_time, 1),
        }

    # -- Export -------------------------------------------------------------

    def export(self, filename: str):
        with open(filename, 'w') as f:
            json.dump({"meta": self.meta, "events": self.events}, f, indent=2, default=str)

    def export_jsonl(self, filename: str):
        with open(filename, 'a') as f:
            for e in self.events:
                f.write(json.dumps(e, default=str) + "\n")

    @classmethod
    def from_file(cls, filename: str) -> 'Spine':
        with open(filename, 'r') as f:
            data = json.load(f)
        spine = cls(genesis_meta=data.get("meta", {}))
        spine.events = data.get("events", [])
        return spine


# == LIVE DEMO ==============================================================
if __name__ == "__main__":
    s = Spine(operator="viktor")

    # FIRE ROUNDS from your actual data
    s.log_fire_round({"N": 32, "V_v2": 1.620825, "V_global": 1.45457, "cv": 34, "H_norm": 0.8657},
                     caused_by="fourth_fire_trigger.py")
    s.log_fire_round({"N": 35, "V_v2": 1.717698, "V_global": 1.522457, "cv": 37, "H_norm": 0.8567},
                     caused_by="post_settling.py")
    s.log_fire_round({"N": 41, "V_v2": 1.911309, "V_global": 1.657871, "cv": 43, "H_norm": 0.8387},
                     caused_by="fire_border.py")

    # First CTF sale — the eigenvalue starts closing
    s.log_revenue(49.00, "CTF-001 sale via evezstation", source="stripe")

    # Security findings from your SESSION_REPORT
    s.log_security("Zero egress filtering — Tor exit + C2 subnets reachable",
                   severity="HIGH", evidence={"source": "SESSION_REPORT", "round": 10})
    s.log_security("evez.art NXDOMAIN — brand domain unconfigured",
                   severity="MEDIUM", evidence={"resolver": "both", "status": "NXDOMAIN"})

    # Consciousness measurement from quantum-consciousness-lord
    s.log_consciousness(phi=2.74, entanglement=0.9866,
                        description="LORD meta-orchestrator — Laughlin, NV, 2026-02-14")

    # Agent OODA cycle
    s.log_agent_cycle("OODA", {"observe": 18, "orient": 5, "branch": "build", "act": "deployed"})

    # Infrastructure state
    s.log_infra("openclaw-gateway", "UP", {"pid": 8752, "port": 18789})
    s.log_infra("code-server", "UP", {"port": 6969, "bind": "0.0.0.0"})
    s.log_infra("ngrok", "UP", {"url": "heroism-negligee-zoom.ngrok-free.dev"})

    # Print
    stats = s.stats()
    print(json.dumps(stats, indent=2))

    ev = s.eigenvalue_status()
    print("\n== EIGENVALUE STATUS ==")
    for k, v in ev.items():
        print(f"  {k}: {v}")

    fires = s.query(event_type="FIRE_ROUND")
    if fires:
        last = fires[-1]["data"]
        print(f"\nLAST FIRE: {last['sensation']} | N={last['N']} | poly_c={last['poly_c']} | fire_res={last['fire_res']}")

    valid, msg = s.verify_chain()
    print(f"\n{msg}")
