"""
Event Spine v2 — Append-Only Domain-of-Domains Kernel
=======================================================
The manifold builds itself. Every change is an EVENT.
Every domain is a PROJECTION over the event log.
Never delete. Only add compensating events.
Postretrospective replay: reconstruct not only "where" but "why".
"""
from rqns.core.interfaces import Event, DomainProjection, QualiaMeasurement
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Any

class EventSpine:
    """The universal append-only log. The kernel. The spine."""
    def __init__(self, log_path: str = "data/event_spine.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.events: List[Event] = []
        self.projections: Dict[str, DomainProjection] = {}
        self._last_hash = "0" * 64
        self._load()

    def _load(self):
        """Replay the spine from disk."""
        if self.log_path.exists():
            with open(self.log_path) as f:
                for line in f:
                    try:
                        d = json.loads(line.strip())
                        event = Event(
                            event_id=d["event_id"],
                            event_type=d["event_type"],
                            domain=d["domain"],
                            timestamp=d["timestamp"],
                            data=d["data"],
                            prev_hash=d.get("prev_hash", "")
                        )
                        self.events.append(event)
                        self._last_hash = d.get("hash", self._last_hash)
                    except:
                        pass

    def append(self, event_type: str, domain: str, data: Dict[str, Any]) -> Event:
        """Append an event. Hash-chained. Immutable."""
        event = Event(
            event_id=hashlib.md5(f"{event_type}{domain}{time.time()}".encode()).hexdigest()[:12],
            event_type=event_type,
            domain=domain,
            timestamp=time.time(),
            data=data
        )
        event.prev_hash = self._last_hash
        
        # Hash chain
        event_json = json.dumps({
            "event_id": event.event_id,
            "event_type": event.event_type,
            "domain": event.domain,
            "timestamp": event.timestamp,
            "data": event.data,
            "prev_hash": event.prev_hash
        }, sort_keys=True)
        h = hashlib.sha256(event_json.encode()).hexdigest()
        
        # Persist
        entry = json.dumps({
            "event_id": event.event_id,
            "event_type": event.event_type,
            "domain": event.domain,
            "timestamp": event.timestamp,
            "data": event.data,
            "prev_hash": event.prev_hash,
            "hash": h
        })
        with open(self.log_path, "a") as f:
            f.write(entry + "\n")
        
        self._last_hash = h
        self.events.append(event)
        
        # Notify all projections
        for name, proj in self.projections.items():
            try:
                proj.apply(event)
            except:
                pass
        
        return event

    def subscribe(self, name: str, projection: DomainProjection):
        """Subscribe a domain projection to the spine."""
        self.projections[name] = projection

    def replay(self, domain: str = None) -> List[Event]:
        """Replay events for a domain. Postretrospective reconstruction."""
        if domain:
            return [e for e in self.events if e.domain == domain]
        return list(self.events)

    def qualia(self, domain: str, context: str, intensity: float, 
               tags: List[str] = None) -> QualiaMeasurement:
        """Record a qualia measurement. Quantized subjective impression."""
        q = QualiaMeasurement(
            measurement_id=hashlib.md5(f"{domain}{context}{time.time()}".encode()).hexdigest()[:12],
            time=time.time(),
            domain=domain,
            context=context,
            intensity=intensity,
            tags=tags or []
        )
        self.append("qualia", domain, {
            "measurement_id": q.measurement_id,
            "context": context,
            "intensity": intensity,
            "tags": tags or []
        })
        return q
