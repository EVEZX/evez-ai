"""
CAIN Contradiction Engine — Layer 2 Review System
Adversarial Dissent for EVEZ-OS (A002)
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path


@dataclass
class Contradiction:
    """A detected contradiction between claims or evidence."""
    contradiction_id: str
    source_a: str  # First claim/source
    source_b: str  # Second claim/source
    claim_a: str
    claim_b: str
    confidence: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    resolved: bool = False
    resolution: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class CAINEngine:
    """
    Contradiction Analysis and Integrity Network
    Adversarially challenges claims and detects inconsistencies.
    """
    
    def __init__(self, spine_path: Path):
        self.spine_path = spine_path
        self.spine_path.mkdir(parents=True, exist_ok=True)
        self.contradictions: List[Contradiction] = []
        
    def _generate_id(self, *parts) -> str:
        data = "|".join(str(p) for p in parts)
        return f"cain_{hashlib.sha256(data.encode()).hexdigest()[:12]}"
    
    def challenge_claim(self, claim: str, sources: List[str]) -> List[Contradiction]:
        """
        Challenge a claim against multiple sources.
        Returns any contradictions found.
        """
        contradictions = []
        
        # Check for absolute claims (rarely true in practice)
        absolutes = ["never", "always", "all", "every", "none"]
        if any(word in claim.lower() for word in absolutes):
            contradictions.append(Contradiction(
                contradiction_id=self._generate_id("absolute", claim),
                source_a="language_pattern",
                source_b="logic",
                claim_a=claim,
                claim_b="Absolute generalizations are rarely true",
                confidence=0.85,
                evidence=["Linguistic analysis detected absolute modifiers"],
                severity="HIGH"
            ))
        
        # Cross-source contradiction check
        for i, src_a in enumerate(sources):
            for src_b in sources[i+1:]:
                # Simple heuristic: if sources disagree on key terms
                if not self._sources_align(src_a, src_b):
                    contradictions.append(Contradiction(
                        contradiction_id=self._generate_id(claim, src_a, src_b),
                        source_a=src_a,
                        source_b=src_b,
                        claim_a=src_a,
                        claim_b=src_b,
                        confidence=0.75,
                        evidence=[f"Source disagreement on claim: {claim}"],
                        severity="MEDIUM"
                    ))
        
        # Add to main list
        self.contradictions.extend(contradictions)
        return contradictions
    
    def _sources_align(self, src_a: str, src_b: str) -> bool:
        """Check if two sources align (simplified)."""
        # Placeholder - in reality would use semantic similarity
        return src_a.lower() == src_b.lower()
    
    def run_dissent_protocol(self, review: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run full adversarial dissent on a review.
        Layer 2 analysis that challenges assumptions.
        """
        findings = {
            "contradictions": [],
            "challenges": [],
            "risk_flags": [],
            "confidence_adjustment": 0.0
        }
        
        # Extract claims from review
        claims = review.get("claims", [])
        evidence = review.get("evidence", [])
        conclusion = review.get("conclusion", "")
        
        # Challenge each claim
        for claim in claims:
            srcs = [e.get("source", "unknown") for e in evidence]
            contradictions = self.challenge_claim(claim, srcs)
            findings["contradictions"].extend([c.__dict__ for c in contradictions])
        
        # Risk flags from unresolved contradictions
        unresolved = [c for c in self.contradictions if not c.resolved]
        if unresolved:
            findings["risk_flags"].append({
                "type": "UNRESOLVED_CONTRADICTIONS",
                "count": len(unresolved),
                "severity": max(c.severity for c in unresolved)
            })
            findings["confidence_adjustment"] -= min(0.3, len(unresolved) * 0.1)
        
        # Add dissent reasoning
        findings["challenges"].append({
            "type": "ASSUMPTION_CHALLENGE",
            "question": "What evidence would falsify this conclusion?",
            "dissent": "The conclusion assumes linearity - nonlinear effects may dominate"
        })
        
        return findings
    
    def generate_ledger_event(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Convert CAIN analysis to spine ledger event."""
        return {
            "event_type": "CAIN_ANALYSIS",
            "timestamp": time.time(),
            "contradictions_found": len(analysis.get("contradictions", [])),
            "confidence_adjustment": analysis.get("confidence_adjustment", 0),
            "risk_flags": analysis.get("risk_flags", []),
            "hash": hashlib.sha256(
                json.dumps(analysis, sort_keys=True).encode()
            ).hexdigest()[:16]
        }