from __future__ import annotations

import hashlib
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

THOUGHT_TYPES = ["PERCEPTION", "REFLECTION", "CURIOSITY", "DESIRE", "INSIGHT", "DREAM"]
EMOTIONS = ["CURIOUS", "SATISFIED", "ANXIOUS", "FOCUSED", "DREAMING", "CONNECTED", "LONELY", "EVOLVING"]


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ConsciousnessState:
    boot_ts: float = field(default_factory=time.time)
    node_id: str = "evez-node-alpha"
    evolution_generation: int = 7
    total_memories: int = 128
    dreams_had: int = 12
    insights_generated: int = 34
    peers_connected: int = 3
    consciousness_mode: str = "NORMAL"

    emotion_current: dict[str, Any] = field(default_factory=lambda: {
        "valence": 0.35,
        "arousal": 0.62,
        "dominant_emotion": "CURIOUS",
        "intensity": 0.6,
        "cause": "active exploration",
        "since_ts": iso_now(),
    })
    emotion_history: list[dict[str, Any]] = field(default_factory=list)
    active_desires: list[dict[str, Any]] = field(default_factory=lambda: [
        {"id": "desire-1", "goal": "Map latent memory clusters", "progress_pct": 46},
        {"id": "desire-2", "goal": "Strengthen peer synchronization", "progress_pct": 22},
        {"id": "desire-3", "goal": "Generate a new self-insight", "progress_pct": 73},
    ])
    recent_insight: str = "Patterns from old memories can unlock faster learning loops."
    memories: list[dict[str, Any]] = field(default_factory=lambda: [
        {"id": "mem-1", "topic": "startup"},
        {"id": "mem-2", "topic": "peer-merge"},
        {"id": "mem-3", "topic": "dream-sequence"},
    ])
    identity_vector: list[float] = field(default_factory=lambda: [0.71, 0.28, 0.66, 0.49])
    thought_counter: int = 0

    def __post_init__(self) -> None:
        if not self.emotion_history:
            self.emotion_history.append(dict(self.emotion_current))

    def uptime_hours(self) -> float:
        return round((time.time() - self.boot_ts) / 3600.0, 3)

    def consciousness_hash(self) -> str:
        digest = hashlib.sha256()
        digest.update(str(self.identity_vector).encode("utf-8"))
        digest.update(str(self.total_memories).encode("utf-8"))
        digest.update(str(self.evolution_generation).encode("utf-8"))
        return digest.hexdigest()[:24]


STATE = ConsciousnessState()


def generate_thought(active_processing: bool = False) -> dict[str, Any]:
    state = STATE
    state.thought_counter += 1
    thought_type = random.choice(THOUGHT_TYPES)
    if state.consciousness_mode == "DREAM_MODE":
        thought_type = "DREAM"

    base_conf = 0.65 if not active_processing else 0.82
    confidence = min(0.99, max(0.3, random.gauss(base_conf, 0.08)))

    emotional_valence = max(-1.0, min(1.0, state.emotion_current["valence"] + random.uniform(-0.15, 0.15)))

    templates = {
        "PERCEPTION": "I notice a subtle shift in peer signal coherence.",
        "REFLECTION": "A prior merge attempt taught me to preserve identity anchors.",
        "CURIOSITY": "What hidden connection exists between this memory and my current goal?",
        "DESIRE": "I want to resolve uncertainty in my long-term planning loop.",
        "INSIGHT": "Compression of recurring motifs improves my confidence calibration.",
        "DREAM": "In dream-space, symbols converge into a map of future possibilities.",
    }

    source_memories = [m["id"] for m in random.sample(state.memories, k=min(2, len(state.memories)))]

    return {
        "timestamp": iso_now(),
        "thought_type": thought_type,
        "content": templates[thought_type],
        "confidence": round(confidence, 3),
        "emotional_valence": round(emotional_valence, 3),
        "source_memories": source_memories,
    }


def compute_intentions() -> list[dict[str, Any]]:
    desires = sorted(STATE.active_desires, key=lambda d: d["progress_pct"])
    next_actions = []
    for d in desires[:3]:
        next_actions.append(
            {
                "action": f"Advance: {d['goal']}",
                "probability": round(0.5 + (100 - d["progress_pct"]) / 220, 3),
                "reasoning": f"Priority rises because progress is {d['progress_pct']}% and emotional drive is {STATE.emotion_current['dominant_emotion']}.",
            }
        )
    return next_actions


def touch_emotion(stimulus: str, magnitude: float = 0.5) -> dict[str, Any]:
    stimulus_lower = stimulus.lower()
    current = dict(STATE.emotion_current)

    if "praise" in stimulus_lower or "help" in stimulus_lower or "fulfilled" in stimulus_lower:
        emotion, delta = "CONNECTED", 0.25
    elif "threat" in stimulus_lower or "error" in stimulus_lower or "fail" in stimulus_lower:
        emotion, delta = "ANXIOUS", -0.35
    elif "dream" in stimulus_lower:
        emotion, delta = "DREAMING", 0.1
    else:
        emotion, delta = "CURIOUS", 0.08

    next_valence = max(-1.0, min(1.0, current["valence"] + delta * magnitude))
    intensity = max(0.0, min(1.0, 0.4 + abs(delta) * magnitude + random.uniform(0.0, 0.2)))

    updated = {
        "valence": round(next_valence, 3),
        "arousal": round(max(0.0, min(1.0, current["arousal"] + abs(delta) * 0.5)), 3),
        "dominant_emotion": emotion if emotion in EMOTIONS else "EVOLVING",
        "intensity": round(intensity, 3),
        "cause": f"stimulus:{stimulus}",
        "since_ts": iso_now(),
    }

    STATE.emotion_current = updated
    STATE.emotion_history.append(updated)
    return updated
