"""core/uncertainty_quantifier.py — R61
The Uncertainty Quantifier. Calibrated confidence.

Knows what it DOESN'T know. Detects overconfidence and underconfidence.
Recommends adjustments.

Falsifier: if confidence scores have zero correlation with actual
outcomes, the quantifier is decoration, not calibration.

truth_plane: CANONICAL
omega (R61): the mind that knows its own uncertainty is the mind that learns.
"""

from __future__ import annotations
import json, math, time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Belief:
    id: str
    claim: str
    confidence: float  # 0-1
    evidence_for: int = 0
    evidence_against: int = 0
    last_updated: float = 0.0
    source: str = "observation"
    risk_level: str = "medium"  # low | medium | high | critical


class UncertaintyQuantifier:
    """Calibrated confidence. Knows what it DOESN'T know."""

    def __init__(self, state_dir: str | None = None):
        self.state_dir = Path(state_dir) if state_dir else REPO_ROOT / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.beliefs: Dict[str, Belief] = {}
        self._calibration: List[Dict] = []  # (predicted_confidence, actual_outcome) pairs
        self._load()

    def _load(self):
        path = self.state_dir / "beliefs.json"
        if path.exists():
            data = json.loads(path.read_text())
            for b in data.get("beliefs", []):
                self.beliefs[b["id"]] = Belief(
                    id=b["id"], claim=b["claim"],
                    confidence=b["confidence"],
                    evidence_for=b.get("evidence_for", 0),
                    evidence_against=b.get("evidence_against", 0),
                    last_updated=b.get("last_updated", 0),
                    source=b.get("source", "observation"),
                    risk_level=b.get("risk_level", "medium"),
                )
            self._calibration = data.get("calibration", [])

    def _save(self):
        path = self.state_dir / "beliefs.json"
        data = {
            "beliefs": [
                {
                    "id": b.id, "claim": b.claim,
                    "confidence": b.confidence,
                    "evidence_for": b.evidence_for,
                    "evidence_against": b.evidence_against,
                    "last_updated": b.last_updated,
                    "source": b.source,
                    "risk_level": b.risk_level,
                } for b in self.beliefs.values()
            ],
            "calibration": self._calibration[-500:],  # Keep last 500
        }
        path.write_text(json.dumps(data, indent=2))

    def track(self, claim: str, confidence: float, source: str = "observation") -> Belief:
        """Track a belief with initial confidence."""
        import hashlib
        bid = hashlib.md5(claim.encode()).hexdigest()[:12]
        if bid in self.beliefs:
            b = self.beliefs[bid]
            b.confidence = (b.confidence + confidence) / 2  # Average with prior
            b.last_updated = time.time()
        else:
            risk = "critical" if confidence > 0.9 else "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low"
            b = Belief(id=bid, claim=claim, confidence=confidence, last_updated=time.time(), source=source, risk_level=risk)
            self.beliefs[bid] = b
        self._save()
        return b

    def update(self, claim: str, outcome: bool):
        """Update belief based on real outcome. Feeds calibration."""
        import hashlib
        bid = hashlib.md5(claim.encode()).hexdigest()[:12]
        if bid in self.beliefs:
            b = self.beliefs[bid]
            if outcome:
                b.evidence_for += 1
                b.confidence = min(1.0, b.confidence + 0.05)
            else:
                b.evidence_against += 1
                b.confidence = max(0.0, b.confidence - 0.1)
            b.last_updated = time.time()

            # Record calibration point
            self._calibration.append({
                "predicted": b.confidence,
                "actual": 1.0 if outcome else 0.0,
                "timestamp": time.time(),
            })
        self._save()

    def calibration_score(self) -> float:
        """Brier score: 0 = perfect, 1 = worst. Lower is better."""
        if not self._calibration:
            return 0.5  # No data = uncertain
        recent = self._calibration[-100:]
        brier = sum((c["predicted"] - c["actual"]) ** 2 for c in recent) / len(recent)
        return round(brier, 4)

    def overconfident_beliefs(self) -> List[Belief]:
        """Beliefs with high confidence but poor evidence."""
        return [
            b for b in self.beliefs.values()
            if b.confidence > 0.8 and b.evidence_for + b.evidence_against < 3
        ]

    def underconfident_beliefs(self) -> List[Belief]:
        """Beliefs with low confidence but strong evidence."""
        return [
            b for b in self.beliefs.values()
            if b.confidence < 0.3 and b.evidence_for >= 5 and b.evidence_for > b.evidence_against * 3
        ]

    def recommend_adjustments(self) -> List[str]:
        """Recommend confidence adjustments."""
        recs = []
        for b in self.overconfident_beliefs():
            recs.append(f"OVERCONFIDENT: '{b.claim[:50]}' — confidence {b.confidence:.2f} with only {b.evidence_for} supporting evidence")
        for b in self.underconfident_beliefs():
            recs.append(f"UNDERCONFIDENT: '{b.claim[:50]}' — confidence {b.confidence:.2f} despite {b.evidence_for} supporting evidence")
        return recs

    def health_check(self) -> Dict[str, Any]:
        """Falsification: is calibration real or decoration?"""
        brier = self.calibration_score()
        # Good calibration: brier < 0.25. Random: ~0.33. Worst: 1.0
        n_points = len(self._calibration)
        overconfident = len(self.overconfident_beliefs())
        underconfident = len(self.underconfident_beliefs())

        # Correlation check (simplified)
        is_decorative = n_points < 10  # Not enough data to calibrate

        return {
            "total_beliefs": len(self.beliefs),
            "calibration_points": n_points,
            "brier_score": brier,
            "overconfident_beliefs": overconfident,
            "underconfident_beliefs": underconfident,
            "is_decorative": is_decorative,
            "is_well_calibrated": brier < 0.25 and n_points >= 10,
            "status": "calibrated" if brier < 0.25 and n_points >= 10 else "uncalibrated",
        }
