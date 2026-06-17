#!/usr/bin/env python3
"""
Tests for A012 — Telemetry Prediction & Coincidence Engine
"""
import sys
import os
import json
import math
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from skills.a012_telemetry_coincidence_engine import (
    divisors, tau, distinct_prime_factors, compute_poly_c,
    generate_prediction, score_prediction,
    scan_jsonl_for_coincidences, generate_coincidence_event,
    generate_lookahead, run_a012
)


class TestFormulaA(unittest.TestCase):
    """Formula A canonical computation tests — fixed fixtures from EVEZ-OS ledger."""

    def test_divisors_explicit(self):
        """Divisors must be computed by explicit enumeration."""
        self.assertEqual(sorted(divisors(12)), [1, 2, 3, 4, 6, 12])
        self.assertEqual(sorted(divisors(449)), [1, 449])   # prime
        self.assertEqual(sorted(divisors(450)), [1, 2, 3, 5, 6, 9, 10, 15, 18, 25, 30, 45, 50, 75, 90, 150, 225, 450])

    def test_tau(self):
        self.assertEqual(tau(449), 2)    # prime
        self.assertEqual(tau(450), 18)   # 2×3²×5²
        self.assertEqual(tau(448), 14)   # 2⁶×7

    def test_omega(self):
        self.assertEqual(distinct_prime_factors(449), 1)  # prime
        self.assertEqual(distinct_prime_factors(450), 3)  # 2,3,5
        self.assertEqual(distinct_prime_factors(448), 2)  # 2,7

    def test_poly_c_r368(self):
        """R368: N=448=2^6×7, tau=14, omega=2, poly_c=0.8599"""
        p = compute_poly_c(368)
        self.assertEqual(p["N"], 448)
        self.assertEqual(p["tau"], 14)
        self.assertEqual(p["omega_k"], 2)
        self.assertAlmostEqual(p["poly_c"], 0.859869, places=4)

    def test_poly_c_r369_prime(self):
        """R369: N=449 prime, tau=2, omega=1, poly_c~0.054 — NO FIRE"""
        p = compute_poly_c(369)
        self.assertEqual(p["N"], 449)
        self.assertEqual(p["tau"], 2)
        self.assertEqual(p["omega_k"], 1)
        self.assertAlmostEqual(p["poly_c"], 0.0543, places=3)
        self.assertFalse(p["fire_candidate"])

    def test_poly_c_r370_extreme(self):
        """R370: N=450=2×3²×5², tau=18, omega=3, poly_c=1.8455 — FIRE#91 EXTREME armed"""
        p = compute_poly_c(370)
        self.assertEqual(p["N"], 450)
        self.assertEqual(p["tau"], 18)
        self.assertEqual(p["omega_k"], 3)
        self.assertAlmostEqual(p["poly_c"], 1.8455, places=3)
        self.assertTrue(p["fire_candidate"])
        self.assertTrue(p["high_tau"])
        # p_fire = clamp((1.8455 - 0.45) / 2.10, 0, 1) ≈ 0.664
        self.assertAlmostEqual(p["p_fire"], 0.664, places=2)


class TestPredictionEngine(unittest.TestCase):

    def test_generate_prediction_structure(self):
        pred = generate_prediction(370, V_global=14.680591, fire_count=90)
        self.assertEqual(pred["type"], "evez.a012.prediction")
        self.assertEqual(pred["round"], 370)
        self.assertIn("commitment_hash", pred)
        self.assertEqual(pred["phase"], "PHASE1_PRECOMMIT")
        self.assertAlmostEqual(pred["predicted"]["poly_c"], 1.8455, places=3)

    def test_score_prediction_kept(self):
        pred = generate_prediction(370, V_global=14.680591, fire_count=90)
        actual = {
            "round": 370,
            "poly_c": pred["predicted"]["poly_c"],  # exact match
            "fire_actual": True,
            "V": 14.829,
            "spine_hash": "abc123"
        }
        score = score_prediction(pred, actual)
        self.assertEqual(score["verdict"], "KEPT")
        self.assertAlmostEqual(score["brier"], 0.0, places=4)  # p≈0.664, actual=True → brier=(0.664-1)²≈0.113

    def test_score_brier_no_fire(self):
        pred = generate_prediction(369, V_global=14.680591, fire_count=90)
        actual = {"round": 369, "poly_c": pred["predicted"]["poly_c"], "fire_actual": False}
        score = score_prediction(pred, actual)
        # p_fire for R369 ≈ 0, fire=False → brier≈0
        self.assertAlmostEqual(score["brier"], 0.0, places=3)


class TestCoincidenceScanner(unittest.TestCase):

    def test_numeric_coincidence_detected(self):
        """V_global value appears in a JSONL record → NUMERIC hit."""
        state = {"round": 368, "V_global": 14.680591, "fire_count": 90}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            json.dump({"type": "test", "value": 14.680591, "round": 10}, f)
            f.write("\n")
            fname = f.name
        try:
            hits = scan_jsonl_for_coincidences(fname, state, 368)
            self.assertTrue(len(hits) > 0)
            types = [h["type"] for hlist in hits for h in hlist["hits"]]
            self.assertIn("NUMERIC", types)
        finally:
            os.unlink(fname)

    def test_empty_file_no_crash(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            fname = f.name
        try:
            hits = scan_jsonl_for_coincidences(fname, {"round": 368, "V_global": 14.0, "fire_count": 90}, 368)
            self.assertEqual(hits, [])
        finally:
            os.unlink(fname)

    def test_lookahead_r370_flagged(self):
        table = generate_lookahead(368, lookahead_n=5)
        fire_rounds = [r for r in table if r["fire_candidate"]]
        round_nums = [r["round"] for r in fire_rounds]
        self.assertIn(370, round_nums)

    def test_lookahead_r369_not_flagged(self):
        table = generate_lookahead(368, lookahead_n=5)
        r369 = next(r for r in table if r["round"] == 369)
        self.assertFalse(r369["fire_candidate"])
        self.assertEqual(r369["class"], "PRIME")


class TestFixedVectors(unittest.TestCase):
    """
    FIXED FIXTURES — canonical test vectors for CPF v4 Formula A.
    Any change to these values = regression.
    """

    VECTORS = [
        # (round, N, tau, omega, poly_c_expected)
        (364, 444, 12, 3, 1.238651),  # R364 FIRE#90
        (367, 447,  4, 2, 0.245947),  # R367 CPF first authoritative
        (368, 448, 14, 2, 0.859869),  # R368 HIGH_TAU NO_FIRE
        (369, 449,  2, 1, 0.054272),  # R369 prime
        (370, 450, 18, 3, 1.845549),  # R370 FIRE#91 EXTREME
    ]

    def test_all_vectors(self):
        for rnd, N_exp, tau_exp, omega_exp, pc_exp in self.VECTORS:
            p = compute_poly_c(rnd)
            self.assertEqual(p["N"], N_exp, f"R{rnd} N mismatch")
            self.assertEqual(p["tau"], tau_exp, f"R{rnd} tau mismatch")
            self.assertEqual(p["omega_k"], omega_exp, f"R{rnd} omega mismatch")
            self.assertAlmostEqual(p["poly_c"], pc_exp, places=4,
                                   msg=f"R{rnd} poly_c mismatch")


if __name__ == "__main__":
    unittest.main(verbosity=2)
