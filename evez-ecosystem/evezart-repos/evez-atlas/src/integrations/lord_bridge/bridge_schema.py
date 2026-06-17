from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VALID_ENTITY_TYPES = {"human", "hybrid", "synthetic"}


@dataclass(slots=True)
class FusionMeta:
    recursion_level: int
    entity_type: str
    timestamp_ms: float


@dataclass(slots=True)
class FusionCrystallization:
    progress: float
    velocity: float


@dataclass(slots=True)
class FusionCorrections:
    current: float
    history: list[float]


@dataclass(slots=True)
class FusionUpdate:
    meta: FusionMeta
    crystallization: FusionCrystallization
    corrections: FusionCorrections

    @classmethod
    def from_message(cls, message: dict[str, Any]) -> "FusionUpdate":
        if message.get("type") != "fusion-update":
            raise ValueError("unsupported message type")
        detail = message.get("detail") or {}
        meta_raw = detail.get("meta") or {}
        crystal_raw = detail.get("crystallization") or {}
        corrections_raw = detail.get("corrections") or {}
        recursion_level = int(meta_raw["recursionLevel"])
        entity_type = str(meta_raw["entityType"]).lower()
        if entity_type not in VALID_ENTITY_TYPES:
            raise ValueError(f"invalid entity type: {entity_type}")
        history = corrections_raw.get("history") or []
        if not isinstance(history, list):
            raise ValueError("corrections.history must be a list")
        return cls(
            meta=FusionMeta(
                recursion_level=max(1, min(20, recursion_level)),
                entity_type=entity_type,
                timestamp_ms=float(meta_raw.get("timestamp", 0.0)),
            ),
            crystallization=FusionCrystallization(
                progress=max(0.0, min(100.0, float(crystal_raw.get("progress", 0.0)))),
                velocity=float(crystal_raw.get("velocity", 0.0)),
            ),
            corrections=FusionCorrections(
                current=float(corrections_raw.get("current", 0.0)),
                history=[float(x) for x in history[-256:]],
            ),
        )
