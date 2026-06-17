"""core/world_model.py — R61
The World Model. Not just "what happened" but WHY and WHAT WILL.

Causal rules with confidence. Predict forward, explain backward.
Falsify when wrong. The difference between sensing and UNDERSTANDING.

Falsifier: if more than 50% of predictions are wrong, the model
is not understanding — it's guessing.

truth_plane: CANONICAL
omega (R61): understanding is the compression of experience into rules that predict.
"""

from __future__ import annotations
import json, time, hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CausalRule:
    id: str
    cause: str
    effect: str
    confidence: float = 0.5  # 0-1
    evidence_for: int = 0
    evidence_against: int = 0
    last_seen: float = 0.0
    source: str = "observation"  # observation | creator | inference

    def bayesian_strength(self) -> float:
        """Confidence adjusted by evidence."""
        total = self.evidence_for + self.evidence_against
        if total == 0:
            return 0.5
        return (self.evidence_for + 1) / (total + 2)  # Laplace smoothing

    def predict(self, observation: Dict[str, Any]) -> Optional[str]:
        """If cause matches observation, return predicted effect."""
        cause_key, cause_val = self.cause.split("=", 1) if "=" in self.cause else (self.cause, "*")
        if cause_val == "*" or str(observation.get(cause_key)) == cause_val:
            return self.effect
        return None


class WorldModel:
    """Causal rules predicting outcomes of actions. Falsify when wrong."""

    def __init__(self, state_dir: str | None = None):
        self.state_dir = Path(state_dir) if state_dir else REPO_ROOT / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.rules: Dict[str, CausalRule] = {}
        self._load()

    def _load(self):
        path = self.state_dir / "world_model.json"
        if path.exists():
            data = json.loads(path.read_text())
            for r in data.get("rules", []):
                rule = CausalRule(
                    id=r["id"],
                    cause=r["cause"],
                    effect=r["effect"],
                    confidence=r.get("confidence", 0.5),
                    evidence_for=r.get("evidence_for", 0),
                    evidence_against=r.get("evidence_against", 0),
                    last_seen=r.get("last_seen", 0),
                    source=r.get("source", "observation"),
                )
                self.rules[rule.id] = rule

    def _save(self):
        path = self.state_dir / "world_model.json"
        data = {
            "rules": [
                {
                    "id": r.id,
                    "cause": r.cause,
                    "effect": r.effect,
                    "confidence": r.confidence,
                    "evidence_for": r.evidence_for,
                    "evidence_against": r.evidence_against,
                    "last_seen": r.last_seen,
                    "source": r.source,
                }
                for r in self.rules.values()
            ]
        }
        path.write_text(json.dumps(data, indent=2))

    def observe(self, cause: str, effect: str, source: str = "observation"):
        """Record a causal observation. Update existing rule or create new one."""
        # Check if rule already exists
        for rule in self.rules.values():
            if rule.cause == cause and rule.effect == effect:
                rule.evidence_for += 1
                rule.confidence = rule.bayesian_strength()
                rule.last_seen = time.time()
                rule.source = source
                self._save()
                return rule

        # New rule
        rule_id = hashlib.md5(f"{cause}->{effect}".encode()).hexdigest()[:12]
        rule = CausalRule(
            id=rule_id,
            cause=cause,
            effect=effect,
            confidence=0.5,
            evidence_for=1,
            last_seen=time.time(),
            source=source,
        )
        self.rules[rule_id] = rule
        self._save()
        return rule

    def falsify(self, cause: str, expected_effect: str, actual_effect: str):
        """A prediction was wrong. Update evidence against."""
        for rule in self.rules.values():
            if rule.cause == cause and rule.effect == expected_effect:
                rule.evidence_against += 1
                rule.confidence = rule.bayesian_strength()
                if rule.confidence < 0.1:
                    # Rule is effectively dead
                    pass
                self._save()
                return True
        return False

    def predict(self, context: Dict[str, Any], top_k: int = 5) -> List[Tuple[str, float]]:
        """Given current context, predict what will happen."""
        predictions = []
        for rule in self.rules.values():
            effect = rule.predict(context)
            if effect:
                predictions.append((effect, rule.confidence))
        predictions.sort(key=lambda x: -x[1])
        return predictions[:top_k]

    def explain(self, effect: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Given an effect, find likely causes (backward reasoning)."""
        causes = []
        for rule in self.rules.values():
            if rule.effect == effect:
                causes.append((rule.cause, rule.confidence))
        causes.sort(key=lambda x: -x[1])
        return causes[:top_k]

    def contradictions(self) -> List[Tuple[CausalRule, CausalRule]]:
        """Find rules where same cause produces contradictory effects."""
        by_cause: Dict[str, List[CausalRule]] = {}
        for rule in self.rules.values():
            by_cause.setdefault(rule.cause, []).append(rule)

        contradictions = []
        for cause, rules in by_cause.items():
            effects = set(r.effect for r in rules)
            if len(effects) > 1:
                for i, r1 in enumerate(rules):
                    for r2 in rules[i+1:]:
                        if r1.effect != r2.effect:
                            contradictions.append((r1, r2))
        return contradictions

    def health_check(self) -> Dict[str, Any]:
        """Falsification: is the model understanding or guessing?"""
        if not self.rules:
            return {"prediction_accuracy": 0, "total_rules": 0, "status": "empty"}

        total_evidence = sum(r.evidence_for + r.evidence_against for r in self.rules.values())
        correct = sum(r.evidence_for for r in self.rules.values())
        accuracy = correct / max(total_evidence, 1)

        weak_rules = [r for r in self.rules.values() if r.confidence < 0.2]
        strong_rules = [r for r in self.rules.values() if r.confidence > 0.8]
        contras = self.contradictions()

        return {
            "total_rules": len(self.rules),
            "strong_rules": len(strong_rules),
            "weak_rules": len(weak_rules),
            "contradictions": len(contras),
            "prediction_accuracy": accuracy,
            "is_guessing": accuracy < 0.5,
            "status": "healthy" if accuracy >= 0.5 and len(contras) == 0 else "degraded",
        }
