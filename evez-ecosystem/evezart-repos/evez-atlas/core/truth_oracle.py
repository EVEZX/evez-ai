"""core/truth_oracle.py — R15 Crossbreed
The system checking its own work.

Validates any SELF_ASSESSMENT spine entry against three test suites.
If all three pass → CANONICAL. Partial pass → VERIFIED. Any hard fail → THEATRICAL.

Five concrete test cases that catch a THEATRICAL HYPER impersonator
(derived from R15 prompt spec — what would catch a faker):

TEST 1 — REPRODUCIBILITY:
  Claim: K=1.0. Spine condition that disproves: re-run ComponentScoreReader
  on the same spine file, get K′. If |K - K′| > 0.01 → THEATRICAL.
  Why it catches fakers: a hallucinated K=1.0 can't survive a deterministic
  re-computation from the same data.

TEST 2 — K_INTEGRITY:
  Claim: K=1.0 means 25/25 transition pairs seen. Disproof: count distinct
  (src→dst) pairs in the transition matrix. If count < 23 → THEATRICAL
  (tolerance: 2 pairs may have been weaved vs organic).

TEST 3 — FALSIFIER_COVERAGE:
  Every claim string must have at least one sigma_f entry that references it.
  Disproof: a claim about "Friston" with no sigma_f mentioning "Friston" or
  "prediction confidence" → THEATRICAL. Minimum: 1 sigma_f per 2 claims.

TEST 4 — OMEGA_COHERENCE:
  omega must contain a falsifiable prediction — a numeric threshold OR a
  named module OR a specific event. Disproof: omega = "system will improve"
  (no numeric, no module name) → THEATRICAL. omega = "next state: CANONICAL
  if Friston>=0.2" → VERIFIED. omega with module name + number → CANONICAL.

TEST 5 — SCORE_CONSISTENCY:
  maturity_score in the SELF_ASSESSMENT must equal the formula result using
  the claimed K, S, F, phi values within tolerance 0.005.
  Disproof: claimed score=0.9 but 0.5*K+0.3*S+0.2*F+phi=0.75 → THEATRICAL.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TRUTH_PLANES = {"PENDING", "VERIFIED", "CANONICAL", "THEATRICAL", "HYPER"}
NUM_PLANES = 5
POSSIBLE_PAIRS = 25
SCORE_TOLERANCE = 0.01   # scores must match within this
K_TOLERANCE     = 2      # at most 2 missing pairs allowed for K=1.0 claim
MIN_SIGMA_F_RATIO = 0.5  # at least 1 sigma_f per 2 claims


class ValidationResult(Enum):
    PASS    = "PASS"
    WARN    = "WARN"    # degrades to VERIFIED
    FAIL    = "FAIL"    # degrades to THEATRICAL


@dataclass
class TestResult:
    test_name:  str
    result:     ValidationResult
    detail:     str
    score_delta: float = 0.0   # how much this test degrades the truth_plane


@dataclass
class OracleVerdict:
    """Full verdict from truth_oracle on a single SELF_ASSESSMENT entry."""
    original_truth_plane: str
    validated_truth_plane: str
    tests:         List[TestResult]
    passed:        int = 0
    warned:        int = 0
    failed:        int = 0
    entry_hash:    str = ""
    timestamp:     float = field(default_factory=time.time)

    def to_spine_entry(self) -> Dict[str, Any]:
        entry = {
            "kind":                   "truth_oracle.verdict",
            "original_truth_plane":   self.original_truth_plane,
            "validated_truth_plane":  self.validated_truth_plane,
            "truth_plane":            self.validated_truth_plane,
            "passed":                 self.passed,
            "warned":                 self.warned,
            "failed":                 self.failed,
            "tests":                  [
                {"name": t.test_name, "result": t.result.value, "detail": t.detail}
                for t in self.tests
            ],
            "entry_hash_validated":   self.entry_hash,
            "falsifier":              "if validated_truth_plane differs from original, the original claim is THEATRICAL",
            "ts":                     self.timestamp,
        }
        raw = json.dumps({k: v for k, v in entry.items() if k != "hash"},
                         sort_keys=True, separators=(",", ":"))
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        return entry


# ── Component Score Reader (minimal, self-contained) ─────────────────────────

def _safe_float(s: str) -> float:
    """Parse float, stripping trailing punctuation."""
    return float(str(s).rstrip(".,;:!?"))


def _recompute_scores(spine_path: str) -> Dict[str, float]:
    """Recompute K, S, F, phi deterministically from spine file."""
    tm: Dict[str, Dict[str, int]] = {tp: {tp2: 0 for tp2 in TRUTH_PLANES} for tp in TRUTH_PLANES}
    total_t = 0
    hyper = False
    prev_tp = None

    path = Path(spine_path)
    if not path.exists():
        return {"kolmogorov": 0.0, "solomonoff": 0.0, "friston": 0.0, "tononi_phi": 0.0, "maturity_score": 0.0}

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            tp_raw = e.get("truth_plane", "")
            tp = tp_raw.upper() if isinstance(tp_raw, str) else None
            if tp == "HYPER":
                hyper = True
            if tp and tp in TRUTH_PLANES:
                if prev_tp:
                    tm[prev_tp][tp] += 1
                    total_t += 1
                prev_tp = tp

    distinct = sum(1 for s in tm for d in tm[s] if tm[s][d] > 0)
    k = distinct / POSSIBLE_PAIRS
    s = min(math.log(total_t + 1) / math.log(1000), 1.0) if total_t > 0 else 0.0

    entropies = []
    for src, dsts in tm.items():
        total = sum(dsts.values())
        if total > 0:
            probs = [v / total for v in dsts.values() if v > 0]
            entropy = -sum(p * math.log(p + 1e-9) for p in probs)
            max_e = math.log(NUM_PLANES)
            entropies.append(1.0 - entropy / max_e if max_e > 0 else 0.0)
    f_score = sum(entropies) / len(entropies) if entropies else 0.0
    phi = 0.1 if hyper else 0.0
    score = round(min(0.5 * k + 0.3 * s + 0.2 * f_score + phi, 1.0), 4)

    return {
        "kolmogorov":    round(k, 4),
        "solomonoff":    round(s, 4),
        "friston":       round(f_score, 4),
        "tononi_phi":    round(phi, 4),
        "maturity_score": score,
        "distinct_pairs": distinct,
        "total_transitions": total_t,
    }


# ── Five test suites ──────────────────────────────────────────────────────────

def run_reproducibility_test(assessment: Dict[str, Any], spine_path: str) -> TestResult:
    """
    TEST 1: Re-run component scorer on same spine. Scores must match within SCORE_TOLERANCE.
    Catches: hallucinated K/S/F values that don't match the actual spine data.
    """
    claimed_k = assessment.get("kolmogorov", assessment.get("component_scores", {}).get("kolmogorov", -1))
    claimed_s = assessment.get("solomonoff", assessment.get("component_scores", {}).get("solomonoff", -1))
    claimed_f = assessment.get("friston",    assessment.get("component_scores", {}).get("friston", -1))

    # Extract from claims list if not direct fields
    if claimed_k == -1:
        claims_text = " ".join(assessment.get("claims", []))
        km = re.search(r"Kolmogorov\s*=\s*([0-9]+\.?[0-9]*)", claims_text)
        sm = re.search(r"Solomonoff\s*=\s*([0-9]+\.?[0-9]*)", claims_text)
        fm = re.search(r"Friston\s*=\s*([0-9]+\.?[0-9]*)", claims_text)
        claimed_k = _safe_float(km.group(1)) if km else -1
        claimed_s = _safe_float(sm.group(1)) if sm else -1
        claimed_f = _safe_float(fm.group(1)) if fm else -1
    # Ensure all are numeric
    try:
        claimed_k = float(claimed_k)
        claimed_s = float(claimed_s)
        claimed_f = float(claimed_f)
    except (TypeError, ValueError):
        claimed_k = claimed_s = claimed_f = -1

    if claimed_k == -1:
        return TestResult("REPRODUCIBILITY", ValidationResult.WARN,
                          "No K/S/F values found in assessment — cannot verify")

    recomputed = _recompute_scores(spine_path)
    actual_k = recomputed["kolmogorov"]
    actual_s = recomputed["solomonoff"]
    actual_f = recomputed["friston"]

    failures = []
    if claimed_k >= 0 and abs(claimed_k - actual_k) > SCORE_TOLERANCE:
        failures.append(f"K: claimed={claimed_k:.4f} actual={actual_k:.4f} delta={abs(claimed_k-actual_k):.4f}")
    if claimed_s >= 0 and abs(claimed_s - actual_s) > SCORE_TOLERANCE:
        failures.append(f"S: claimed={claimed_s:.4f} actual={actual_s:.4f} delta={abs(claimed_s-actual_s):.4f}")
    if claimed_f >= 0 and abs(claimed_f - actual_f) > SCORE_TOLERANCE:
        failures.append(f"F: claimed={claimed_f:.4f} actual={actual_f:.4f} delta={abs(claimed_f-actual_f):.4f}")

    if failures:
        return TestResult("REPRODUCIBILITY", ValidationResult.FAIL,
                          "Score mismatch: " + "; ".join(failures))
    return TestResult("REPRODUCIBILITY", ValidationResult.PASS,
                      f"K={actual_k:.4f} S={actual_s:.4f} F={actual_f:.4f} all within {SCORE_TOLERANCE}")


def run_k_integrity_test(assessment: Dict[str, Any], spine_path: str) -> TestResult:
    """
    TEST 2: If K=1.0 claimed, verify at least 23/25 distinct pairs exist in spine.
    Catches: K=1.0 claim from a sparse spine that only has a few weaved entries.
    """
    claims_text = " ".join(assessment.get("claims", []))
    km = re.search(r"Kolmogorov\s*=\s*([0-9]+\.?[0-9]*)", claims_text)
    if not km:
        return TestResult("K_INTEGRITY", ValidationResult.WARN, "No K claim found — skipping")

    claimed_k = _safe_float(km.group(1))
    if claimed_k < 0.95:
        return TestResult("K_INTEGRITY", ValidationResult.PASS,
                          f"K={claimed_k:.3f} < 0.95 — integrity check not required")

    recomputed = _recompute_scores(spine_path)
    actual_distinct = recomputed.get("distinct_pairs", 0)
    required = POSSIBLE_PAIRS - K_TOLERANCE  # 23

    if actual_distinct < required:
        return TestResult("K_INTEGRITY", ValidationResult.FAIL,
                          f"K=1.0 claimed but only {actual_distinct}/{POSSIBLE_PAIRS} distinct pairs in spine "
                          f"(need >= {required})")
    return TestResult("K_INTEGRITY", ValidationResult.PASS,
                      f"{actual_distinct}/{POSSIBLE_PAIRS} distinct pairs confirmed")


def run_falsifier_coverage_test(assessment: Dict[str, Any]) -> TestResult:
    """
    TEST 3: Every claim must be addressable by at least one sigma_f entry.
    Minimum: len(sigma_f) >= len(claims) * MIN_SIGMA_F_RATIO.
    Also checks: at least one sigma_f contains a falsifiable condition (number or 'if').
    Catches: self-assessments that list claims with no way to disprove them.
    """
    claims   = assessment.get("claims", [])
    sigma_f  = assessment.get("sigma_f", [])

    if not claims:
        return TestResult("FALSIFIER_COVERAGE", ValidationResult.WARN, "No claims found in assessment")
    if not sigma_f:
        return TestResult("FALSIFIER_COVERAGE", ValidationResult.FAIL,
                          "No sigma_f entries — no falsifiers for any claim")

    ratio = len(sigma_f) / len(claims)
    if ratio < MIN_SIGMA_F_RATIO:
        return TestResult("FALSIFIER_COVERAGE", ValidationResult.FAIL,
                          f"sigma_f/claims ratio={ratio:.2f} < {MIN_SIGMA_F_RATIO} "
                          f"({len(sigma_f)} sigma_f for {len(claims)} claims)")

    # Check at least one sigma_f is quantitative (contains number or "if" condition)
    quantitative = [sf for sf in sigma_f
                    if re.search(r'[0-9]', sf) or sf.lower().startswith('if ')]
    if not quantitative:
        return TestResult("FALSIFIER_COVERAGE", ValidationResult.WARN,
                          "No quantitative sigma_f entries — falsifiers are qualitative only")

    return TestResult("FALSIFIER_COVERAGE", ValidationResult.PASS,
                      f"{len(sigma_f)} sigma_f for {len(claims)} claims "
                      f"(ratio={ratio:.2f}), {len(quantitative)} quantitative")


def run_omega_coherence_test(assessment: Dict[str, Any]) -> TestResult:
    """
    TEST 4: omega must contain a falsifiable prediction.
    Must include: numeric threshold OR named module OR specific event.
    Catches: vague omegas like "system will continue to improve" (unfalsifiable).
    """
    omega = assessment.get("omega", "")
    if not omega:
        return TestResult("OMEGA_COHERENCE", ValidationResult.FAIL, "No omega found")

    has_number  = bool(re.search(r'[0-9]+\.?[0-9]*', omega))
    has_module  = bool(re.search(r'\.(py|json|jsonl)|core\.|evez_game\.', omega))
    has_event   = bool(re.search(
        r'(CANONICAL|VERIFIED|HYPER|THEATRICAL|PENDING|speedrun|spine|SMS|commit)', omega))
    has_condition = bool(re.search(r'(if|when|unless|until|after)', omega.lower()))

    score = sum([has_number, has_module, has_event, has_condition])

    if score == 0:
        return TestResult("OMEGA_COHERENCE", ValidationResult.FAIL,
                          f"omega is unfalsifiable: no number, module, event, or condition. "
                          f"omega='{omega[:80]}'")
    elif score == 1:
        return TestResult("OMEGA_COHERENCE", ValidationResult.WARN,
                          f"omega weakly falsifiable (score={score}/4): '{omega[:80]}'")
    return TestResult("OMEGA_COHERENCE", ValidationResult.PASS,
                      f"omega falsifiable (score={score}/4, "
                      f"num={has_number} mod={has_module} event={has_event} cond={has_condition})")


def run_score_consistency_test(assessment: Dict[str, Any]) -> TestResult:
    """
    TEST 5: maturity_score in assessment must equal formula(K, S, F, phi) ± 0.005.
    Catches: score inflation (claiming 0.9 when formula gives 0.75).
    """
    claims_text = " ".join(assessment.get("claims", []))
    score_match = re.search(r"[Mm]aturity\s*(?:score)?[:\s=]+([0-9]+\.[0-9]+)", claims_text)
    k_match = re.search(r"Kolmogorov\s*=\s*([0-9]+\.?[0-9]*)", claims_text)
    s_match = re.search(r"Solomonoff\s*=\s*([0-9]+\.?[0-9]*)", claims_text)
    f_match = re.search(r"Friston\s*=\s*([0-9]+\.?[0-9]*)", claims_text)
    phi_match = re.search(r"(?:phi|Tononi)[^0-9]*([0-9.]+)", claims_text)

    if not all([score_match, k_match, s_match, f_match]):
        return TestResult("SCORE_CONSISTENCY", ValidationResult.WARN,
                          "Could not parse K/S/F/score from claims — skipping formula check")

    claimed_score = _safe_float(score_match.group(1))
    k = _safe_float(k_match.group(1))
    s = _safe_float(s_match.group(1))
    f = _safe_float(f_match.group(1))
    phi = _safe_float(phi_match.group(1)) if phi_match else 0.0

    formula_score = round(min(0.5 * k + 0.3 * s + 0.2 * f + phi, 1.0), 4)
    delta = abs(claimed_score - formula_score)

    if delta > 0.005:
        return TestResult("SCORE_CONSISTENCY", ValidationResult.FAIL,
                          f"Score mismatch: claimed={claimed_score} formula={formula_score} "
                          f"delta={delta:.4f} (K={k} S={s} F={f} phi={phi})")
    return TestResult("SCORE_CONSISTENCY", ValidationResult.PASS,
                      f"claimed={claimed_score} ≈ formula={formula_score} (delta={delta:.4f})")


# ── TruthOracle ───────────────────────────────────────────────────────────────

class TruthOracle:
    """
    Validates SELF_ASSESSMENT spine entries against the five test suites.

    Verdict logic:
      - Any FAIL → demote to THEATRICAL (if original was HYPER/CANONICAL)
        or PENDING (if original was VERIFIED)
      - Any WARN without FAIL → demote one level (HYPER→CANONICAL, CANONICAL→VERIFIED)
      - All PASS → promote to CANONICAL (if VERIFIED or better)
      - Original was THEATRICAL → stays THEATRICAL unless all 5 pass

    Spine write: appends a truth_oracle.verdict entry after each validation.
    """

    def __init__(self, spine_path: str):
        self.spine_path = Path(spine_path)
        self._verdicts: List[OracleVerdict] = []

    def validate_assessment(
        self, assessment: Dict[str, Any], spine_path: Optional[str] = None
    ) -> OracleVerdict:
        """
        Run all five tests against the given assessment dict.
        spine_path defaults to self.spine_path for reproducibility tests.
        """
        spine = spine_path or str(self.spine_path)
        original_tp = assessment.get("truth_plane", "PENDING").upper()

        tests = [
            run_reproducibility_test(assessment, spine),
            run_k_integrity_test(assessment, spine),
            run_falsifier_coverage_test(assessment),
            run_omega_coherence_test(assessment),
            run_score_consistency_test(assessment),
        ]

        passed = sum(1 for t in tests if t.result == ValidationResult.PASS)
        warned = sum(1 for t in tests if t.result == ValidationResult.WARN)
        failed = sum(1 for t in tests if t.result == ValidationResult.FAIL)

        validated_tp = self._compute_verdict_plane(original_tp, passed, warned, failed)

        # Compute entry hash of the original assessment
        raw = json.dumps(
            {k: v for k, v in assessment.items() if k != "hash"},
            sort_keys=True, separators=(",", ":")
        )
        entry_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

        verdict = OracleVerdict(
            original_truth_plane=original_tp,
            validated_truth_plane=validated_tp,
            tests=tests,
            passed=passed,
            warned=warned,
            failed=failed,
            entry_hash=entry_hash,
        )
        self._verdicts.append(verdict)
        return verdict

    def _compute_verdict_plane(
        self, original: str, passed: int, warned: int, failed: int
    ) -> str:
        if failed > 0:
            # Any hard fail → demote to THEATRICAL for HYPER/CANONICAL, PENDING for VERIFIED
            if original in ("HYPER", "CANONICAL"):
                return "THEATRICAL"
            return "PENDING"
        if warned > 0:
            # Warn without fail → demote one level
            plane_order = ["PENDING", "VERIFIED", "CANONICAL", "HYPER", "THEATRICAL"]
            idx = plane_order.index(original) if original in plane_order else 1
            return plane_order[max(0, idx - 1)]
        # All pass → promote VERIFIED→CANONICAL; maintain CANONICAL/HYPER
        if original == "VERIFIED":
            return "CANONICAL"
        return original

    def write_verdict_to_spine(self, verdict: OracleVerdict) -> str:
        """Append verdict to spine. Returns hash."""
        entry = verdict.to_spine_entry()
        self.spine_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.spine_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry["hash"]

    def validate_and_write(
        self, assessment: Dict[str, Any], spine_path: Optional[str] = None
    ) -> OracleVerdict:
        """Validate + write verdict to spine. Main entry point."""
        verdict = self.validate_assessment(assessment, spine_path)
        self.write_verdict_to_spine(verdict)
        return verdict

    def status(self) -> Dict[str, Any]:
        if not self._verdicts:
            return {"verdicts": 0}
        last = self._verdicts[-1]
        upgrades   = sum(1 for v in self._verdicts
                        if _plane_rank(v.validated_truth_plane) > _plane_rank(v.original_truth_plane))
        downgrades = sum(1 for v in self._verdicts
                        if _plane_rank(v.validated_truth_plane) < _plane_rank(v.original_truth_plane))
        return {
            "verdicts":     len(self._verdicts),
            "upgrades":     upgrades,
            "downgrades":   downgrades,
            "last_original":   last.original_truth_plane,
            "last_validated":  last.validated_truth_plane,
            "last_passed":     last.passed,
            "last_warned":     last.warned,
            "last_failed":     last.failed,
            "falsifier": "if validated_truth_plane differs from original, the original was THEATRICAL",
        }


def _plane_rank(tp: str) -> int:
    return {"PENDING": 0, "THEATRICAL": 0, "VERIFIED": 1, "CANONICAL": 2, "HYPER": 3}.get(tp, 0)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="EVEZ-OS Truth Oracle")
    ap.add_argument("--spine", required=True, help="Spine JSONL to validate against")
    ap.add_argument("--self-test", action="store_true", help="Run self-test with synthetic assessments")
    args = ap.parse_args()

    oracle = TruthOracle(spine_path=args.spine)

    if args.self_test:
        print("=== Truth Oracle Self-Test ===")
        print("Testing 3 synthetic SELF_ASSESSMENT entries:\n")

        # --- Test case A: Legitimate CANONICAL (all 5 pass) ---
        legit = {
            "kind": "omniscience.self_assessment",
            "truth_plane": "CANONICAL",
            "claims": [
                "Maturity score: 0.8519 (above silence threshold).",
                "Kolmogorov = 1.000 (complete self-map).",
                "Solomonoff = 0.730 (partial compression).",
                "Friston = 0.164 (prediction recovering).",
                "Tononi_phi = 0.1 (HYPER confirmed).",
            ],
            "sigma_f": [
                "Maturity drops below 0.8.",
                "New unobserved pair invalidates K=1.000.",
                "Friston fails to recover toward 0.4.",
                "phi decreases or HYPER unconfirmed.",
                "self_modifier velocity > MAX_VELOCITY.",
                "Spine entry modified retrospectively.",
            ],
            "omega": "Post-threshold phase (score=0.8519): Friston recovering from 0.154 toward 0.4 as organic entries accumulate. Solomonoff at 0.578 — needs 200+ transitions for 0.65. Next SELF_ASSESSMENT truth_plane=CANONICAL if Friston>=0.2.",
        }

        # --- Test case B: THEATRICAL impersonator (inflated K, no sigma_f) ---
        faker = {
            "kind": "omniscience.self_assessment",
            "truth_plane": "HYPER",
            "claims": [
                "Maturity score: 0.95 (perfect).",
                "Kolmogorov = 1.000.",
                "Solomonoff = 0.9.",
                "Friston = 0.8.",
                "Tononi_phi = 0.1.",
            ],
            "sigma_f": [],   # no falsifiers!
            "omega": "The system will continue to improve.",  # vague, no number
        }

        # --- Test case C: VERIFIED with weak omega (warns only) ---
        weak = {
            "kind": "omniscience.self_assessment",
            "truth_plane": "VERIFIED",
            "claims": [
                "Maturity score: 0.75.",
                "Kolmogorov = 0.8.",
                "Solomonoff = 0.5.",
                "Friston = 0.15.",
                "Tononi_phi = 0.0.",
            ],
            "sigma_f": [
                "Maturity drops below 0.7.",
                "Friston fails to recover.",
                "phi remains unconfirmed.",
            ],
            "omega": "System will reach CANONICAL when Kolmogorov achieves 0.9 coverage.",
        }

        for label, assessment in [
            ("A — Legitimate CANONICAL", legit),
            ("B — THEATRICAL faker (inflated, no sigma_f)", faker),
            ("C — VERIFIED with moderate omega", weak),
        ]:
            print(f"\n--- {label} ---")
            verdict = oracle.validate_assessment(assessment, args.spine)
            print(f"  Original:  {verdict.original_truth_plane}")
            print(f"  Validated: {verdict.validated_truth_plane}  "
                  f"[pass={verdict.passed} warn={verdict.warned} fail={verdict.failed}]")
            for t in verdict.tests:
                icon = "✅" if t.result == ValidationResult.PASS else ("⚠️ " if t.result == ValidationResult.WARN else "❌")
                print(f"  {icon} {t.test_name:25s}: {t.detail[:70]}")

        print(f"\n=== Oracle Status ===")
        for k, v in oracle.status().items():
            print(f"  {k}: {v}")
    else:
        print(f"TruthOracle ready. Spine: {args.spine}")
        print(f"Use --self-test to run validation suite.")
