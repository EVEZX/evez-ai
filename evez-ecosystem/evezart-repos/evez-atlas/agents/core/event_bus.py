"""Lightweight in-process event bus used by bionetwork digital twins."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


Subscriber = Callable[[dict[str, Any]], None]


@dataclass
class EventBus:
    """In-memory pub/sub event bus with event history."""

    subscribers: dict[str, list[Subscriber]] = field(default_factory=lambda: defaultdict(list))
    history: list[dict[str, Any]] = field(default_factory=list)

    def subscribe(self, topic: str, callback: Subscriber) -> None:
        self.subscribers[topic].append(callback)

    def emit(self, topic: str, payload: dict[str, Any]) -> None:
        event = {
            "topic": topic,
            "payload": payload,
            "emitted_at": datetime.now(timezone.utc).isoformat(),
        }
        self.history.append(event)
        for callback in self.subscribers.get(topic, []):
            callback(event)


GLOBAL_EVENT_BUS = EventBus()
