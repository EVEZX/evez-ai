from fastapi import APIRouter
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


class IsolationDecision(BaseModel):
    mode: str
    actions: List[str]
    principles: List[str]


class IsolationEvent(BaseModel):
    event_id: str
    source: str
    severity: str
    description: str
    decision: IsolationDecision
    received_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}


# in-memory store stub; swap for Postgres later
ISOLATION_EVENTS: Dict[str, IsolationEvent] = {}


@router.post("/isolation")
async def ingest_isolation(event: IsolationEvent):
    ISOLATION_EVENTS[event.event_id] = event
    # later: append to spine, write to Postgres, trigger views
    return {"status": "accepted", "event_id": event.event_id}


@router.get("/isolation/{event_id}")
async def get_isolation(event_id: str) -> Optional[IsolationEvent]:
    return ISOLATION_EVENTS.get(event_id)
