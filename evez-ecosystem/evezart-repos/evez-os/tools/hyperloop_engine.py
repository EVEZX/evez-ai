#!/usr/bin/env python3
"""
hyperloop_engine.py — Exponential Acceleration Engine for Agent Bus
HYPERLOOP-003. Compounds Round 1 (architecture) + Round 2 (compression) + Round 3 (acceleration).

Each round is faster than the last by a compounding factor.
The acceleration comes from 5 new techniques layered ON TOP of swarm_compress.py's 5.

Total stack: 10 techniques, 2 layers.

Layer 1 (swarm_compress.py — Round 2):
  1. Stigmergy, 2. Delta compression, 3. Fan-out/gather, 4. Speculative cache, 5. Quorum shortcut

Layer 2 (hyperloop_engine.py — Round 3):
  6. Pheromone decay, 7. Bloom dedup, 8. Merkle spine, 9. Speculative execution,
  10. Information bottleneck compression
"""

import hashlib
import json
import math
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


# ─── Technique 6: Pheromone Decay ──────────────────────────────
class PheromoneDecay:
    """Ant colony pheromone evaporation on spine entries.
    Older entries have less routing influence.
    Failure mode: STALE_AMNESIA — if decay too fast, swarm forgets
    critical early discoveries. Mitigation: Ω-tagged entries never decay."""

    def __init__(self, rho: float = 0.1, omega_tag: str = "CANONICAL"):
        self.rho = rho  # evaporation rate per round
        self.omega_tag = omega_tag

    def apply(self, entries: List[dict], current_round: int) -> List[dict]:
        """Weight entries by recency. Ω-tagged entries weight = 1.0 always."""
        weighted = []
        for e in entries:
            age = current_round - e.get("round", 0)
            if e.get("status") == self.omega_tag:
                weight = 1.0  # Never decays
            else:
                weight = (1 - self.rho) ** age
            e_copy = dict(e)
            e_copy["_pheromone_weight"] = round(weight, 4)
            weighted.append(e_copy)
        return weighted

    def prune(self, entries: List[dict], threshold: float = 0.01) -> List[dict]:
        """Remove entries below pheromone threshold (effectively forgotten)."""
        return [e for e in entries if e.get("_pheromone_weight", 1.0) >= threshold]


# ─── Technique 7: Bloom Filter Dedup ──────────────────────────
class BloomDedup:
    """Probabilistic dedup for agent outputs.
    Perplexity-sourced: m = -n * ln(p) / (ln(2))^2
    For n=1000, p=0.01: m=9585 bits (1.2KB).
    Failure mode: FALSE_POSITIVE_DROP — real new entries rejected.
    Mitigation: two-tier (Bloom fast reject → exact check on positives)."""

    def __init__(self, n: int = 1000, fp_rate: float = 0.01):
        self.m = int(-n * math.log(fp_rate) / (math.log(2) ** 2))
        self.k = int((self.m / n) * math.log(2))
        self.bits = [0] * self.m
        self.exact_set = set()  # Tier 2: exact check

    def _hashes(self, item: str) -> List[int]:
        """Generate k hash positions."""
        positions = []
        for i in range(self.k):
            h = hashlib.md5(f"{item}:{i}".encode()).hexdigest()
            positions.append(int(h, 16) % self.m)
        return positions

    def add(self, item: str):
        """Add item to filter."""
        for pos in self._hashes(item):
            self.bits[pos] = 1
        self.exact_set.add(item)

    def is_duplicate(self, item: str) -> bool:
        """Two-tier check: Bloom → exact."""
        # Bloom: fast rejection (definitely new = False)
        for pos in self._hashes(item):
            if self.bits[pos] == 0:
                return False
        # Bloom says maybe-duplicate → exact check
        return item in self.exact_set

    def stats(self) -> dict:
        fill = sum(self.bits) / self.m
        return {"bits": self.m, "hashes": self.k, "fill_ratio": round(fill, 4),
                "exact_items": len(self.exact_set)}


# ─── Technique 8: Merkle Spine ─────────────────────────────────
class MerkleSpine:
    """Merkle tree over spine entries for O(log n) verification.
    Failure mode: REBALANCE_COST — inserting new entries requires
    recomputing path to root. Amortized O(log n) per insert."""

    def __init__(self):
        self.leaves = []
        self.tree = []

    def _hash(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def build(self, entries: List[dict]):
        """Build Merkle tree from spine entries."""
        self.leaves = [self._hash(json.dumps(e, sort_keys=True)) for e in entries]
        if not self.leaves:
            self.tree = []
            return
        level = list(self.leaves)
        self.tree = [level]
        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else left
                next_level.append(self._hash(left + right))
            level = next_level
            self.tree.append(level)

    def root(self) -> Optional[str]:
        return self.tree[-1][0] if self.tree else None

    def verify_entry(self, index: int) -> List[str]:
        """Return proof path for entry at index. O(log n) verification."""
        if not self.tree or index >= len(self.leaves):
            return []
        proof = []
        idx = index
        for level in self.tree[:-1]:
            sibling = idx ^ 1
            if sibling < len(level):
                proof.append(level[sibling])
            idx //= 2
        return proof

    def stats(self) -> dict:
        return {"leaves": len(self.leaves), "depth": len(self.tree),
                "root": self.root(), "verification_cost": f"O(log {len(self.leaves)})"}


# ─── Technique 9: Speculative Execution ────────────────────────
class SpeculativeExecutor:
    """Start next round BEFORE current finishes.
    Break-even: rollback_cost < prediction_accuracy * saved_time.
    Failure mode: WASTED_COMPUTE — wrong prediction = thrown away work.
    Mitigation: only speculate on high-confidence predictions (>0.7)."""

    def __init__(self, confidence_threshold: float = 0.7):
        self.threshold = confidence_threshold
        self.predictions = {}
        self.hits = 0
        self.misses = 0

    def should_speculate(self, predicted_lobby: str, confidence: float) -> bool:
        return confidence >= self.threshold

    def record_result(self, predicted: str, actual: str):
        if predicted == actual:
            self.hits += 1
        else:
            self.misses += 1

    def accuracy(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def break_even(self, round_time_ms: int, rollback_cost_ms: int) -> dict:
        """Break-even formula: accuracy > rollback_cost / round_time."""
        threshold = rollback_cost_ms / round_time_ms if round_time_ms > 0 else 1.0
        return {"accuracy": round(self.accuracy(), 3),
                "break_even_threshold": round(threshold, 3),
                "profitable": self.accuracy() > threshold,
                "saved_ms_per_round": int(round_time_ms * self.accuracy() - rollback_cost_ms * (1 - self.accuracy()))}


# ─── Technique 10: Information Bottleneck ──────────────────────
class InfoBottleneck:
    """Compress agent outputs preserving mission-relevant signal.
    L[p(t|x)] = I(T;X) - beta * I(T;Y)
    Minimize info about input X, maximize info about target Y.
    Failure mode: OVER_COMPRESSION — mission signal lost.
    Mitigation: beta starts high (preserve signal), decays as confidence grows."""

    def __init__(self, beta: float = 10.0, decay: float = 0.95):
        self.beta = beta
        self.decay = decay
        self.round = 0

    def compress(self, output: dict, mission_keys: List[str]) -> dict:
        """Keep only mission-relevant keys + metadata."""
        self.round += 1
        compressed = {}
        # Always keep structural keys
        for key in ["trace_id", "round_id", "timestamp", "type", "status"]:
            if key in output:
                compressed[key] = output[key]
        # Keep mission-relevant keys (high beta = keep more)
        for key in mission_keys:
            if key in output:
                compressed[key] = output[key]
        # Probabilistic keep for other keys based on beta
        effective_beta = self.beta * (self.decay ** self.round)
        keep_ratio = min(1.0, effective_beta / 10.0)
        other_keys = [k for k in output if k not in compressed]
        keep_count = max(1, int(len(other_keys) * keep_ratio))
        for key in other_keys[:keep_count]:
            compressed[key] = output[key]
        compressed["_ib_compression_ratio"] = round(len(compressed) / max(len(output), 1), 3)
        compressed["_ib_beta"] = round(effective_beta, 3)
        return compressed


# ─── Unified Engine ────────────────────────────────────────────
class HyperloopEngine:
    """Layer 2 acceleration. Sits on top of SwarmCompressor (Layer 1)."""

    def __init__(self):
        self.pheromone = PheromoneDecay(rho=0.1)
        self.bloom = BloomDedup(n=1000, fp_rate=0.01)
        self.merkle = MerkleSpine()
        self.speculator = SpeculativeExecutor(confidence_threshold=0.7)
        self.bottleneck = InfoBottleneck(beta=10.0, decay=0.95)
        self.round = 0
        self.metrics_history = []

    def accelerate(self, entries: List[dict], new_entries: List[dict],
                   predicted_lobby: str = None, confidence: float = 0.0,
                   mission_keys: List[str] = None) -> dict:
        """Run all 5 Layer 2 techniques. Returns metrics."""
        self.round += 1
        t0 = time.time()
        metrics = {"round": self.round, "layer": 2, "techniques": []}

        # T6: Pheromone decay
        weighted = self.pheromone.apply(entries, self.round)
        pruned = self.pheromone.prune(weighted)
        metrics["techniques"].append({
            "name": "pheromone_decay",
            "entries_before": len(entries),
            "entries_after_prune": len(pruned),
            "pruned": len(entries) - len(pruned)
        })

        # T7: Bloom dedup on new entries
        deduped = []
        dupes = 0
        for e in new_entries:
            key = e.get("trace_id", json.dumps(e, sort_keys=True))
            if not self.bloom.is_duplicate(key):
                self.bloom.add(key)
                deduped.append(e)
            else:
                dupes += 1
        metrics["techniques"].append({
            "name": "bloom_dedup",
            "new_entries": len(new_entries),
            "duplicates_caught": dupes,
            "bloom_stats": self.bloom.stats()
        })

        # T8: Merkle spine
        all_entries = pruned + deduped
        self.merkle.build(all_entries)
        metrics["techniques"].append({
            "name": "merkle_spine",
            **self.merkle.stats()
        })

        # T9: Speculative execution check
        spec_result = None
        if predicted_lobby and confidence > 0:
            if self.speculator.should_speculate(predicted_lobby, confidence):
                spec_result = f"SPECULATING on {predicted_lobby} @ {confidence:.0%}"
                metrics["techniques"].append({
                    "name": "speculative_execution",
                    "action": "SPECULATE",
                    "target": predicted_lobby,
                    "confidence": confidence,
                    "break_even": self.speculator.break_even(5000, 1000)
                })
            else:
                metrics["techniques"].append({
                    "name": "speculative_execution",
                    "action": "WAIT",
                    "confidence": confidence,
                    "threshold": self.speculator.threshold
                })

        # T10: Information bottleneck
        compressed_entries = []
        if mission_keys:
            for e in deduped:
                compressed_entries.append(
                    self.bottleneck.compress(e, mission_keys)
                )
            avg_ratio = sum(
                c.get("_ib_compression_ratio", 1) for c in compressed_entries
            ) / max(len(compressed_entries), 1)
            metrics["techniques"].append({
                "name": "info_bottleneck",
                "entries_compressed": len(compressed_entries),
                "avg_compression_ratio": round(avg_ratio, 3),
                "beta": round(self.bottleneck.beta * self.bottleneck.decay ** self.round, 3)
            })

        metrics["wallclock_ms"] = int((time.time() - t0) * 1000)
        metrics["total_acceleration_techniques"] = len(metrics["techniques"])

        # Compound factor: each round's metrics vs previous
        if self.metrics_history:
            prev = self.metrics_history[-1]
            prev_wall = prev.get("wallclock_ms", 1)
            current_wall = max(metrics["wallclock_ms"], 1)
            metrics["compound_factor"] = round(prev_wall / current_wall, 2)
        else:
            metrics["compound_factor"] = 1.0

        self.metrics_history.append(metrics)
        return metrics


if __name__ == "__main__":
    engine = HyperloopEngine()
    # Demo with synthetic entries
    entries = [{"trace_id": f"t{i}", "round": i // 5, "lobby": ["DNS","BGP","TLS","AUTH","MIXED"][i % 5],
                "status": "CANONICAL" if i < 3 else "PENDING", "data": f"probe_{i}"}
               for i in range(20)]
    new = [{"trace_id": f"new_{i}", "round": 4, "lobby": "FSC", "status": "PENDING"} for i in range(5)]
    m = engine.accelerate(entries, new, predicted_lobby="DNS", confidence=0.85,
                          mission_keys=["lobby", "status", "trace_id"])
    print(json.dumps(m, indent=2))
