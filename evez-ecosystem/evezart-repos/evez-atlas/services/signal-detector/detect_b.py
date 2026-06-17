"""detect_b.py — Canonical EVEZ signal detector (DetectB class)

This is the executable core of the signal-detection subsystem.
The hyperloop fire condition poly_c >= 0.500 is detect_B with k=0, threshold=0.500.
All round data from R114+ is valid test input.

Canonical reference: docs/architecture/EVEZ_IMPL.md
"""

import math
from dataclasses import dataclass, field
from collections import deque
from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone


@dataclass
class DetectorConfig:
    """Runtime configuration for DetectB.

    For EVEZ hyperloop fire detection:
      k=0, baseline_mean=0.500, baseline_std=0 (fixed threshold mode)
    For adaptive signal detection:
      k=3.0, rolling baseline from window
    """
    k: float = 3.0
    decay_tau_ms: float = 500.0
    min_peak_prominence: float = 0.05
    refractory_window_ms: float = 200.0
    baseline_window: int = 100
    confidence_floor: float = 0.50
    # Fixed threshold mode (k=0, set fixed_threshold to override rolling baseline)
    fixed_threshold: Optional[float] = None

    # Hyperloop preset
    @classmethod
    def hyperloop_fire(cls) -> "DetectorConfig":
        """Preset for hyperloop fire condition: poly_c >= 0.500"""
        return cls(
            k=0,
            fixed_threshold=0.500,
            min_peak_prominence=0.0,
            refractory_window_ms=0.0,  # Prime blocks act as natural refractory
            confidence_floor=0.0,
        )


class DetectB:
    """
    Adaptive threshold signal detector.

    detect_B fires when:
      value >= threshold
      AND prominence >= min_peak_prominence
      AND confidence >= confidence_floor
      AND not in refractory window

    EVEZ hyperloop equivalence:
      poly_c >= 0.500  ==  DetectB(DetectorConfig.hyperloop_fire()).process(poly_c, round_number)
    """

    def __init__(self, config: DetectorConfig = None):
        self.cfg = config or DetectorConfig()
        self._baseline: deque = deque(maxlen=self.cfg.baseline_window)
        self._last_fire_ms: Optional[float] = None
        self._envelope: float = 0.0
        self._sample_count: int = 0
        self._fire_count: int = 0

    def update_baseline(self, value: float) -> None:
        if self.cfg.fixed_threshold is None:
            self._baseline.append(value)

    @property
    def baseline_mean(self) -> float:
        if self.cfg.fixed_threshold is not None:
            return self.cfg.fixed_threshold
        if not self._baseline:
            return 0.0
        return sum(self._baseline) / len(self._baseline)

    @property
    def baseline_std(self) -> float:
        if self.cfg.fixed_threshold is not None:
            return 0.0
        if len(self._baseline) < 2:
            return 1.0
        m = self.baseline_mean
        variance = sum((x - m) ** 2 for x in self._baseline) / len(self._baseline)
        return math.sqrt(variance) or 1e-9

    def peak_threshold(self) -> float:
        if self.cfg.fixed_threshold is not None:
            return self.cfg.fixed_threshold
        return self.baseline_mean + self.cfg.k * self.baseline_std

    def update_envelope(self, value: float, dt_ms: float) -> float:
        if dt_ms <= 0:
            dt_ms = 16.67
        alpha = math.exp(-dt_ms / max(self.cfg.decay_tau_ms, 1e-9))
        self._envelope = max(value, self._envelope * alpha)
        return self._envelope

    def confidence(self, value: float) -> float:
        thresh = self.peak_threshold()
        if thresh <= 0:
            return 1.0 if value > 0 else 0.0
        excess = value - thresh
        if excess <= 0:
            return 0.0
        return min(1.0, excess / thresh)

    def process(self, value: float, timestamp_ms: float, dt_ms: float = 16.67) -> dict:
        """Process one sample. Returns signal_event dict."""
        self._sample_count += 1
        self.update_baseline(value)
        envelope = self.update_envelope(value, dt_ms)
        thresh = self.peak_threshold()
        prominence = value - self.baseline_mean
        conf = self.confidence(value)

        in_refractory = (
            self._last_fire_ms is not None
            and self.cfg.refractory_window_ms > 0
            and (timestamp_ms - self._last_fire_ms) < self.cfg.refractory_window_ms
        )

        peak_detected = (
            value >= thresh
            and prominence >= self.cfg.min_peak_prominence
        )

        detect_b = (
            peak_detected
            and conf >= self.cfg.confidence_floor
            and not in_refractory
        )

        if detect_b:
            self._last_fire_ms = timestamp_ms
            self._fire_count += 1

        # Classify A (sub-threshold peak) / B (detect_B fire) / C (no peak)
        if detect_b:
            classification = "B"
        elif peak_detected:
            classification = "A"
        else:
            classification = "C"

        return {
            "schema": "signal_event/1.0",
            "id": f"sig_{uuid4().hex[:12]}",
            "timestamp_ms": timestamp_ms,
            "raw_value": value,
            "normalized_value": value,
            "baseline_mean": round(self.baseline_mean, 6),
            "baseline_std": round(self.baseline_std, 6),
            "peak_threshold": round(thresh, 6),
            "envelope": round(envelope, 6),
            "prominence": round(prominence, 6),
            "peak_detected": peak_detected,
            "detect_B": detect_b,
            "in_refractory": in_refractory,
            "confidence": round(conf, 6),
            "classification": classification,
            "sample_count": self._sample_count,
            "fire_count": self._fire_count,
        }

    def reset(self) -> None:
        """Reset detector state (use between independent signal streams)."""
        self._baseline.clear()
        self._last_fire_ms = None
        self._envelope = 0.0
        self._sample_count = 0
        self._fire_count = 0
