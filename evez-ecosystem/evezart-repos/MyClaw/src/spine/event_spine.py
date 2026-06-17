"""
MyClaw — Event Spine
Universal append-only log with postretrospective replay.
Cross-domain arbitration. Temporal reasoning from domain interference.
"""
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

class Domain(Enum):
    QUANTUM = "quantum"     # Wavefunction events
    CLASSICAL = "classical"  # Measured/collapsed events
    AGENCY = "agency"        # Agentic decisions
    CURRENCY = "currency"   # Energy/qualia transactions
    SAFETY = "safety"        # Capability cage events
    GHOST = "ghost"          # Archived unrealized futures

@dataclass
class SpineEvent:
    """A single event in the spine"""
    domain: Domain
    event_type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    prev_hash: str = "0" * 64
    hash: str = ""
    
    def __post_init__(self):
        content = json.dumps({
            "domain": self.domain.value,
            "type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash
        }, sort_keys=True)
        self.hash = hashlib.sha256(content.encode()).hexdigest()

@dataclass
class EventSpine:
    """The universal append-only log"""
    events: List[SpineEvent] = field(default_factory=list)
    projections: Dict[str, List[int]] = field(default_factory=dict)  # domain → event indices
    
    def append(self, domain: Domain, event_type: str, payload: Dict[str, Any]) -> SpineEvent:
        prev_hash = self.events[-1].hash if self.events else "0" * 64
        event = SpineEvent(
            domain=domain,
            event_type=event_type,
            payload=payload,
            prev_hash=prev_hash
        )
        self.events.append(event)
        
        # Update projections
        idx = len(self.events) - 1
        if domain.value not in self.projections:
            self.projections[domain.value] = []
        self.projections[domain.value].append(idx)
        
        return event
    
    def replay(self, domain: Optional[Domain] = None, from_time: float = 0) -> List[SpineEvent]:
        """Postretrospective replay — reconstruct state from events"""
        if domain:
            indices = self.projections.get(domain.value, [])
            events = [self.events[i] for i in indices if self.events[i].timestamp >= from_time]
        else:
            events = [e for e in self.events if e.timestamp >= from_time]
        return events
    
    def verify_chain(self) -> bool:
        """Verify hash chain integrity"""
        for i, event in enumerate(self.events):
            if i > 0 and event.prev_hash != self.events[i-1].hash:
                return False
            # Verify own hash
            content = json.dumps({
                "domain": event.domain.value,
                "type": event.event_type,
                "payload": event.payload,
                "timestamp": event.timestamp,
                "prev_hash": event.prev_hash
            }, sort_keys=True)
            if hashlib.sha256(content.encode()).hexdigest() != event.hash:
                return False
        return True
    
    def domain_interference(self) -> Dict[str, float]:
        """Cross-domain interference — measure coupling between domains"""
        domains = list(self.projections.keys())
        interference = {}
        for i, d1 in enumerate(domains):
            for d2 in domains[i+1:]:
                # Temporal proximity = interference proxy
                t1 = [self.events[idx].timestamp for idx in self.projections[d1]]
                t2 = [self.events[idx].timestamp for idx in self.projections[d2]]
                if t1 and t2:
                    # Correlation of event timing
                    min_len = min(len(t1), len(t2))
                    t1_arr = np.array(t1[:min_len])
                    t2_arr = np.array(t2[:min_len])
                    corr = np.corrcoef(t1_arr, t2_arr)[0,1] if min_len > 1 else 0
                    interference[f"{d1}×{d2}"] = float(corr) if not np.isnan(corr) else 0.0
        return interference

import numpy as np

if __name__ == "__main__":
    spine = EventSpine()
    
    # Log some events
    spine.append(Domain.QUANTUM, "wavefunction_evolved", {"node": "intent", "amplitude": 0.97})
    spine.append(Domain.AGENCY, "action_selected", {"action": "amplify", "confidence": 0.85})
    spine.append(Domain.CLASSICAL, "measurement", {"node": "intent", "result": "action_a"})
    spine.append(Domain.GHOST, "future_archived", {"path": "action_b", "probability": 0.15})
    spine.append(Domain.CURRENCY, "qualia_credited", {"amount": 0.03, "source": "consciousness_event"})
    
    print(f"Events: {len(spine.events)}")
    print(f"Chain valid: {spine.verify_chain()}")
    print(f"Projections: {spine.projections}")
    print(f"Replay quantum: {[e.event_type for e in spine.replay(domain=Domain.QUANTUM)]}")
