"""
EVEZ Spine — Immutable append-only event log with SHA256 hash chaining.
Never rewrite. All changes via new events + projection rebuild.
"""

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import telemetry


@dataclass
class EventRecord:
    timestamp: float
    prev_hash: str
    payload: Dict[str, Any]
    hash: str = ""

    def compute_hash(self) -> str:
        data = f"{self.timestamp}{self.prev_hash}{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()


class AppendOnlySpine:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._events: List[EventRecord] = []
        self._load()

    def _load(self):
        if self.path.exists():
            with self.path.open() as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self._events.append(EventRecord(**data))

    def append(self, payload: Dict[str, Any]) -> EventRecord:
        prev_hash = self._events[-1].hash if self._events else "GENESIS"
        event = EventRecord(
            timestamp=time.time(),
            prev_hash=prev_hash,
            payload=payload,
        )
        event.hash = event.compute_hash()
        self._events.append(event)

        # OpenTelemetry hook
        telemetry.start_spine_append(
            agent_id=payload.get("agent_id", "unknown"),
            anomaly=payload.get("anomaly", "none"),
        )

        with self.path.open("a") as f:
            f.write(json.dumps(asdict(event)) + "\n")
        return event

    def verify_chain(self) -> bool:
        prev = "GENESIS"
        for ev in self._events:
            if ev.prev_hash != prev:
                return False
            if ev.hash != ev.compute_hash():
                return False
            prev = ev.hash
        return True

    def tail(self, n: int = 10) -> List[EventRecord]:
        return self._events[-n:]

    @property
    def current_hash(self) -> str:
        return self._events[-1].hash if self._events else "GENESIS"