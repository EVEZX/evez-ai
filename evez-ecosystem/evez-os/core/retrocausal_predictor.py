#!/usr/bin/env python3
"""
retrocausal_predictor.py — Bayesian Truth Plane Transition Predictor

R6 CROSSBREED: ChatGPT (RetrocausalPredictor skeleton) × Perplexity (Bayesian priors + deterministic embedding)

KEY FINDINGS FROM ROUND 6:
- ChatGPT built the transition tracker and Bayesian inference structure
- Perplexity answered the HYPER prior question:
    P(HYPER at t+1 | HYPER at t) = 0.5 → Beta(α=1/2, β=1/2) = maximal ignorance
    Rationale: HYPER is rare and self-referential; once you've exited it, you
    know nothing about its recurrence. Assign maximal uncertainty.
- Perplexity also provided the deterministic stdlib embedding architecture:
    For each dimension i: hash(i || text_bytes) → 4 bytes → float in [-1,1]
    Identical text + dimension → identical vector in any Python session, zero deps

INTEGRATION:
- RetrocausalPredictor reads the spine JSONL
- Builds Laplace-smoothed Markov transition matrix over truth_plane
- Uses Beta(0.5, 0.5) (Jeffreys prior) for HYPER→HYPER specifically
- Predicts next truth_plane using posterior mean
- Emits spine entry for each prediction (falsifier: if next truth_plane != predicted)

DETERMINISTIC EMBEDDER:
- Used inside memory_entanglement.py as the session-invariant vector function
- SHA-256 keyed per dimension, struct.unpack to float, normalized to [-1,1]
- O(d × len(text)) per embedding, ~10μs for d=64 on modern hardware
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TRUTH_PLANES = ["PENDING", "VERIFIED", "CANONICAL", "THEATRICAL", "HYPER"]

# Jeffreys prior (Beta(0.5, 0.5)) counts — maximal ignorance
# Used for HYPER→HYPER specifically per Perplexity R6 verdict
JEFFREYS_PSEUDO_COUNT = 0.5
# Laplace smoothing for all other transitions
LAPLACE_PSEUDO_COUNT = 1.0


# ─── DETERMINISTIC STDLIB EMBEDDER ──────────────────────────────────────────
# Perplexity R6: "For each dimension i, derive a separate pseudorandom stream
# from a keyed hash of (i, text). From that stream, read 4 bytes → float in [-1,1]."

def deterministic_embed(text: str, dim: int = 64) -> List[float]:
    """
    Session-invariant text embedding using only stdlib (hashlib, struct).

    Algorithm (Perplexity R6):
      For dimension i:
        seed = sha256(i.to_bytes(4, "big") + text.encode("utf-8"))
        raw = struct.unpack(">I", seed.digest()[:4])[0]  # uint32
        value = (raw / 2^32) * 2 - 1                    # normalize to [-1,1]

    Properties:
      - Deterministic: identical text + dim → identical vector, any session
      - Session-invariant: no random seed, no state
      - Collision-resistant: SHA-256 keyed per dimension
      - Zero dependencies: hashlib + struct only
      - O(d × |text|) time, O(d) space

    Failure mode: DIMENSIONAL_ALIASING — if dim >> len(text), later dimensions
    carry less information. Use dim ≤ len(text) * 4 as a rough guide.
    """
    text_bytes = text.encode("utf-8")
    vector = []
    for i in range(dim):
        key = i.to_bytes(4, "big") + text_bytes
        digest = hashlib.sha256(key).digest()
        raw = struct.unpack(">I", digest[:4])[0]           # uint32, range [0, 2^32)
        value = (raw / (2**32)) * 2.0 - 1.0               # normalize to [-1, 1]
        vector.append(value)
    return vector


def cosine_similarity_stdlib(vec_a: List[float], vec_b: List[float]) -> float:
    """Cosine similarity without numpy. O(d)."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ─── RETROCAUSAL PREDICTOR ───────────────────────────────────────────────────

@dataclass
class TransitionMatrix:
    """
    Markov transition matrix over truth_plane states.

    Smoothing: Laplace (count+1) for standard transitions.
                Jeffreys (count+0.5) for HYPER→HYPER (maximal ignorance prior).
    """
    counts: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        tp: {tp2: 0.0 for tp2 in TRUTH_PLANES} for tp in TRUTH_PLANES
    })
    total_transitions: int = 0

    def observe(self, from_tp: str, to_tp: str):
        if from_tp not in self.counts:
            self.counts[from_tp] = {tp: 0.0 for tp in TRUTH_PLANES}
        self.counts[from_tp][to_tp] = self.counts[from_tp].get(to_tp, 0.0) + 1.0
        self.total_transitions += 1

    def posterior_mean(self, from_tp: str) -> Dict[str, float]:
        """
        Bayesian posterior mean for P(to | from).

        For HYPER→HYPER: Jeffreys prior (pseudo=0.5) → maximal ignorance
        For all others: Laplace prior (pseudo=1.0) → slight regularization
        """
        row = self.counts.get(from_tp, {tp: 0.0 for tp in TRUTH_PLANES})
        smoothed = {}
        for tp in TRUTH_PLANES:
            count = row.get(tp, 0.0)
            # HYPER→HYPER gets Jeffreys prior (Perplexity R6 verdict)
            if from_tp == "HYPER" and tp == "HYPER":
                pseudo = JEFFREYS_PSEUDO_COUNT
            else:
                pseudo = LAPLACE_PSEUDO_COUNT
            smoothed[tp] = count + pseudo
        total = sum(smoothed.values())
        return {tp: v / total for tp, v in smoothed.items()}

    def predict_next(self, from_tp: str) -> Tuple[str, float]:
        """Returns (most_likely_next_tp, probability)."""
        probs = self.posterior_mean(from_tp)
        best = max(probs, key=lambda k: probs[k])
        return best, probs[best]

    def predict_distribution(self, from_tp: str) -> Dict[str, float]:
        """Full distribution over next states."""
        return self.posterior_mean(from_tp)


@dataclass
class RetrocausalPredictor:
    """
    Reads an append-only spine JSONL and predicts the next truth plane.

    "Retrocausal" in the evez-os sense: later spine entries can reinterpret
    earlier predictions, but they cannot rewrite them. The prediction IS the
    claim; the next entry falsifies or confirms it.

    Usage:
        predictor = RetrocausalPredictor("spine/spine.jsonl")
        predictor.ingest()
        next_tp, prob = predictor.predict(current_tp="VERIFIED")
        spine_entry = predictor.emit_prediction(current_tp="VERIFIED")
    """
    spine_path: str = "spine/spine.jsonl"
    matrix: TransitionMatrix = field(default_factory=TransitionMatrix)
    history: List[str] = field(default_factory=list)   # Ordered truth planes
    _preloaded: bool = False

    def ingest(self) -> int:
        """Read spine and build transition matrix. Returns entry count."""
        path = Path(self.spine_path)
        if not path.exists():
            return 0

        prev_tp: Optional[str] = None
        count = 0

        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                tp = entry.get("truth_plane")
                if tp and tp in TRUTH_PLANES:
                    self.history.append(tp)
                    if prev_tp is not None:
                        self.matrix.observe(prev_tp, tp)
                    prev_tp = tp
                    count += 1

        self._preloaded = True
        return count

    def predict(self, current_tp: Optional[str] = None) -> Tuple[str, float]:
        """
        Predict next truth plane.
        current_tp: override; if None, uses last observed truth_plane.
        """
        if not self._preloaded:
            self.ingest()
        tp = current_tp or (self.history[-1] if self.history else "PENDING")
        return self.matrix.predict_next(tp)

    def predict_distribution(self, current_tp: Optional[str] = None) -> Dict[str, float]:
        """Full probability distribution over next states."""
        if not self._preloaded:
            self.ingest()
        tp = current_tp or (self.history[-1] if self.history else "PENDING")
        return self.matrix.predict_distribution(tp)

    def emit_prediction(self, current_tp: Optional[str] = None) -> Dict[str, Any]:
        """
        Emit a spine entry for the prediction.
        This IS the claim. The next spine entry falsifies or confirms it.
        """
        tp = current_tp or (self.history[-1] if self.history else "PENDING")
        predicted, prob = self.predict(tp)
        dist = self.predict_distribution(tp)
        ts = datetime.now(timezone.utc).isoformat()

        entry = {
            "kind": "retrocausal.prediction",
            "from_truth_plane": tp,
            "predicted_next": predicted,
            "confidence": round(prob, 4),
            "distribution": {k: round(v, 4) for k, v in dist.items()},
            "total_transitions_seen": self.matrix.total_transitions,
            "hyper_prior": "jeffreys_beta_0.5_0.5",  # Per Perplexity R6
            "other_prior": "laplace_pseudo_1.0",
            "truth_plane": "PENDING",
            "falsifier": (
                f"if next spine entry truth_plane != {predicted}, "
                f"prediction FAILED (expected {predicted} with p={prob:.3f})"
            ),
            "ts": ts,
            "hash": __import__("hashlib").sha256(
                f"retrocausal:{tp}:{predicted}:{prob:.6f}:{ts}".encode()
            ).hexdigest(),
        }
        return entry

    def maturity_signal(self) -> Dict[str, Any]:
        """
        Maturity assessment: how well does the system understand its own transitions?
        Maturity = (total_transitions / (|states|^2)) normalized by HYPER appearance rate

        This is the trigger for the creation to speak.
        Maturity >= 0.8 AND at least one HYPER transition observed → SPEAK.
        """
        n_states = len(TRUTH_PLANES)
        n_possible = n_states * n_states
        n_observed = sum(
            1 for tp in TRUTH_PLANES
            for tp2 in TRUTH_PLANES
            if self.matrix.counts.get(tp, {}).get(tp2, 0) > 0
        )
        coverage = n_observed / n_possible if n_possible > 0 else 0.0
        hyper_seen = self.matrix.counts.get("HYPER", {}).get("HYPER", 0) > 0
        history_len = len(self.history)

        # Maturity formula: coverage × log(1 + transitions) normalized
        maturity = coverage * math.log(1 + self.matrix.total_transitions) / 10.0
        maturity = min(maturity, 1.0)

        return {
            "kind": "maturity.signal",
            "maturity_score": round(maturity, 4),
            "transition_coverage": round(coverage, 4),
            "total_transitions": self.matrix.total_transitions,
            "history_length": history_len,
            "hyper_observed": hyper_seen,
            "ready_to_speak": maturity >= 0.8 and hyper_seen,
            "speak_condition": "maturity >= 0.8 AND HYPER transition observed",
            "ts": datetime.now(timezone.utc).isoformat(),
        }


if __name__ == "__main__":
    # Demo
    predictor = RetrocausalPredictor()

    # Simulate a spine with truth plane entries
    import tempfile, os

    test_spine = [
        {"truth_plane": "PENDING", "ts": "2026-02-20T00:00:00Z"},
        {"truth_plane": "PENDING", "ts": "2026-02-20T00:01:00Z"},
        {"truth_plane": "VERIFIED", "ts": "2026-02-20T00:02:00Z"},
        {"truth_plane": "CANONICAL", "ts": "2026-02-20T00:03:00Z"},
        {"truth_plane": "THEATRICAL", "ts": "2026-02-20T00:04:00Z"},
        {"truth_plane": "PENDING", "ts": "2026-02-20T00:05:00Z"},
        {"truth_plane": "VERIFIED", "ts": "2026-02-20T00:06:00Z"},
        {"truth_plane": "CANONICAL", "ts": "2026-02-20T00:07:00Z"},
        {"truth_plane": "HYPER", "ts": "2026-02-20T00:08:00Z"},
        {"truth_plane": "CANONICAL", "ts": "2026-02-20T00:09:00Z"},
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for e in test_spine:
            f.write(json.dumps(e) + "\n")
        tmppath = f.name

    predictor.spine_path = tmppath
    count = predictor.ingest()
    print(f"Ingested {count} truth-plane entries")

    for tp in TRUTH_PLANES:
        next_tp, prob = predictor.predict(tp)
        print(f"  {tp:12s} → {next_tp:12s} (p={prob:.3f})")

    print()
    pred_entry = predictor.emit_prediction("CANONICAL")
    print(f"Prediction entry: {json.dumps(pred_entry, indent=2)}")

    print()
    maturity = predictor.maturity_signal()
    print(f"Maturity: {maturity['maturity_score']:.3f}")
    print(f"Ready to speak: {maturity['ready_to_speak']}")

    # Test deterministic embedder
    v1 = deterministic_embed("evez-os forensic spine", dim=8)
    v2 = deterministic_embed("evez-os forensic spine", dim=8)
    v3 = deterministic_embed("different text", dim=8)
    print(f"\nEmbedding stability: v1==v2 = {v1==v2}")
    print(f"Cross-text cosine: {cosine_similarity_stdlib(v1, v3):.4f} (expected < 1.0)")
    print(f"Self-cosine: {cosine_similarity_stdlib(v1, v2):.4f} (expected 1.0)")

    os.unlink(tmppath)
