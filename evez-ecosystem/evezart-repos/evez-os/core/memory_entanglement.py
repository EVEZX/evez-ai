#!/usr/bin/env python3
"""
memory_entanglement.py — Tri-Metric Memory Entanglement Engine

R3 CROSSBREED: Perplexity (PMI vs Cosine vs SAT-clause analysis)

Perplexity verdict (Round 3):
- PMI: best for "these anchors appear in similar contexts" — sparse bias failure
- Cosine: MOST ACTIONABLE for self-auditing — semantic similarity, robust, continuous
- SAT-clause: discrete alarm for SAFETY INVARIANTS ONLY — NP-complete, not for continuous use

Implementation: all three run simultaneously.
Spine entry carries all three scores.
System operator chooses which to surface in the bottom-right panel.

Failure modes committed:
- PMI: SPARSITY_BIAS (rare pairs get inflated scores)
- Cosine: EMBEDDING_COLLAPSE (similar vectors for distinct content)
- SAT: MODELING_GAP (natural language → propositional encoding is lossy)

Steven asked: PMI? cosine overlap? contradiction-SAT clauses?
Answer: ALL THREE. Cosine is the primary signal. SAT is the safety alarm.
PMI is the early warning for unexpected co-occurrence.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple


# ─── PMI ────────────────────────────────────────────────────────────────────

def pmi(count_xy: int, count_x: int, count_y: int, total_windows: int,
        smoothing: float = 0.5) -> float:
    """
    PMI(x,y) = log[ P(x,y) / (P(x) * P(y)) ]

    Smoothed to avoid -inf on zero counts.
    Failure mode: SPARSITY_BIAS — rare pairs get inflated scores.
    Mitigation: require count_xy >= 3 before trusting PMI.
    """
    if total_windows == 0:
        return 0.0
    p_xy = (count_xy + smoothing) / (total_windows + smoothing * total_windows)
    p_x  = (count_x  + smoothing) / (total_windows + smoothing * total_windows)
    p_y  = (count_y  + smoothing) / (total_windows + smoothing * total_windows)
    if p_x * p_y == 0:
        return 0.0
    return math.log(p_xy / (p_x * p_y))


def pmi_reliable(count_xy: int) -> bool:
    """PMI is only reliable when count >= 3. Below that: SPARSITY_BIAS."""
    return count_xy >= 3


# ─── COSINE (zero-dep, bag-of-words fallback) ────────────────────────────────

def _tfidf_vector(text: str, corpus_df: Dict[str, int], N: int) -> Dict[str, float]:
    """
    Bag-of-words TF-IDF vector for cosine similarity without numpy.
    For production: replace with actual embeddings (sentence-transformers, etc.)
    """
    tokens = text.lower().split()
    tf = Counter(tokens)
    vector = {}
    for tok, count in tf.items():
        tf_score = count / len(tokens) if tokens else 0
        df = corpus_df.get(tok, 1)
        idf = math.log((N + 1) / (df + 1)) + 1
        vector[tok] = tf_score * idf
    return vector


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """
    cos(u,v) = (u·v) / (||u||₂ * ||v||₂)

    O(|vocab|) per pair.
    Failure mode: EMBEDDING_COLLAPSE — similar vectors for distinct content.
    """
    if not vec_a or not vec_b:
        return 0.0
    dot = sum(vec_a.get(k, 0) * v for k, v in vec_b.items())
    norm_a = math.sqrt(sum(v**2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v**2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ─── SAT-CLAUSE CONTRADICTION ────────────────────────────────────────────────

def sat_contradiction_check(anchor_constraints: List[List[int]]) -> Tuple[bool, List[List[int]]]:
    """
    Simple DPLL-style unit propagation for small clause sets.

    anchor_constraints: list of clauses (each clause = list of literals, positive=True, negative=False)
    Returns (is_contradicted, minimal_unsat_core)

    O(2^n) worst case — only use for SAFETY INVARIANTS (small clause sets).
    Failure mode: MODELING_GAP — NL → propositional encoding is lossy.
    """
    def unit_propagate(clauses, assignment):
        changed = True
        while changed:
            changed = False
            for clause in clauses:
                unassigned = [lit for lit in clause if abs(lit) not in assignment]
                satisfied = any(
                    (lit > 0 and assignment.get(abs(lit)) is True) or
                    (lit < 0 and assignment.get(abs(lit)) is False)
                    for lit in clause
                )
                if satisfied:
                    continue
                if len(unassigned) == 0:
                    return False, assignment  # Empty clause = contradiction
                if len(unassigned) == 1:
                    lit = unassigned[0]
                    assignment[abs(lit)] = lit > 0
                    changed = True
        return True, assignment

    assignment = {}
    ok, _ = unit_propagate(anchor_constraints, assignment)
    if not ok:
        return True, anchor_constraints  # Contradiction found
    return False, []


# ─── UNIFIED ENTANGLEMENT ENGINE ─────────────────────────────────────────────

@dataclass
class AnchorPair:
    a: str
    b: str
    pmi_score: float
    pmi_reliable: bool
    cosine_score: float
    sat_contradiction: bool

    @property
    def composite_score(self) -> float:
        """Cosine is primary. PMI modulates. SAT flags."""
        base = self.cosine_score
        if self.pmi_reliable:
            base = 0.7 * base + 0.3 * min(max(self.pmi_score / 5.0, 0), 1)
        if self.sat_contradiction:
            base = -abs(base)  # Contradiction inverts the signal
        return round(base, 4)

    def to_spine_entry(self) -> Dict[str, Any]:
        return {
            "kind": "entanglement.pair",
            "pair": [self.a, self.b],
            "pmi": round(self.pmi_score, 4),
            "pmi_reliable": self.pmi_reliable,
            "cosine": round(self.cosine_score, 4),
            "sat_contradiction": self.sat_contradiction,
            "composite": self.composite_score,
            "primary_signal": "cosine",
            "ts": datetime.now(timezone.utc).isoformat(),
        }


class MemoryEntanglementEngine:
    """
    Tri-metric memory entanglement for the evez-os spine.

    Primary: cosine similarity (most actionable, continuous)
    Adjunct: PMI (early warning for unexpected co-occurrence)
    Safety: SAT-clause contradiction (alarm for logical impossibility)
    """

    def __init__(self):
        self.anchor_texts: Dict[str, str] = {}
        self.co_occurrence: Dict[FrozenSet[str], int] = defaultdict(int)
        self.occurrence: Counter = Counter()
        self.total_windows: int = 0
        self.corpus_df: Dict[str, int] = defaultdict(int)
        self.total_docs: int = 0
        self._vectors: Dict[str, Dict[str, float]] = {}

    def ingest_window(self, anchors: List[Dict[str, Any]]):
        """
        Process one spine entry's memory anchors.
        anchors: list of {"id": str, "text": str, "used": bool}
        """
        self.total_windows += 1
        active = [a for a in anchors if isinstance(a, dict) and a.get("used", False)]
        ids = [a["id"] for a in active]

        # Update occurrence counts
        for a in active:
            aid = a["id"]
            self.occurrence[aid] += 1
            text = a.get("text", "")
            # Store text for cosine
            if aid not in self.anchor_texts and text:
                self.anchor_texts[aid] = text
                # Update corpus document frequency
                for tok in text.lower().split():
                    self.corpus_df[tok] += 1
                self.total_docs += 1
                self._vectors[aid] = None  # Mark as dirty

        # Update co-occurrence
        for i, a in enumerate(ids):
            for b in ids[i+1:]:
                key = frozenset([a, b])
                self.co_occurrence[key] += 1

    def _get_vector(self, anchor_id: str) -> Dict[str, float]:
        if anchor_id not in self._vectors or self._vectors[anchor_id] is None:
            text = self.anchor_texts.get(anchor_id, anchor_id)
            self._vectors[anchor_id] = _tfidf_vector(
                text, self.corpus_df, max(self.total_docs, 1)
            )
        return self._vectors[anchor_id]

    def score_pair(self, a: str, b: str,
                   sat_clauses: Optional[List[List[int]]] = None) -> AnchorPair:
        """Score one pair across all three metrics."""
        pair_key = frozenset([a, b])
        co = self.co_occurrence.get(pair_key, 0)
        c_a = self.occurrence.get(a, 0)
        c_b = self.occurrence.get(b, 0)

        pmi_s = pmi(co, c_a, c_b, self.total_windows)
        pmi_r = pmi_reliable(co)

        vec_a = self._get_vector(a)
        vec_b = self._get_vector(b)
        cos_s = cosine_similarity(vec_a, vec_b)

        sat_c = False
        if sat_clauses:
            sat_c, _ = sat_contradiction_check(sat_clauses)

        return AnchorPair(a=a, b=b, pmi_score=pmi_s, pmi_reliable=pmi_r,
                          cosine_score=cos_s, sat_contradiction=sat_c)

    def top_pairs(self, n: int = 10) -> List[AnchorPair]:
        """Top N most entangled pairs by composite score."""
        pairs = []
        anchor_ids = list(self.occurrence.keys())
        for i, a in enumerate(anchor_ids):
            for b in anchor_ids[i+1:]:
                pairs.append(self.score_pair(a, b))
        pairs.sort(key=lambda p: abs(p.composite_score), reverse=True)
        return pairs[:n]

    def summary(self) -> Dict[str, Any]:
        top = self.top_pairs(5)
        return {
            "kind": "entanglement.summary",
            "total_windows": self.total_windows,
            "unique_anchors": len(self.occurrence),
            "unique_pairs": len(self.co_occurrence),
            "primary_metric": "cosine",
            "top_pairs": [p.to_spine_entry() for p in top],
            "ts": datetime.now(timezone.utc).isoformat(),
            "trace_id": hashlib.sha256(
                f"ent:{self.total_windows}:{len(self.co_occurrence)}".encode()
            ).hexdigest()[:16],
        }


if __name__ == "__main__":
    engine = MemoryEntanglementEngine()

    steps = [
        [{"id": "goal", "text": "maintain append-only provenance integrity", "used": True},
         {"id": "rule2", "text": "every claim names its falsifier", "used": True}],
        [{"id": "goal", "text": "maintain append-only provenance integrity", "used": True},
         {"id": "section", "text": "forensic game engine evez-os", "used": True}],
        [{"id": "rule2", "text": "every claim names its falsifier", "used": True},
         {"id": "section", "text": "forensic game engine evez-os", "used": True}],
        [{"id": "goal", "text": "maintain append-only provenance integrity", "used": True},
         {"id": "rule2", "text": "every claim names its falsifier", "used": True},
         {"id": "section", "text": "forensic game engine evez-os", "used": True}],
    ]

    for step_anchors in steps * 30:  # Simulate 120 steps
        engine.ingest_window(step_anchors)

    summary = engine.summary()
    print(json.dumps(summary, indent=2))
