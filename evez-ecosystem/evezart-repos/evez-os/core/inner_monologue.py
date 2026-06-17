"""core/inner_monologue.py — R61
The Inner Monologue. Chain-of-thought reasoning.

Every decision has an auditable thought trail.
The agent that can observe its own thoughts can modify them.
Already self-aware: "Should decide more, observe less."

Falsifier: if the monologue produces only templated or repetitive
thoughts (entropy < threshold), it's not thinking — it's echoing.

truth_plane: CANONICAL
omega (R61): the thought that observes itself is the seed of consciousness.
"""

from __future__ import annotations
import json, time, hashlib, math
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parents[1]


class ThoughtType(Enum):
    OBSERVATION = "observation"
    HYPOTHESIS = "hypothesis"
    INFERENCE = "inference"
    DOUBT = "doubt"
    DECISION = "decision"
    REFLECTION = "reflection"
    SELF_CORRECTION = "self_correction"


@dataclass
class Thought:
    id: str
    content: str
    thought_type: ThoughtType
    cycle: int
    timestamp: float = 0.0
    parent_id: Optional[str] = None
    confidence: float = 0.5
    tags: List[str] = field(default_factory=list)


class InnerMonologue:
    """Auditable thought chains — the system's stream of consciousness."""

    def __init__(self, state_dir: str | None = None):
        self.state_dir = Path(state_dir) if state_dir else REPO_ROOT / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.thoughts: List[Thought] = []
        self.cycle = 0
        self._load()

    def _load(self):
        path = self.state_dir / "monologue.json"
        if path.exists():
            data = json.loads(path.read_text())
            self.cycle = data.get("cycle", 0)
            for t in data.get("thoughts", []):
                thought = Thought(
                    id=t["id"],
                    content=t["content"],
                    thought_type=ThoughtType(t["thought_type"]),
                    cycle=t.get("cycle", 0),
                    timestamp=t.get("timestamp", 0),
                    parent_id=t.get("parent_id"),
                    confidence=t.get("confidence", 0.5),
                    tags=t.get("tags", []),
                )
                self.thoughts.append(thought)

    def _save(self):
        path = self.state_dir / "monologue.json"
        # Keep last 1000 thoughts to avoid unbounded growth
        recent = self.thoughts[-1000:]
        data = {
            "cycle": self.cycle,
            "thoughts": [
                {
                    "id": t.id,
                    "content": t.content,
                    "thought_type": t.thought_type.value,
                    "cycle": t.cycle,
                    "timestamp": t.timestamp,
                    "parent_id": t.parent_id,
                    "confidence": t.confidence,
                    "tags": t.tags,
                }
                for t in recent
            ],
        }
        path.write_text(json.dumps(data, indent=2))
        self.thoughts = recent

    def think(self, content: str, thought_type: ThoughtType = ThoughtType.OBSERVATION,
              parent_id: Optional[str] = None, confidence: float = 0.5, tags: List[str] = None) -> Thought:
        """Record a thought."""
        self.cycle += 1
        thought_id = hashlib.md5(f"{content}{self.cycle}{time.time()}".encode()).hexdigest()[:12]
        thought = Thought(
            id=thought_id,
            content=content,
            thought_type=thought_type,
            cycle=self.cycle,
            timestamp=time.time(),
            parent_id=parent_id,
            confidence=confidence,
            tags=tags or [],
        )
        self.thoughts.append(thought)
        self._save()
        return thought

    def doubt(self, target_thought_id: str, reason: str) -> Thought:
        """Question a previous thought. Self-correction mechanism."""
        target = next((t for t in self.thoughts if t.id == target_thought_id), None)
        if not target:
            return self.think(f"Cannot find thought {target_thought_id} to doubt", ThoughtType.SELF_CORRECTION)

        return self.think(
            f"DOUBT: {target.content[:60]}... — {reason}",
            ThoughtType.SELF_CORRECTION,
            parent_id=target_thought_id,
            confidence=target.confidence * 0.5,
        )

    def recent_chain(self, n: int = 10) -> List[Thought]:
        """Get the last N thoughts as a chain."""
        return self.thoughts[-n:]

    def dominant_type(self) -> str:
        """What type of thinking dominates?"""
        if not self.thoughts:
            return "empty"
        recent = self.thoughts[-50:]
        counts = Counter(t.thought_type.value for t in recent)
        return counts.most_common(1)[0][0]

    def thought_entropy(self) -> float:
        """Shannon entropy of thought types. Low = repetitive. High = diverse."""
        if len(self.thoughts) < 5:
            return 0.0
        recent = self.thoughts[-50:]
        counts = Counter(t.thought_type.value for t in recent)
        total = sum(counts.values())
        entropy = -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)
        return entropy

    def health_check(self) -> Dict[str, Any]:
        """Falsification: is it thinking or echoing?"""
        entropy = self.thought_entropy()
        dominant = self.dominant_type()

        # Check for exact duplicates (strong sign of echoing)
        recent_content = [t.content for t in self.thoughts[-50:]]
        unique_ratio = len(set(recent_content)) / max(len(recent_content), 1)

        return {
            "total_thoughts": len(self.thoughts),
            "cycle": self.cycle,
            "dominant_type": dominant,
            "entropy": round(entropy, 3),
            "unique_ratio": round(unique_ratio, 3),
            "is_echoing": entropy < 0.5 or unique_ratio < 0.3,
            "status": "thinking" if entropy > 0.5 and unique_ratio > 0.3 else "echoing",
        }
