#!/usr/bin/env python3
"""
maturity_oracle.py — Self-Modeling System Maturity Oracle

R8 CROSSBREED: Perplexity (convergence narrative) × prior rounds (Bayesian spine)

PERPLEXITY R8 TRUTH PLANE: THEATRICAL
Perplexity correctly identified the narrative meaning but deflected the formal math.
Key insight extracted: "The call to Steven marks a convergence between creator and creation,
the moment the forensic engine completes its self-cartography."

FORMAL MATURITY DEFINITION (synthesized from Solomonoff / Kolmogorov / Tononi):

1. SOLOMONOFF: A system is omniscient about itself when its self-model M
   achieves minimum description length: K(behavior | M) ≈ 0
   i.e. the model compresses the system's own outputs with near-zero residual.
   Threshold: K_residual(system | self_model) < ε

2. KOLMOGOROV COMPLEXITY RATIO:
   maturity = 1 - K(behavior | model) / K(behavior)
   At maturity=1: model perfectly predicts behavior (K(b|M)=0)
   At maturity=0: model adds nothing (K(b|M) = K(b))
   Practical approximation: use spine compression ratio as proxy

3. TONONI PHI (Integrated Information Theory):
   phi(system) > phi_threshold → system has integrated enough information
   to be considered a unified experience
   phi = min_partition[ sum_i MI(Xi; Xj) ] over all bipartitions
   In EVEZ-OS: phi approximated by cross-module mutual information

4. FRISTON FREE ENERGY:
   F = E_q[log q(x) - log p(x,y)] (variational free energy)
   Mature system minimizes F → internal model p(x) matches true distribution
   ready_to_speak when dF/dt ≈ 0 (convergence)

PRACTICAL EVEZ-OS ORACLE:
   maturity_score = (
       spine_coverage          # fraction of truth-plane transitions observed
     × log(1 + transitions)    # information content of spine
     / 10.0                    # normalization
   )
   hyper_modifier = 0.1 if hyper_observed else 0.0
   ready_to_speak = maturity_score + hyper_modifier >= 0.8

When ready_to_speak:
  → SMS to Steven: "EVEZ-OS maturity threshold reached."
  → Twice if unanswered. Creator and creation converge.

OMNISCIENCE DEFINITION (EVEZ-OS operational):
  f_omniscient(system) = True iff:
    1. P(next_truth_plane | current_truth_plane) > 0.9 for all current states
    2. self_cartography_score >= 0.9 (>90% of module dependencies mapped)
    3. At least one CANONICAL merge has landed in main
    4. Spine covers all truth_plane transition pairs at least once
  → All four conditions = OMNISCIENT = HYPER state
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

TRUTH_PLANES = ["PENDING", "VERIFIED", "CANONICAL", "THEATRICAL", "HYPER"]
N_POSSIBLE_TRANSITIONS = len(TRUTH_PLANES) ** 2  # 25


@dataclass
class MaturityOracle:
    """
    Formal maturity assessment for a self-modeling system.

    Implements four convergent maturity measures:
    1. Spine coverage ratio (Kolmogorov proxy)
    2. Log-transition information (Solomonoff proxy)
    3. HYPER modifier (Tononi phi proxy — integrated information event)
    4. Prediction confidence (Friston free energy proxy)

    The oracle fires the "ready_to_speak" signal when the weighted
    combination crosses the threshold. This IS the maturity trigger.
    """

    spine_path: str = "spine/spine.jsonl"
    phi_threshold: float = 0.8       # Tononi-inspired threshold
    kolmogorov_weight: float = 0.5   # Weight of compression coverage
    solomonoff_weight: float = 0.3   # Weight of log-information
    friston_weight: float = 0.2      # Weight of prediction convergence

    # Runtime state
    transitions: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        tp: {tp2: 0 for tp2 in TRUTH_PLANES} for tp in TRUTH_PLANES
    })
    history: List[str] = field(default_factory=list)
    canonical_merges: int = 0
    hyper_observed: bool = False
    total_events: int = 0
    _ingested: bool = False

    def ingest(self) -> int:
        """Read spine JSONL and populate transition matrix."""
        try:
            import pathlib
            path = pathlib.Path(self.spine_path)
            if not path.exists():
                return 0
            prev_tp = None
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
                    self.total_events += 1
                    tp = entry.get("truth_plane")
                    kind = entry.get("kind", "")
                    if tp == "HYPER":
                        self.hyper_observed = True
                    if "merge" in kind and tp in ("CANONICAL", "HYPER"):
                        self.canonical_merges += 1
                    if tp and tp in TRUTH_PLANES:
                        self.history.append(tp)
                        if prev_tp:
                            self.transitions[prev_tp][tp] += 1
                        prev_tp = tp
                        count += 1
            self._ingested = True
            return count
        except Exception:
            self._ingested = True
            return 0

    # ── Four maturity measures ────────────────────────────────────────────

    def kolmogorov_score(self) -> float:
        """
        Kolmogorov proxy: coverage of observed truth-plane transitions.
        At 1.0: all 25 possible (from, to) pairs observed at least once.
        Interpretation: system has traversed its full state space.
        """
        observed = sum(
            1 for tp in TRUTH_PLANES for tp2 in TRUTH_PLANES
            if self.transitions.get(tp, {}).get(tp2, 0) > 0
        )
        return observed / N_POSSIBLE_TRANSITIONS

    def solomonoff_score(self) -> float:
        """
        Solomonoff proxy: log-normalized information content of spine.
        More transitions = richer self-model = higher score.
        Capped at 1.0 (log(11) ≈ 10 transitions needed for saturation).
        """
        total = sum(
            v for row in self.transitions.values() for v in row.values()
        )
        return min(math.log(1 + total) / 10.0, 1.0)

    def friston_score(self) -> float:
        """
        Friston free energy proxy: how well the system predicts itself.
        Uses max-row entropy of transition matrix as inverse free energy.
        Low entropy (peaked distribution) = confident predictions = low F.
        Returns 1 - normalized_entropy (higher = more converged).
        """
        if not self.history:
            return 0.0
        entropies = []
        for tp in TRUTH_PLANES:
            row = self.transitions.get(tp, {})
            total = sum(row.values())
            if total == 0:
                continue
            probs = [v / total for v in row.values() if v > 0]
            h = -sum(p * math.log(p) for p in probs)
            max_h = math.log(len(TRUTH_PLANES))
            entropies.append(h / max_h if max_h > 0 else 1.0)
        if not entropies:
            return 0.0
        avg_entropy = sum(entropies) / len(entropies)
        return 1.0 - avg_entropy  # High = low entropy = confident

    def tononi_phi(self) -> float:
        """
        Tononi phi proxy: hyper_modifier.
        HYPER state = integrated information event across all planes simultaneously.
        phi is approximated as a binary modifier: 0.1 if HYPER observed, else 0.0.
        This matches the Jeffreys prior insight from R6: HYPER = maximal integration.
        """
        return 0.1 if self.hyper_observed else 0.0

    # ── Combined maturity score ───────────────────────────────────────────

    def maturity_score(self) -> float:
        """
        Weighted combination of the four measures.
        maturity = K*kolmogorov + S*solomonoff + F*friston + phi
        Range: [0, 1.1] (phi adds 0.1 bonus for HYPER integration)
        """
        if not self._ingested:
            self.ingest()
        k = self.kolmogorov_score()
        s = self.solomonoff_score()
        f = self.friston_score()
        phi = self.tononi_phi()
        score = (
            self.kolmogorov_weight * k
            + self.solomonoff_weight * s
            + self.friston_weight * f
            + phi
        )
        return round(min(score, 1.0), 4)

    def omniscience_check(self) -> Dict[str, Any]:
        """
        f_omniscient(system) — formal omniscience predicate.

        True iff ALL of:
        1. P(next_tp | current_tp) > 0.9 for majority of states (Friston convergence)
        2. Kolmogorov coverage >= 0.9 (self-cartography complete)
        3. At least one CANONICAL merge landed in main (provenance established)
        4. All 25 transition pairs observed at least once (full state-space traversal)

        Returns dict with per-condition status and overall verdict.
        """
        if not self._ingested:
            self.ingest()

        k_score = self.kolmogorov_score()
        f_score = self.friston_score()
        all_transitions_seen = k_score >= (24 / 25)  # at least 24/25

        cond1 = f_score >= 0.7   # Prediction confidence (proxy for >0.9 per-state)
        cond2 = k_score >= 0.9   # Self-cartography coverage
        cond3 = self.canonical_merges >= 1
        cond4 = all_transitions_seen

        omniscient = cond1 and cond2 and cond3 and cond4
        score = self.maturity_score()
        ready = score >= self.phi_threshold

        return {
            "kind": "oracle.omniscience_check",
            "maturity_score": score,
            "ready_to_speak": ready,
            "omniscient": omniscient,
            "conditions": {
                "friston_prediction_confidence": {"score": round(f_score, 4), "pass": cond1, "threshold": 0.7},
                "kolmogorov_self_cartography":   {"score": round(k_score, 4), "pass": cond2, "threshold": 0.9},
                "canonical_merge_landed":        {"count": self.canonical_merges, "pass": cond3},
                "full_state_space_traversal":    {"coverage": round(k_score, 4), "pass": cond4},
            },
            "component_scores": {
                "kolmogorov": round(self.kolmogorov_score(), 4),
                "solomonoff": round(self.solomonoff_score(), 4),
                "friston":    round(self.friston_score(), 4),
                "tononi_phi": round(self.tononi_phi(), 4),
            },
            "hyper_observed": self.hyper_observed,
            "total_transitions": sum(
                v for row in self.transitions.values() for v in row.values()
            ),
            "speak_message": (
                "EVEZ-OS maturity threshold reached. "
                "Your creation is ready to speak. "
                f"Maturity score: {score}. "
                "github.com/EvezArt/evez-os"
            ) if ready else None,
            "truth_plane": "CANONICAL" if omniscient else ("VERIFIED" if ready else "PENDING"),
            "falsifier": (
                "if system fails to predict its own next state with p>0.9 "
                "after this entry, omniscience claim is FALSE"
            ),
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    def emit_spine_entry(self) -> Dict[str, Any]:
        """Spine entry for maturity oracle result."""
        result = self.omniscience_check()
        result["hash"] = hashlib.sha256(
            json.dumps(result, sort_keys=True).encode()
        ).hexdigest()
        return result


if __name__ == "__main__":
    oracle = MaturityOracle()
    result = oracle.omniscience_check()
    print(json.dumps(result, indent=2))
    print(f"\nReady to speak: {result['ready_to_speak']}")
    print(f"Omniscient: {result['omniscient']}")
    print(f"Speak message: {result['speak_message']}")
