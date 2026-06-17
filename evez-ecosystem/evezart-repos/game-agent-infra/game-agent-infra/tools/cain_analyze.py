#!/usr/bin/env python3
"""
CAIN - Contradiction Analysis & Inquiry Net
Layer 2 Review Engine (A002 adversarial dissent system)
Wrapper for processing review items directly.
"""

from __future__ import annotations
import json
import hashlib
from dataclasses import dataclass
from typing import Any
from pathlib import Path

# Import the main CAIN engine
from cain_engine import CAINEngine, Contradiction


@dataclass
class CAINAnalysisResult:
    review_id: str
    findings: list
    risk_level: str
    recommendation: str


def analyze_review_item(review_item: dict[str, Any], spine_path: Path = Path("cain_spine")) -> CAINAnalysisResult:
    """Analyze a review item using CAIN engine."""
    engine = CAINEngine(spine_path=spine_path)
    
    # Build review format for CAIN
    review = {
        "review_id": review_item.get("review_id", "unknown"),
        "claims": review_item.get("claims", [review_item.get("content", "")]),
        "evidence": review_item.get("evidence", []),
        "conclusion": review_item.get("conclusion", "pending"),
    }
    
    # Run dissent protocol
    findings = engine.run_dissent_protocol(review)
    
    # Determine risk level
    risk_level = "LOW"
    if findings["risk_flags"]:
        risk_level = max(f["severity"] for f in findings["risk_flags"])
    
    # Recommendation
    recommendation = "APPROVED" if not findings["contradictions"] else "NEEDS_REVIEW"
    if findings["risk_flags"]:
        recommendation = "REJECTED"
    
    return CAINAnalysisResult(
        review_id=review["review_id"],
        findings=findings,
        risk_level=risk_level,
        recommendation=recommendation,
    )


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: cain_analyze.py <review_item.json>")
        sys.exit(1)
    
    item = json.loads(Path(sys.argv[1]).read_text())
    result = analyze_review_item(item)
    
    print(json.dumps({
        "review_id": result.review_id,
        "risk_level": result.risk_level,
        "recommendation": result.recommendation,
        "findings": result.findings,
    }, indent=2))
    
    sys.exit(0 if result.recommendation != "REJECTED" else 1)


if __name__ == "__main__":
    main()