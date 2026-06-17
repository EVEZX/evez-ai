"""
Spine Adapter — bridges EVEZ-OS agent_bus events to evez-spine.
Every agent event becomes a hash-chained spine entry.
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional

SPINE_LIB = Path(__file__).parent.parent.parent / "evez-spine"
sys.path.insert(0, str(SPINE_LIB))
from spine import Spine, Domain, Status, SignalClass

EVENT_DOMAIN_MAP = {
    "FIRE_EVENT": Domain.COGNITION, "OODA_CYCLE": Domain.AGENT,
    "TASK_CREATED": Domain.AGENT, "TASK_COMPLETED": Domain.AGENT,
    "AGENT_SPAWNED": Domain.AGENT, "AGENT_DIED": Domain.AGENT,
    "ERROR": Domain.INFRA, "EVOLUTION": Domain.COGNITION,
    "REPAIR": Domain.INFRA, "EXPANSION": Domain.COGNITION,
    "MEMORY_CONSOLIDATION": Domain.CONSCIOUSNESS,
    "CROSS_REPO": Domain.AGENT, "HEARTBEAT": Domain.INFRA,
}
EVENT_SIGNAL_MAP = {
    "FIRE_EVENT": SignalClass.FIRE_EVENT,
    "EVOLUTION": SignalClass.EIGENVALUE,
    "ERROR": SignalClass.LOG_ONLY,
}

class SpineAdapter:
    def __init__(self, spine_path: Optional[str] = None):
        if spine_path and Path(spine_path).exists():
            self.spine = Spine.from_file(spine_path)
        else:
            self.spine = Spine(operator="evez-os", genesis_meta={
                "source": "agent_bus", "version": "1.0.0",
                "eigenvalue_threshold": -0.358,
            })
        self.spine_path = spine_path

    def ingest_event(self, event_type: str, payload: Dict[str, Any],
                     caused_by: Optional[str] = None) -> Dict:
        domain = EVENT_DOMAIN_MAP.get(event_type, Domain.AGENT)
        signal = EVENT_SIGNAL_MAP.get(event_type, SignalClass.LOG_ONLY)
        if event_type == "FIRE_EVENT" and "V_v2" in payload:
            return self.spine.log_fire_round(payload, caused_by=caused_by)
        if event_type == "OODA_CYCLE":
            return self.spine.log_agent_cycle("OODA", payload, caused_by=caused_by)
        return self.spine.log(event_type, payload, domain=domain.value,
                              confidence=0.9, signal_class=signal.value,
                              caused_by=caused_by, tags=[event_type.lower()])

    def save(self):
        if self.spine_path: self.spine.export(self.spine_path)
    def get_eigenvalue_status(self) -> Dict: return self.spine.eigenvalue_status()
    def get_fire_history(self) -> list: return self.spine.query(event_type="FIRE_ROUND", domain=Domain.COGNITION.value)
    def get_agent_history(self) -> list: return self.spine.query(domain=Domain.AGENT.value)
    def verify(self) -> tuple: return self.spine.verify_chain()

if __name__ == "__main__":
    a = SpineAdapter()
    a.ingest_event("FIRE_EVENT", {"N": 32, "V_v2": 1.620825, "V_global": 1.45457, "cv": 34, "H_norm": 0.8657})
    a.ingest_event("OODA_CYCLE", {"observe": 18, "orient": 5, "branch": "build", "act": "deployed"})
    a.ingest_event("AGENT_SPAWNED", {"agent_id": "research", "model": "MiniMax-M2.5"})
    a.ingest_event("HEARTBEAT", {"services": {"gateway": "UP"}})
    print(json.dumps(a.spine.stats(), indent=2, default=str))
    print(f"Chain: {a.verify()}")
