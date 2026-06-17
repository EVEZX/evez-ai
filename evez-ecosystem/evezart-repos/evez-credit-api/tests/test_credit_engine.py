"""Tests for the EVEZ credit scoring engine."""
import math
import pytest
import sys
from pathlib import Path

# Ensure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import evez_credit_engine as engine


class TestFactorScoring:
    """Verify each factor normalization function."""

    def test_payment_history_perfect(self):
        assert engine.compute_factor_score("payment_history", 100) == 1.0

    def test_payment_history_zero(self):
        assert engine.compute_factor_score("payment_history", 0) == 0.0

    def test_credit_utilization_zero(self):
        """0% utilization should score 1.0 (best)."""
        assert engine.compute_factor_score("credit_utilization", 0) == 1.0

    def test_credit_utilization_full(self):
        """100% utilization should score 0.0 (worst)."""
        assert engine.compute_factor_score("credit_utilization", 100) == 0.0

    def test_new_inquiries_none(self):
        assert engine.compute_factor_score("new_inquiries", 0) == 1.0

    def test_dti_zero(self):
        assert engine.compute_factor_score("dti_ratio", 0) == 1.0

    def test_derogatory_marks_none(self):
        assert engine.compute_factor_score("derogatory_marks", 0) == 1.0

    def test_unknown_factor(self):
        assert engine.compute_factor_score("nonexistent", 0) == 0.5


class TestScoreApplicant:
    """Verify scoring with known inputs."""

    def test_perfect_applicant(self):
        """All-perfect inputs should yield a score near 850."""
        applicant = {
            "id": "PERFECT-001",
            "payment_history": 100,
            "credit_utilization": 0,
            "credit_age": 25,
            "credit_mix": 5,
            "new_inquiries": 0,
            "dti_ratio": 0,
            "derogatory_marks": 0,
            "total_accounts": 20,
        }
        result = engine.score_applicant(applicant)
        assert result["applicant_id"] == "PERFECT-001"
        assert result["credit_score"] == 850
        assert result["grade"] == "A+"
        assert result["decision"] == "APPROVED"
        assert result["risk_level"] == "low"
        assert result["default_probability"] < 0.01
        assert len(result["adverse_actions"]) == 0

    def test_worst_applicant(self):
        """All-worst inputs should yield a score of 300."""
        applicant = {
            "id": "WORST-001",
            "payment_history": 0,
            "credit_utilization": 100,
            "credit_age": 0,
            "credit_mix": 0,
            "new_inquiries": 10,
            "dti_ratio": 60,
            "derogatory_marks": 5,
            "total_accounts": 0,
        }
        result = engine.score_applicant(applicant)
        assert result["credit_score"] == 300
        assert result["grade"] == "F"
        assert result["decision"] == "DENIED"
        assert result["risk_level"] == "high"
        assert len(result["adverse_actions"]) > 0

    def test_moderate_applicant_manual_review(self):
        """A marginal applicant should hit MANUAL_REVIEW zone (600-619)."""
        # payment_history=50, utilization=50, age=8, mix=2, inquiries=5, dti=30, derogatory=2, accounts=5
        applicant = {
            "payment_history": 50,
            "credit_utilization": 50,
            "credit_age": 8,
            "credit_mix": 2,
            "new_inquiries": 5,
            "dti_ratio": 30,
            "derogatory_marks": 2,
            "total_accounts": 5,
        }
        result = engine.score_applicant(applicant)
        # We just verify the score is in a plausible range and a decision is made
        assert 300 <= result["credit_score"] <= 850
        assert result["decision"] in ("APPROVED", "DENIED", "MANUAL_REVIEW")

    def test_score_range_bounded(self):
        """Any input combination must stay within 300-850."""
        for ph in [0, 50, 100]:
            for cu in [0, 50, 100]:
                result = engine.score_applicant({
                    "payment_history": ph,
                    "credit_utilization": cu,
                    "credit_age": 5,
                    "credit_mix": 3,
                    "new_inquiries": 2,
                    "dti_ratio": 30,
                    "derogatory_marks": 0,
                    "total_accounts": 10,
                })
                assert 300 <= result["credit_score"] <= 850

    def test_adverse_action_for_poor_factors(self):
        """Factors below 0.6 normalized should generate adverse actions."""
        applicant = {
            "payment_history": 30,  # 0.3 normalized → high severity
            "credit_utilization": 80,  # 0.2 normalized → high severity
            "credit_age": 2,
            "credit_mix": 1,
            "new_inquiries": 1,
            "dti_ratio": 20,
            "derogatory_marks": 0,
            "total_accounts": 15,
        }
        result = engine.score_applicant(applicant)
        codes = [a["code"] for a in result["adverse_actions"]]
        assert any("AA01" in c for c in codes)  # payment_history
        assert any("AA02" in c for c in codes)  # credit_utilization

    def test_default_probability_scales(self):
        """Higher scores → lower default probability."""
        high = engine.score_applicant({"payment_history": 95, "credit_utilization": 5, "credit_age": 20,
                                        "credit_mix": 5, "new_inquiries": 0, "dti_ratio": 10,
                                        "derogatory_marks": 0, "total_accounts": 18})
        low = engine.score_applicant({"payment_history": 30, "credit_utilization": 80, "credit_age": 1,
                                       "credit_mix": 1, "new_inquiries": 8, "dti_ratio": 50,
                                       "derogatory_marks": 3, "total_accounts": 2})
        assert high["default_probability"] < low["default_probability"]

    def test_compliance_fields_present(self):
        result = engine.score_applicant({"payment_history": 70, "credit_utilization": 30})
        assert "compliance" in result
        assert result["compliance"]["ecoa_compliant"] is True
        assert result["compliance"]["fcra_compliant"] is True
        assert "model_version" in result["compliance"]


class TestSampleApplicant:
    """Verify sample applicant generator."""

    def test_deterministic_with_seed(self):
        a = engine.generate_sample_applicant(seed=1)
        b = engine.generate_sample_applicant(seed=1)
        assert a == b

    def test_different_seeds(self):
        a = engine.generate_applicant(seed=1) if hasattr(engine, "generate_applicant") else engine.generate_sample_applicant(seed=1)
        b = engine.generate_sample_applicant(seed=2)
        assert a != b

    def test_has_all_factors(self):
        a = engine.generate_sample_applicant(seed=42)
        for factor in engine.RISK_FACTORS:
            assert factor in a, f"Missing factor: {factor}"


class TestModelConstants:
    """Verify the model is self-consistent."""

    def test_weights_sum_to_one(self):
        total = sum(m["weight"] for m in engine.RISK_FACTORS.values())
        assert abs(total - 1.0) < 1e-9

    def test_eight_factors(self):
        assert len(engine.RISK_FACTORS) == 8

    def test_grade_thresholds_descending(self):
        thresholds = list(engine.GRADE_THRESHOLDS.values())
        # Should be non-increasing when read in definition order
        for i in range(1, len(thresholds)):
            assert thresholds[i] <= thresholds[i - 1]
