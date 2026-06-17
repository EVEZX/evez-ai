"""Cognitive Event (CE) — the atomic unit of agent reasoning in EVEZ-OS."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from typing import Any, Optional


class CEState(str, Enum):
    TEST     = "TEST"    # freshly generated, not yet validated
    ACT      = "ACT"     # survived all rotations — commit to state
    HOLD     = "HOLD"    # partial pass — await more data
    DISCARD  = "DISCARD" # failed one or more rotations (Rule 1)


@dataclass
class CognitiveEvent:
    assertion: str                          # e.g. "USDC/USDT spread >2.5% within 30s"
    source_agent: str
    raw_signal: dict
    state: CEState                          = CEState.TEST
    confidence: float                       = 0.0          # 0–1
    rotation_scores: dict[str, float]       = field(default_factory=dict)
    rotation_meta:   dict[str, Any]         = field(default_factory=dict)
    defeater_log:    list[str]              = field(default_factory=list)
    identity_root_refused: bool             = False        # Rule 2 — Gödelian exception
    arc_agi_efficiency_delta: Optional[float] = None       # Mar 25: external benchmark
    ce_id: str                              = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str                         = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "ce_id":           self.ce_id,
            "assertion":       self.assertion,
            "source_agent":    self.source_agent,
            "state":           self.state.value,
            "confidence":      self.confidence,
            "rotation_scores": self.rotation_scores,
            "defeater_log":    self.defeater_log,
            "identity_root_refused": self.identity_root_refused,
            "arc_agi_efficiency_delta": self.arc_agi_efficiency_delta,
            "created_at":      self.created_at,
        }
