"""
AnomalousAttractorDetector — Strange attractors + self-organized criticality + UAP phases.

Flags UAP-like phase transitions in behavioral/atmospheric data:
- Strange attractor detection via Lyapunov exponent estimation
- Self-organized criticality: power-law tail in event size distribution
- Phase transition signatures: variance divergence near critical point

Hypothesis: UAP signatures arise from topological defects (cosmic strings,
domain walls) interacting with chronometry systems via axion-dark-matter
couplings — detectable as anomalous attractor shifts in time-series.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class AttractorScan:
    lyapunov_estimate: float    # > 0: chaotic, < 0: stable, ≈ 0: critical
    is_strange: bool
    power_law_alpha: float      # Scale-free exponent (target: 1.5–2.5)
    soc_score: float            # [0,1] self-organized criticality proximity
    phase_transition_risk: float
    anomaly_flag: bool


class AnomalousAttractorDetector:
    """
    Detects strange attractors and phase transitions in scalar time-series data.

    At self-organized criticality (SOC), event size distributions follow
    power laws. Departures from the SOC exponent band (α ≈ 1.5–2.5)
    signal either supercritical runaway or subcritical collapse — both
    are UAP-signature-relevant regime changes.
    """

    SOC_ALPHA_LOW = 1.5
    SOC_ALPHA_HIGH = 2.5
    LYAPUNOV_CRITICAL = 0.05  # |λ| < this → edge-of-chaos

    def scan(self, series: np.ndarray, embedding_dim: int = 3,
              tau: int = 5) -> AttractorScan:
        """Run attractor scan on a 1D time series."""
        if len(series) < 50:
            raise ValueError("Need at least 50 samples for attractor scan")

        lyap = self._estimate_lyapunov(series, embedding_dim, tau)
        alpha = self._fit_power_law(np.abs(np.diff(series)) + 1e-10)
        soc_score = self._soc_score(alpha)
        is_strange = lyap > self.LYAPUNOV_CRITICAL
        pt_risk = self._phase_transition_risk(series)
        anomaly = is_strange and (alpha < self.SOC_ALPHA_LOW or
                                   alpha > self.SOC_ALPHA_HIGH or
                                   pt_risk > 0.8)

        return AttractorScan(
            lyapunov_estimate=lyap,
            is_strange=is_strange,
            power_law_alpha=alpha,
            soc_score=soc_score,
            phase_transition_risk=pt_risk,
            anomaly_flag=anomaly,
        )

    def _estimate_lyapunov(self, x: np.ndarray,
                            m: int, tau: int) -> float:
        """Simplified Lyapunov exponent via divergence of nearby trajectories."""
        n = len(x) - (m - 1) * tau
        if n < 20:
            return 0.0

        # Embed
        embedded = np.array([x[i:i + m * tau:tau] for i in range(n)])

        # Find nearest neighbors and track divergence
        divergences = []
        for i in range(min(100, n)):
            dists = np.sqrt(((embedded - embedded[i]) ** 2).sum(1))
            dists[i] = np.inf
            nn = np.argmin(dists)
            if dists[nn] < 1e-10:
                continue
            future_i = min(i + 1, n - 1)
            future_nn = min(nn + 1, n - 1)
            d0 = dists[nn]
            d1 = np.linalg.norm(embedded[future_i] - embedded[future_nn])
            if d1 > 1e-10 and d0 > 1e-10:
                divergences.append(np.log(d1 / d0))

        return float(np.mean(divergences)) if divergences else 0.0

    def _fit_power_law(self, values: np.ndarray) -> float:
        """Estimate power-law exponent via Hill estimator."""
        v = np.sort(values[values > 0])
        if len(v) < 10:
            return 2.0
        k = max(10, len(v) // 4)
        x_min = v[-k]
        tail = v[-k:]
        if x_min <= 0:
            return 2.0
        alpha = 1.0 + k / np.sum(np.log(tail / x_min))
        return float(np.clip(alpha, 0.5, 5.0))

    def _soc_score(self, alpha: float) -> float:
        """How close is the power-law exponent to the SOC band?"""
        center = (self.SOC_ALPHA_LOW + self.SOC_ALPHA_HIGH) / 2.0
        width = (self.SOC_ALPHA_HIGH - self.SOC_ALPHA_LOW) / 2.0
        dist = abs(alpha - center)
        return float(max(0.0, 1.0 - dist / width))

    def _phase_transition_risk(self, x: np.ndarray) -> float:
        """
        Variance divergence near critical point is the canonical phase
        transition signature. Risk = normalized running variance slope.
        """
        w = max(10, len(x) // 10)
        variances = [x[i:i+w].var() for i in range(0, len(x) - w, w)]
        if len(variances) < 3:
            return 0.0
        slope = np.polyfit(range(len(variances)), variances, 1)[0]
        return float(min(1.0, abs(slope) / (np.var(x) + 1e-10)))
