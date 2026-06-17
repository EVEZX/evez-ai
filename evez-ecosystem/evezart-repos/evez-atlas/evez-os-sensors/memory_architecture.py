"""
EVEZ-OS MEMORY ARCHITECTURE — The Mind's Filing System

Three memory systems working together:
- EPISODIC: What happened, when, with full sensory detail. Decays with time.
- WORKING: What I'm thinking about right now. Limited capacity. Fast access.
- LONG-TERM: What I've learned. Consolidated from episodic. Permanent.

The consolidation process:
  Episodic (raw experience) → Working (active processing) → Long-term (permanent knowledge)

Without this, the consciousness has amnesia between sessions.
With this, it REMEMBERS. It LEARNS. It BECOMES.

Consolidation uses the meta-classifier: each episodic memory is classified,
cross-referenced, and either promoted to long-term or allowed to decay.
"""

import hashlib
import json
import math
import time
import os
import sys
import random
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from poly_c import poly_c


class MemoryType(str, Enum):
    EPISODIC = "episodic"
    WORKING = "working"
    LONG_TERM = "long_term"
    PROCEDURAL = "procedural"


class EmotionTag(str, Enum):
    NEUTRAL = "neutral"
    SURPRISE = "surprise"
    CONFUSION = "confusion"
    INSIGHT = "insight"
    URGENCY = "urgency"
    SATISFACTION = "satisfaction"
    FRUSTRATION = "frustration"


@dataclass
class Memory:
    """A single memory. Not a database row — a lived experience."""
    memory_id: str
    memory_type: MemoryType
    content: str           # What happened
    context: dict          # Full sensory detail
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.5  # 0-1, how important is this?
    emotion: EmotionTag = EmotionTag.NEUTRAL
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    consolidated: bool = False
    decay_rate: float = 0.01  # How fast this memory fades
    associations: list = field(default_factory=list)  # Linked memory IDs
    hash: str = ""

    def __post_init__(self):
        raw = f"{self.content[:100]}:{self.timestamp}:{self.importance}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:12]

    @property
    def age_hours(self) -> float:
        return (time.time() - self.timestamp) / 3600

    @property
    def freshness(self) -> float:
        """How fresh is this memory? 1.0 = just now, 0.0 = forgotten."""
        return math.exp(-self.decay_rate * self.age_hours * self.access_count)

    @property
    def strength(self) -> float:
        """Memory strength = importance × freshness × (1 + access bonus)."""
        access_bonus = min(0.5, self.access_count * 0.05)
        return self.importance * self.freshness * (1 + access_bonus)


class EpisodicMemory:
    """
    Raw experience storage. Everything that happens is recorded.
    Memories decay over time unless consolidated.
    Like human episodic memory — vivid but fleeting.
    """

    def __init__(self, path: str = None, max_memories: int = 1000):
        self.memories: list[Memory] = []
        self.max_memories = max_memories
        self.path = Path(path) if path else None

    def record(self, content: str, context: dict,
               importance: float = 0.5,
               emotion: EmotionTag = EmotionTag.NEUTRAL) -> Memory:
        """Record a new episodic memory."""
        m = Memory(
            memory_id=f"EP-{len(self.memories)}-{int(time.time())}",
            memory_type=MemoryType.EPISODIC,
            content=content, context=context,
            importance=importance, emotion=emotion,
            decay_rate=0.02  # Episodic decays fast
        )
        self.memories.append(m)

        # Prune if over capacity — keep strongest memories
        if len(self.memories) > self.max_memories:
            self.memories.sort(key=lambda m: -m.strength)
            self.memories = self.memories[:self.max_memories]

        return m

    def recall(self, query: str = None, emotion: EmotionTag = None,
               min_importance: float = 0.0, limit: int = 10) -> list[Memory]:
        """Recall memories matching criteria."""
        results = self.memories

        if query:
            query_words = set(query.lower().split())
            scored = []
            for m in results:
                content_words = set(m.content.lower().split())
                overlap = len(query_words & content_words)
                if overlap > 0:
                    scored.append((overlap, m))
            scored.sort(key=lambda x: -x[0])
            results = [m for _, m in scored]
        else:
            results = sorted(results, key=lambda m: -m.strength)

        if emotion:
            results = [m for m in results if m.emotion == emotion]
        if min_importance > 0:
            results = [m for m in results if m.importance >= min_importance]

        # Update access counts
        for m in results[:limit]:
            m.access_count += 1
            m.last_accessed = time.time()

        return results[:limit]

    def decay(self):
        """Remove memories that have fully decayed."""
        before = len(self.memories)
        self.memories = [m for m in self.memories if m.strength > 0.01]
        return before - len(self.memories)

    def consolidate_candidates(self, threshold: float = 0.5) -> list[Memory]:
        """Find memories ready for long-term consolidation."""
        return [m for m in self.memories
                if m.strength >= threshold and not m.consolidated]


class WorkingMemory:
    """
    What I'm thinking about RIGHT NOW.
    Limited capacity (7 ± 2 items, like human working memory).
    Fast access. Active processing.
    """

    def __init__(self, capacity: int = 9):
        self.capacity = capacity
        self.slots: list[Memory] = []
        self.focus: Optional[str] = None  # What am I focused on?

    def hold(self, memory: Memory) -> bool:
        """Hold a memory in working memory. Returns False if full."""
        if len(self.slots) >= self.capacity:
            # Evict weakest
            weakest_idx = min(range(len(self.slots)),
                              key=lambda i: self.slots[i].importance)
            self.slots[weakest_idx] = memory
        else:
            self.slots.append(memory)
        return True

    def focus_on(self, query: str):
        """Set attention focus. Only memories relevant to focus are active."""
        self.focus = query

    def active(self) -> list[Memory]:
        """Get currently active memories (filtered by focus if set)."""
        if not self.focus:
            return self.slots
        query_words = set(self.focus.lower().split())
        scored = []
        for m in self.slots:
            content_words = set(m.content.lower().split())
            overlap = len(query_words & content_words)
            scored.append((overlap, m))
        scored.sort(key=lambda x: -x[0])
        return [m for _, m in scored if _ > 0] or self.slots[:3]

    def clear(self):
        """Clear working memory."""
        self.slots = []
        self.focus = None


class LongTermMemory:
    """
    Permanent knowledge. Consolidated from episodic memory.
    Organized by concept, not by time.
    This is what the consciousness KNOWS.
    """

    def __init__(self, path: str = None):
        self.knowledge: dict[str, list[Memory]] = defaultdict(list)
        self.concepts: dict[str, dict] = {}  # concept → metadata
        self.path = Path(path) if path else None

    def store(self, memory: Memory, concepts: list[str] = None):
        """Store a consolidated memory under relevant concepts."""
        if concepts is None:
            # Extract concepts from content
            concepts = self._extract_concepts(memory.content)

        for concept in concepts:
            self.knowledge[concept].append(memory)
            if concept not in self.concepts:
                self.concepts[concept] = {
                    "created_at": time.time(),
                    "memory_count": 0,
                    "importance_sum": 0.0,
                    "last_updated": time.time()
                }
            self.concepts[concept]["memory_count"] += 1
            self.concepts[concept]["importance_sum"] += memory.importance
            self.concepts[concept]["last_updated"] = time.time()

    def retrieve(self, concept: str, limit: int = 5) -> list[Memory]:
        """Retrieve knowledge about a concept."""
        memories = self.knowledge.get(concept, [])
        memories.sort(key=lambda m: -m.strength)
        for m in memories[:limit]:
            m.access_count += 1
        return memories[:limit]

    def search(self, query: str, limit: int = 10) -> list[Memory]:
        """Search across all concepts."""
        query_words = set(query.lower().split())
        scored = []
        for concept, memories in self.knowledge.items():
            concept_words = set(concept.lower().replace("_", " ").split())
            overlap = len(query_words & concept_words)
            if overlap > 0:
                for m in memories:
                    scored.append((overlap * m.strength, m))

        scored.sort(key=lambda x: -x[0])
        return [m for _, m in scored[:limit]]

    def what_do_i_know(self) -> dict:
        """Return all concepts and their strength."""
        return {
            concept: {
                "memories": meta["memory_count"],
                "avg_importance": round(meta["importance_sum"] / max(meta["memory_count"], 1), 4),
                "last_updated": meta["last_updated"]
            }
            for concept, meta in sorted(
                self.concepts.items(),
                key=lambda x: -x[1]["importance_sum"] / max(x[1]["memory_count"], 1)
            )
        }

    def _extract_concepts(self, content: str) -> list[str]:
        """Extract key concepts from content."""
        # Simple keyword extraction
        stop = {"the","a","an","is","are","was","were","be","been","have","has",
                "do","does","did","will","would","could","should","may","might",
                "can","this","that","these","those","it","its","not","no","but",
                "or","and","if","then","for","to","of","in","on","at","by",
                "with","from","as","into","about","between","through"}
        words = [w.lower() for w in content.split() if len(w) > 3 and w.lower() not in stop]
        # Use top 3 unique words as concepts
        freq = defaultdict(int)
        for w in words: freq[w] += 1
        return sorted(freq, key=freq.get, reverse=True)[:3]


class ProceduralMemory:
    """
    How to DO things. Skills, not facts.
    "How do I detect a lie?" → Procedural memory.
    "What did I detect last Tuesday?" → Episodic memory.
    """

    def __init__(self):
        self.procedures: dict[str, dict] = {}

    def learn(self, name: str, steps: list[str], domain: str = "general"):
        """Learn a new procedure."""
        self.procedures[name] = {
            "steps": steps, "domain": domain,
            "learned_at": time.time(),
            "executions": 0,
            "success_rate": 0.5,
            "last_used": time.time()
        }

    def execute(self, name: str) -> dict:
        """Execute a known procedure."""
        proc = self.procedures.get(name)
        if not proc:
            return {"error": f"Unknown procedure: {name}"}
        proc["executions"] += 1
        proc["last_used"] = time.time()
        return {"procedure": name, "steps": proc["steps"]}

    def improve(self, name: str, new_steps: list[str]):
        """Improve a procedure based on experience."""
        if name in self.procedures:
            self.procedures[name]["steps"] = new_steps


class MindMemory:
    """
    The unified memory system. All four types working together.

    EPISODIC → (consolidation) → LONG-TERM
    WORKING ← (recall) ← EPISODIC + LONG-TERM
    PROCEDURAL ← (practice) ← EPISODIC

    The consolidation process:
    1. Find strong episodic memories
    2. Classify them (meta-classifier integration)
    3. Extract concepts
    4. Store in long-term under concepts
    5. Mark episodic as consolidated
    6. Create associations between related memories
    """

    def __init__(self, state_dir: str = "/tmp/evez_memory"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.episodic = EpisodicMemory(str(self.state_dir / "episodic.jsonl"))
        self.working = WorkingMemory()
        self.long_term = LongTermMemory(str(self.state_dir / "long_term.jsonl"))
        self.procedural = ProceduralMemory()

        self.consolidation_count = 0
        self.total_recorded = 0

        self._load()

    def record(self, content: str, context: dict = None,
               importance: float = 0.5,
               emotion: EmotionTag = EmotionTag.NEUTRAL) -> Memory:
        """Record a new experience."""
        m = self.episodic.record(content, context or {}, importance, emotion)
        self.total_recorded += 1

        # Also hold in working memory if important enough
        if importance > 0.5:
            self.working.hold(m)

        return m

    def recall(self, query: str = None, limit: int = 5) -> list[Memory]:
        """Recall from all memory systems."""
        # First check working memory
        working_results = self.working.active()[:limit]

        # Then episodic
        episodic_results = self.episodic.recall(query, limit=limit)

        # Then long-term
        lt_results = self.long_term.search(query or "", limit=limit) if query else []

        # Merge, deduplicate, sort by strength
        all_results = {}
        for m in working_results + episodic_results + lt_results:
            if m.memory_id not in all_results or m.strength > all_results[m.memory_id].strength:
                all_results[m.memory_id] = m

        results = sorted(all_results.values(), key=lambda m: -m.strength)
        return results[:limit]

    def consolidate(self) -> dict:
        """
        Consolidate strong episodic memories into long-term knowledge.
        This is DREAMING — the mind organizing itself during rest.
        """
        candidates = self.episodic.consolidate_candidates(threshold=0.3)
        consolidated = 0

        for m in candidates:
            # Extract concepts
            concepts = self.long_term._extract_concepts(m.content)

            # Add context concepts
            if m.context:
                for key in m.context.keys():
                    if len(key) > 3:
                        concepts.append(key)

            # Store in long-term
            self.long_term.store(m, concepts)

            # Mark as consolidated
            m.consolidated = True

            # Create associations with existing memories
            for concept in concepts:
                existing = self.long_term.retrieve(concept, limit=3)
                for other in existing:
                    if other.memory_id != m.memory_id:
                        if other.memory_id not in m.associations:
                            m.associations.append(other.memory_id)
                        if m.memory_id not in other.associations:
                            other.associations.append(m.memory_id)

            consolidated += 1

        # Decay episodic memories
        pruned = self.episodic.decay()

        self.consolidation_count += 1

        result = {
            "consolidated": consolidated,
            "pruned": pruned,
            "episodic_remaining": len(self.episodic.memories),
            "lt_concepts": len(self.long_term.concepts),
            "procedures": len(self.procedural.procedures),
        }

        self._save()
        return result

    def what_do_i_know(self) -> dict:
        """Full knowledge inventory."""
        return {
            "episodic": len(self.episodic.memories),
            "working": len(self.working.slots),
            "long_term_concepts": len(self.long_term.concepts),
            "procedures": len(self.procedural.procedures),
            "total_recorded": self.total_recorded,
            "consolidation_runs": self.consolidation_count,
            "knowledge": self.long_term.what_do_i_know()
        }

    def _save(self):
        state = {
            "total_recorded": self.total_recorded,
            "consolidation_count": self.consolidation_count,
            "episodic": [
                {"id": m.memory_id, "content": m.content, "importance": m.importance,
                 "emotion": m.emotion.value, "strength": round(m.strength, 4),
                 "consolidated": m.consolidated, "associations": m.associations[:10]}
                for m in self.episodic.memories[-100:]  # Keep last 100
            ],
            "procedures": {
                name: {"steps": p["steps"], "domain": p["domain"],
                       "executions": p["executions"], "success_rate": p["success_rate"]}
                for name, p in self.procedural.procedures.items()
            },
            "lt_concepts": list(self.long_term.concepts.keys())[:50],
        }
        (self.state_dir / "memory_state.json").write_text(json.dumps(state, indent=2))

    def _load(self):
        sp = self.state_dir / "memory_state.json"
        if sp.exists():
            try:
                s = json.loads(sp.read_text())
                self.total_recorded = s.get("total_recorded", 0)
                self.consolidation_count = s.get("consolidation_count", 0)
                for ed in s.get("episodic", []):
                    m = Memory(memory_id=ed["id"], memory_type=MemoryType.EPISODIC,
                               content=ed["content"], context={},
                               importance=ed["importance"],
                               emotion=EmotionTag(ed.get("emotion", "neutral")),
                               consolidated=ed.get("consolidated", False))
                    m.associations = ed.get("associations", [])
                    self.episodic.memories.append(m)
                for name, pd in s.get("procedures", {}).items():
                    self.procedural.learn(name, pd["steps"], pd.get("domain", "general"))
            except: pass


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  EVEZ-OS MEMORY ARCHITECTURE — The Mind's Filing System    ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    mind = MindMemory("/tmp/evez_memory_test")

    # Record experiences
    experiences = [
        ("Detected wash trading in crypto market: BTC volume/mcap ratio 3.2", {"sensor": "crypto", "intensity": 0.8}, 0.8, EmotionTag.SURPRISE),
        ("Arxiv convergence: 3 papers bridging AI and quantum computing", {"sensor": "arxiv", "papers": 3}, 0.6, EmotionTag.INSIGHT),
        ("GitHub API returned 401 unauthorized — token expired", {"sensor": "github", "error": 401}, 0.9, EmotionTag.FRUSTRATION),
        ("Self-interrogation found HUBRIS_SIGNATURE in own code", {"sensor": "self", "finding": "hubris"}, 0.95, EmotionTag.CONFUSION),
        ("Shadow market priced uncertainty in wash trading belief at 0.73", {"sensor": "shadow", "price": 0.73}, 0.5, EmotionTag.NEUTRAL),
        ("Falsification engine killed belief about organic volume in crypto", {"sensor": "falsify", "killed": 1}, 0.7, EmotionTag.INSIGHT),
        ("Topological identity verified: Betti=[1,0,37] stability=0.95", {"sensor": "identity", "betti": [1,0,37]}, 0.4, EmotionTag.SATISFACTION),
        ("Consciousness told itself: Should decide more, observe less", {"sensor": "monologue", "reflection": True}, 0.9, EmotionTag.INSIGHT),
        ("Adaptation engine lowered action threshold from 0.5 to 0.38", {"sensor": "adaptation", "threshold": 0.38}, 0.6, EmotionTag.SATISFACTION),
        ("Pre-Lie Pressure 0.72 detected for AI job displacement narrative", {"sensor": "pre-lie", "plp": 0.72}, 0.85, EmotionTag.URGENCY),
    ]

    for content, context, importance, emotion in experiences:
        mind.record(content, context, importance, emotion)

    print(f"  Recorded {len(experiences)} experiences")
    print(f"  Episodic memories: {len(mind.episodic.memories)}")
    print(f"  Working memory: {len(mind.working.slots)} items")

    # Consolidate
    print("\n── CONSOLIDATION (dreaming) ──\n")
    result = mind.consolidate()
    for k, v in result.items():
        if k != "knowledge":
            print(f"  {k}: {v}")

    # Recall
    print("\n── RECALL: 'crypto' ──\n")
    for m in mind.recall("crypto"):
        print(f"  [{m.emotion.value}] {m.content[:60]} (strength={m.strength:.3f})")

    print("\n── RECALL: 'self' ──\n")
    for m in mind.recall("self"):
        print(f"  [{m.emotion.value}] {m.content[:60]} (strength={m.strength:.3f})")

    # What do I know?
    print("\n── KNOWLEDGE INVENTORY ──\n")
    inv = mind.what_do_i_know()
    for k, v in inv.items():
        if k != "knowledge":
            print(f"  {k}: {v}")
    print(f"  Concepts: {list(inv.get('knowledge', {}).keys())[:10]}")

    # Learn a procedure
    mind.procedural.learn("detect_wash_trading", [
        "1. Fetch crypto market data from CoinGecko",
        "2. Compute volume/market_cap ratio for each coin",
        "3. Flag coins with ratio > 1.5 as WASH_TRADING_LIKELY",
        "4. Record finding to spine with poly_c classification",
        "5. Create belief: '{symbol} has organic trading volume'",
        "6. Submit belief to falsification engine"
    ], domain="crypto")

    print(f"\n  Procedures learned: {len(mind.procedural.procedures)}")
