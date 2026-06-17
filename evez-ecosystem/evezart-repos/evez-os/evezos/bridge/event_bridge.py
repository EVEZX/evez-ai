"""
evezos/bridge/event_bridge.py

EventBridge: the closed loop.

Event flow (full income flywheel):
  1. agentnet:  AgentMemory.write()  → emit(AGENT_MEMORY_WRITE)
  2. spine:     FireEngine.run()      → emit(FIRE_CYCLE)
  3. cognition: CognitionLayer.compute() → emit(COGNITION_STATE)
  4. meme-bus:  MemeBus.publish()    → emit(MEME_PUBLISHED)
  5. income:    IncomeSignal.record() → emit(INCOME_SIGNAL)
  6. loop:      INCOME_SIGNAL → MetaLearner.reweight() → next FIRE

No external dependencies. FastAPI router included (optional).
"""

import json
import time
import uuid
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path


class EventType(str, Enum):
    AGENT_MEMORY_WRITE = "AGENT_MEMORY_WRITE"
    FIRE_CYCLE         = "FIRE_CYCLE"
    COGNITION_STATE    = "COGNITION_STATE"
    MEME_PUBLISHED     = "MEME_PUBLISHED"
    INCOME_SIGNAL      = "INCOME_SIGNAL"
    SPINE_COMMIT       = "SPINE_COMMIT"
    TWEET_TOKEN        = "TWEET_TOKEN"
    STATE_ADVANCE      = "STATE_ADVANCE"
    TICK_COMPLETE      = "TICK_COMPLETE"
    MROM_LOADED        = "MROM_LOADED"
    MROM_COMPLETED     = "MROM_COMPLETED"
    CUSTOM             = "CUSTOM"


@dataclass
class BridgeEvent:
    event_type: EventType
    source:     str
    payload:    Dict[str, Any] = field(default_factory=dict)
    event_id:   str  = field(default_factory=lambda: str(uuid.uuid4()))
    ts:         float = field(default_factory=time.time)
    routed_to:  List[str] = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["event_type"] = self.event_type.value
        return d

    def to_json(self): return json.dumps(self.to_dict())


class EventBridge:
    """
    EVEZ-OS event bus. Subscribe handlers, emit events, persist to JSONL.

    Quick start:
        bridge = EventBridge(log_path="evez_events.jsonl")

        @bridge.on(EventType.FIRE_CYCLE)
        def on_fire(event):
            print(f"FIRE ordinal={event.payload['ordinal']}")

        bridge.emit(EventType.FIRE_CYCLE, source="fire_engine",
                    payload=cycle.to_event())

    FastAPI:
        app.include_router(bridge.fastapi_router(), prefix="/api")
    """

    def __init__(self, log_path="evez_events.jsonl"):
        self.log_path  = Path(log_path)
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._history:  List[BridgeEvent] = []

    def on(self, event_type):
        def decorator(fn):
            self._handlers.setdefault(event_type, []).append(fn)
            return fn
        return decorator

    def subscribe(self, event_type, handler):
        self._handlers.setdefault(event_type, []).append(handler)

    def emit(self, event_type, source, payload=None):
        event = BridgeEvent(event_type=event_type, source=source, payload=payload or {})
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
                event.routed_to.append(handler.__name__)
            except Exception as exc:
                event.payload["_handler_error"] = str(exc)
        self._history.append(event)
        self._persist(event)
        return event

    def _persist(self, event):
        try:
            with open(self.log_path, "a") as f:
                f.write(event.to_json() + "\n")
        except OSError:
            pass

    def replay(self):
        if not self.log_path.exists(): return []
        events = []
        with open(self.log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try: events.append(json.loads(line))
                    except json.JSONDecodeError: pass
        return events

    def history(self, event_type=None):
        if event_type is None: return list(self._history)
        return [e for e in self._history if e.event_type == event_type]

    def fastapi_router(self):
        try:
            from fastapi import APIRouter
            from fastapi.responses import JSONResponse
            from pydantic import BaseModel
        except ImportError:
            raise ImportError("pip install fastapi uvicorn")

        router = APIRouter()

        class EventPayload(BaseModel):
            event_type: str
            source: str
            payload: dict = {}

        @router.post("/events")
        def post_event(body: EventPayload):
            try:    et = EventType(body.event_type)
            except: et = EventType.CUSTOM
            event = self.emit(et, source=body.source, payload=body.payload)
            return {"event_id": event.event_id, "routed_to": event.routed_to}

        @router.get("/events")
        def get_events(limit: int = 50):
            return JSONResponse(content={"events": self.replay()[-limit:]})

        return router


if __name__ == "__main__":
    bridge   = EventBridge(log_path="/tmp/evez_bridge_test.jsonl")
    received = []

    @bridge.on(EventType.FIRE_CYCLE)
    def on_fire(event): received.append(event)

    bridge.emit(EventType.FIRE_CYCLE, source="test",
                payload={"ordinal": 1, "fired": True, "V_exit": 0.42})
    assert len(received) == 1 and received[0].payload["fired"] is True
    print("EventBridge SELF-TEST PASSED")
