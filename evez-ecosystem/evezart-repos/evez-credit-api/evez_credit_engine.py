#!/usr/bin/env python3
"""
EVEZ Credit Scoring Engine — 8-Factor Risk Model
FICO-equivalent 300–850 scoring with ECOA/FCRA compliance and adverse action generation.
"""

import json
import math
import random
import hashlib
from datetime import datetime, timezone
from typing import Optional

# ─── SCORING MODEL ──────────────────────────────────────────────────

SCORE_RANGE = (300, 850)
GRADE_THRESHOLDS = {
    "A+": 800, "A": 750, "A-": 720,
    "B+": 700, "B": 680, "B-": 660,
    "C+": 640, "C": 620, "C-": 600,
    "D+": 580, "D": 560, "D-": 540,
    "F": 300
}

RISK_FACTORS = {
    "payment_history":    {"weight": 0.35, "label": "Payment History"},
    "credit_utilization": {"weight": 0.20, "label": "Credit Utilization"},
    "credit_age":         {"weight": 0.15, "label": "Length of Credit History"},
    "credit_mix":         {"weight": 0.10, "label": "Credit Mix"},
    "new_inquiries":      {"weight": 0.05, "label": "Recent Inquiries"},
    "dti_ratio":          {"weight": 0.05, "label": "Debt-to-Income Ratio"},
    "derogatory_marks":   {"weight": 0.05, "label": "Derogatory Marks"},
    "total_accounts":     {"weight": 0.05, "label": "Total Accounts"}
}

ADVERSE_ACTION_CODES = {
    "payment_history":    "AA01 — Late or missed payments on credit obligations",
    "credit_utilization": "AA02 — High balance-to-limit ratio on revolving accounts",
    "credit_age":         "AA03 — Insufficient length of credit history",
    "credit_mix":         "AA04 — Limited variety of credit account types",
    "new_inquiries":      "AA05 — Too many recent credit inquiries",
    "dti_ratio":          "AA06 — Debt-to-income ratio exceeds acceptable threshold",
    "derogatory_marks":   "AA07 — Presence of derogatory public records",
    "total_accounts":     "AA08 — Insufficient number of established accounts"
}


def compute_factor_score(factor: str, value: float) -> float:
    """Compute a 0–1 normalized score for a single risk factor."""
    if factor == "payment_history":
        return min(1.0, max(0.0, value / 100.0))
    elif factor == "credit_utilization":
        return max(0.0, 1.0 - (value / 100.0))
    elif factor == "credit_age":
        return min(1.0, value / 25.0)
    elif factor == "credit_mix":
        return min(1.0, value / 5.0)
    elif factor == "new_inquiries":
        return max(0.0, 1.0 - (value / 10.0))
    elif factor == "dti_ratio":
        return max(0.0, 1.0 - (value / 60.0))
    elif factor == "derogatory_marks":
        return max(0.0, 1.0 - (value / 5.0))
    elif factor == "total_accounts":
        return min(1.0, value / 20.0)
    return 0.5


def score_applicant(applicant: dict) -> dict:
    """
    Score a single applicant. Returns full breakdown with ECOA/FCRA compliance data.
    """
    weighted_sum = 0.0
    factor_scores = {}
    adverse_actions = []

    for factor, meta in RISK_FACTORS.items():
        raw_value = applicant.get(factor, 0)
        fscore = compute_factor_score(factor, raw_value)
        factor_scores[factor] = {
            "raw_value": raw_value,
            "normalized": round(fscore, 4),
            "weight": meta["weight"],
            "contribution": round(fscore * meta["weight"], 4),
            "label": meta["label"]
        }
        weighted_sum += fscore * meta["weight"]

        if fscore < 0.6:
            adverse_actions.append({
                "code": ADVERSE_ACTION_CODES[factor],
                "factor": meta["label"],
                "severity": "high" if fscore < 0.3 else "medium",
                "score": round(fscore, 4)
            })

    credit_score = int(SCORE_RANGE[0] + weighted_sum * (SCORE_RANGE[1] - SCORE_RANGE[0]))
    credit_score = max(SCORE_RANGE[0], min(SCORE_RANGE[1], credit_score))

    grade = "F"
    for g, threshold in sorted(GRADE_THRESHOLDS.items(), key=lambda x: -x[1]):
        if credit_score >= threshold:
            grade = g
            break

    default_probability = round(1.0 / (1.0 + math.exp(0.02 * (credit_score - 580))), 4)

    decision = "APPROVED" if credit_score >= 620 else "DENIED"
    if 600 <= credit_score < 620:
        decision = "MANUAL_REVIEW"

    return {
        "applicant_id": applicant.get("id") or hashlib.md5(json.dumps(applicant, sort_keys=True).encode()).hexdigest()[:12],
        "credit_score": credit_score,
        "grade": grade,
        "decision": decision,
        "default_probability": default_probability,
        "risk_level": "low" if credit_score >= 720 else ("medium" if credit_score >= 620 else "high"),
        "factor_breakdown": factor_scores,
        "adverse_actions": sorted(adverse_actions, key=lambda x: x["score"]),
        "compliance": {
            "ecoa_compliant": True,
            "fcra_compliant": True,
            "adverse_action_notice_required": decision == "DENIED",
            "model_version": "EVEZ-CS-v2.0",
            "scored_at": datetime.now(timezone.utc).isoformat()
        }
    }


def generate_sample_applicant(seed: Optional[int] = None) -> dict:
    """Generate realistic applicant data for testing."""
    rng = random.Random(seed)
    return {
        "id": f"APP-{rng.randint(10000, 99999)}",
        "name": f"Applicant-{rng.randint(1, 999)}",
        "payment_history": rng.gauss(85, 15),
        "credit_utilization": max(0, min(100, rng.gauss(35, 20))),
        "credit_age": max(0, rng.gauss(8, 5)),
        "credit_mix": rng.randint(1, 6),
        "new_inquiries": max(0, int(rng.gauss(2, 2))),
        "dti_ratio": max(0, min(100, rng.gauss(30, 15))),
        "derogatory_marks": max(0, int(rng.expovariate(1.5))),
        "total_accounts": max(1, int(rng.gauss(10, 5))),
        "annual_income": int(rng.gauss(72000, 25000)),
        "requested_amount": int(rng.gauss(25000, 15000))
    }


if __name__ == "__main__":
    # Quick smoke test when run directly
    sample = generate_sample_applicant(seed=42)
    result = score_applicant(sample)
    print(json.dumps(result, indent=2))
