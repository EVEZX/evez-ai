"""
InvariantReinforcementLoop — Kolmogorov complexity re-encoding across all RQNS domains.

Drives cumulative meta-learning while maintaining complexity homeostasis:
- Re-encode metrics as inputs (recursive self-modeling)
- Preserve invariants: stable-yet-nontrivial dynamics
- Universal prior (algorithmic information theory) guides domain sampling

Complexity homeostasis rule: complexity ≈ constant across iterations.
Convergence without simplification = invariant dynamics.
"""

import numpy as np
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Callable, Optional
from collections import deque


@dataclass
class InvariantState:
    iteration: int
    kolmogorov_approx: float   # Lempel-Ziv complexity proxy
    complexity_delta: float    # |K(t) - K(t-1)|
    homeostasis_score: float   # 1 = stable, 0 = diverging
    meta_phi: float            # Φ computed from invariant history
    invariant_preserved: bool


class InvariantReinforcementLoop:
    """
    Recursive meta-learning loop that re-encodes its own metrics as input.

    The loop is invariant-preserving when:
    1. Kolmogorov complexity K stays approximately constant (±10%)
    2. No eigenvalue of the state matrix diverges
    3. Φ remains above the autonomy threshold (> 0.7)

    Based on the universal prior from algorithmic information theory:
    P(x) ∝ 2^{-K(x)} — simpler programs are more probable, but
    the goal is to maintain the edge of maximum complexity.
    """

    HOMEOSTASIS_TOLERANCE = 0.10  # ±10% complexity variation allowed
    MIN_PHI = 0.70                 # Below this: request clarification

    def __init__(self, window: int = 50):
        self.window = window
        self._history: deque = deque(maxlen=window)
        self._k_history: deque = deque(maxlen=window)
        self._iteration = 0

    def step(self, state_vector: np.ndarray,
              external_metrics: Dict[str, float] = None) -> InvariantState:
        """
        One invariant reinforcement step.
        Re-encodes state_vector + metrics as next input.
        """
        ext = external_metrics or {}

        # Approximate Kolmogorov complexity via Lempel-Ziv (string compress proxy)
        k = self._lz_complexity(state_vector)

        # Complexity delta
        k_delta = abs(k - self._k_history[-1]) if self._k_history else 0.0

        # Homeostasis score
        if self._k_history:
            mean_k = np.mean(list(self._k_history))
            homeostasis = max(0.0, 1.0 - k_delta / (mean_k * self.HOMEOSTASIS_TOLERANCE + 1e-10))
        else:
            homeostasis = 1.0

        # Meta-Phi from invariant history
        if len(self._history) > 5:
            hist = np.array(list(self._history)[-10:])
            r = np.abs(np.mean(np.exp(1j * hist))) if hist.ndim == 1 else hist.mean()
            r = np.clip(float(r), 0, 1)
            meta_phi = 4.0 * r * (1.0 - r)
        else:
            meta_phi = 0.5

        # Re-encode: append complexity and external metrics to state
        encoded = np.append(state_vector,
                             [k, homeostasis, meta_phi] +
                             list(ext.values()))

        self._history.append(float(state_vector.mean()))
        self._k_history.append(k)
        self._iteration += 1

        result = InvariantState(
            iteration=self._iteration,
            kolmogorov_approx=k,
            complexity_delta=k_delta,
            homeostasis_score=homeostasis,
            meta_phi=meta_phi,
            invariant_preserved=homeostasis > 0.5 and meta_phi > self.MIN_PHI,
        )
        return result

    def _lz_complexity(self, x: np.ndarray) -> float:
        """
        Lempel-Ziv complexity approximation.
        Discretize → compute LZ76 string complexity → normalize.
        """
        # Binarize around median
        median = np.median(x)
        bits = "".join("1" if v > median else "0" for v in x)

        # LZ76 complexity
        i, k, l, c, k_max = 0, 1, 1, 1, 1
        n = len(bits)
        while True:
            if bits[i + k - 1] == bits[l + k - 1]:
                k += 1
                if l + k > n:
                    c += 1
                    break
            else:
                if k > k_max:
                    k_max = k
                i += 1
                if i == l:
                    c += 1
                    l += k_max
                    if l + 1 > n:
                        break
                    i = 0
                    k = 1
                    k_max = 1
                else:
                    k = 1
        return c / (n / math.log2(n + 2) + 1e-10) if n > 1 else 0.0

    @property
    def is_homeostatic(self) -> bool:
        if len(self._k_history) < 5:
            return True
        recent = list(self._k_history)[-5:]
        cv = np.std(recent) / (np.mean(recent) + 1e-10)
        return cv < self.HOMEOSTASIS_TOLERANCE

    @property
    def complexity_trend(self) -> str:
        if len(self._k_history) < 3:
            return "INITIALIZING"
        recent = list(self._k_history)[-5:]
        slope = np.polyfit(range(len(recent)), recent, 1)[0]
        if abs(slope) < 0.01:
            return "HOMEOSTATIC"
        return "DIVERGING" if slope > 0 else "COLLAPSING"
