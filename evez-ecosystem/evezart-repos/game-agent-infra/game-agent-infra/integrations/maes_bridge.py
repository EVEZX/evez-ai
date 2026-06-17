"""
MAES Bridge — Integrates EvezArt/maes with Game Agent Infra
Modular Agent Ecology System event sourcing for the autonomous runtime.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
import hashlib
import time


@dataclass
class MAESEvent:
    eventId: str
    streamId: str
    eventType: str
    domain: str
    timestamp_unix: float
    payload: Dict[str, Any]
    causedBy: str
    confidence: float
    status: str  # VERIFIED | PENDING | INVESTIGATING
    hash: str

    def compute_hash(self) -> str:
        data = f"{self.eventId}{self.streamId}{self.eventType}{self.timestamp_unix}{self.payload}"
        return hashlib.sha256(data.encode()).hexdigest()


class MAESBridge:
    """Bridges MAES event sourcing into the Game Agent Infra spine."""

    def __init__(self, spine):
        self.spine = spine
        self.events: List[MAESEvent] = []

    def create_event(
        self,
        stream_id: str,
        event_type: str,
        payload: Dict[str, Any],
        domain: str = "cognitive",
        confidence: float = 0.95,
        caused_by: str = "evezvearl-bot"
    ) -> MAESEvent:
        """Create a MAES-compliant event and append to spine."""

        event = MAESEvent(
            eventId=f"evt_{int(time.time()*1000)}",
            streamId=stream_id,
            eventType=event_type,
            domain=domain,
            timestamp_unix=time.time(),
            payload=payload,
            causedBy=caused_by,
            confidence=confidence,
            status="PENDING",
            hash=""
        )
        event.hash = event.compute_hash()

        # Append to Game Agent Infra spine with MAES metadata
        self.spine.append({
            "maes_event_id": event.eventId,
            "maes_stream_id": event.streamId,
            "maes_event_type": event.eventType,
            "maes_domain": event.domain,
            "maes_confidence": event.confidence,
            "maes_status": event.status,
            "payload": payload
        })

        self.events.append(event)
        return event

    def verify_event(self, event_id: str) -> bool:
        """Mark an event as VERIFIED after successful processing."""
        for ev in self.events:
            if ev.eventId == event_id:
                ev.status = "VERIFIED"
                return True
        return False

    def get_stream(self, stream_id: str) -> List[MAESEvent]:
        """Retrieve all events for a given stream."""
        return [e for e in self.events if e.streamId == stream_id]