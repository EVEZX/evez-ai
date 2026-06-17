#!/usr/bin/env python3
"""
EVEZ-OS Agent Bus — pub/sub message bus for inter-agent communication.

Agents publish events and subscribe to event types. All messages persisted
to an append-only JSONL log for full auditability.

Event types:
    TASK_CREATED, TASK_COMPLETED, AGENT_SPAWNED, AGENT_DIED,
    ERROR, EVOLUTION, FIRE_EVENT, OODA_CYCLE, REPAIR, EXPANSION,
    MEMORY_CONSOLIDATION, CROSS_REPO, HEARTBEAT
"""
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Canonical event types
EVENT_TYPES = frozenset({
    "TASK_CREATED",
    "TASK_COMPLETED",
    "AGENT_SPAWNED",
    "AGENT_DIED",
    "ERROR",
    "EVOLUTION",
    "FIRE_EVENT",
    "OODA_CYCLE",
    "REPAIR",
    "EXPANSION",
    "MEMORY_CONSOLIDATION",
    "CROSS_REPO",
    "HEARTBEAT",
})


class Event:
    """Immutable event on the bus."""

    __slots__ = (
        "event_id", "event_type", "source", "timestamp",
        "data", "correlation_id",
    )

    def __init__(
        self,
        event_type: str,
        source: str,
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ):
        self.event_id = uuid.uuid4().hex[:16]
        self.event_type = event_type
        self.source = source
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.data = data or {}
        self.correlation_id = correlation_id or self.event_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "timestamp": self.timestamp,
            "data": self.data,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Event":
        ev = cls.__new__(cls)
        ev.event_id = d["event_id"]
        ev.event_type = d["event_type"]
        ev.source = d["source"]
        ev.timestamp = d["timestamp"]
        ev.data = d.get("data", {})
        ev.correlation_id = d.get("correlation_id", ev.event_id)
        return ev

    def __repr__(self) -> str:
        return f"Event({self.event_type}, src={self.source}, id={self.event_id})"


# Type alias for subscriber callbacks
Subscriber = Callable[[Event], None]


class AgentBus:
    """
    Pub/sub message bus with persistent JSONL log.

    Thread-safe. Subscribers receive events synchronously in the
    publisher's thread (keeps ordering deterministic).
    """

    def __init__(self, log_path: Optional[Path] = None):
        self._lock = threading.Lock()
        self._subscribers: Dict[str, List[Subscriber]] = {}
        self._wildcard_subscribers: List[Subscriber] = []
        self._log_path = log_path or Path("spine/agent_bus.jsonl")
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    # ── publish / subscribe ──────────────────────────────────────────

    def publish(self, event: Event) -> Event:
        """Publish an event: persist then fan-out to subscribers."""
        self._persist(event)
        with self._lock:
            targets = list(self._subscribers.get(event.event_type, []))
            wildcards = list(self._wildcard_subscribers)
        for fn in targets + wildcards:
            try:
                fn(event)
            except Exception:
                pass  # subscribers must not crash the bus
        return event

    def emit(
        self,
        event_type: str,
        source: str,
        data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """Convenience: build + publish in one call."""
        return self.publish(Event(event_type, source, data, correlation_id))

    def subscribe(
        self,
        event_type: Optional[str],
        callback: Subscriber,
    ) -> None:
        """
        Subscribe to a specific event type, or pass None for wildcard.
        """
        with self._lock:
            if event_type is None:
                self._wildcard_subscribers.append(callback)
            else:
                self._subscribers.setdefault(event_type, []).append(callback)

    def unsubscribe(
        self,
        event_type: Optional[str],
        callback: Subscriber,
    ) -> None:
        with self._lock:
            if event_type is None:
                try:
                    self._wildcard_subscribers.remove(callback)
                except ValueError:
                    pass
            else:
                lst = self._subscribers.get(event_type, [])
                try:
                    lst.remove(callback)
                except ValueError:
                    pass

    # ── persistence ──────────────────────────────────────────────────

    def _persist(self, event: Event) -> None:
        try:
            with open(self._log_path, "a") as f:
                f.write(json.dumps(event.to_dict(), separators=(",", ":")) + "\n")
        except OSError:
            pass  # graceful degradation if disk is unavailable

    def read_log(self, limit: int = 0) -> List[Event]:
        """Read events from the persistent log. 0 = all."""
        events: List[Event] = []
        try:
            with open(self._log_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(Event.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, KeyError):
                        continue
        except FileNotFoundError:
            pass
        if limit > 0:
            return events[-limit:]
        return events

    def read_log_by_type(self, event_type: str, limit: int = 50) -> List[Event]:
        """Read events of a specific type from log."""
        return [
            e for e in self.read_log()
            if e.event_type == event_type
        ][-limit:]

    def read_log_by_source(self, source: str, limit: int = 50) -> List[Event]:
        """Read events from a specific source."""
        return [
            e for e in self.read_log()
            if e.source == source
        ][-limit:]

    # ── helpers ──────────────────────────────────────────────────────

    def tail(self, n: int = 20) -> List[Dict[str, Any]]:
        """Return last N events as dicts (for CLI / status display)."""
        return [e.to_dict() for e in self.read_log(limit=n)]

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            typed = sum(len(v) for v in self._subscribers.values())
            return typed + len(self._wildcard_subscribers)

    def __repr__(self) -> str:
        return f"AgentBus(log={self._log_path}, subs={self.subscriber_count})"


# ── Singleton for the default spine-backed bus ───────────────────────

_default_bus: Optional[AgentBus] = None
_bus_lock = threading.Lock()


def get_bus(log_path: Optional[Path] = None) -> AgentBus:
    """Get or create the default AgentBus singleton."""
    global _default_bus
    with _bus_lock:
        if _default_bus is None:
            _default_bus = AgentBus(log_path)
        return _default_bus
