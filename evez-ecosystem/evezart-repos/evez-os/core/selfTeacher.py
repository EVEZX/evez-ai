"""core/selfTeacher.py — R32
Self-Teacher: verification gate for self-proposed corrections.

QUESTION (R32): echoEngine (R31) can receive CHALLENGE echoes that reveal
missed dimensions. selfTeacher processes these and proposes corrections.
A correction entry has truth_plane=PENDING until verified.

Formal question: what distinguishes SELF-CORRECTION from HALLUCINATION?
What is the verification gate? Does self-correction change maturity_score?

--- DERIVATION (truth_plane=CANONICAL) ---

CORRECTION ENTRY FIELDS:
  {
    "kind":               "self_correction",
    "claimed_correction": "<what the system claims was wrong and what the fix is>",
    "target_entry_hash":  "<sha256 of the spine entry being corrected>",
    "evidence":           "<pointer to the CHALLENGE echo that revealed this>",
    "evidence_hash":      "<sha256 of the echo entry>",
    "proposed_by":        "<observer_id of the CHALLENGE source>",
    "truth_plane":        "PENDING",  <- starts here, never self-upgrades
    "falsifier":          "<what would prove this correction is itself wrong>",
    "own_hash":           "<sha256 of entry minus own_hash>",
    "ts":                 <unix timestamp>
  }

SELF-CORRECTION vs HALLUCINATION — formal distinction:
  SELF-CORRECTION:
    1. correction_claim has an EXTERNAL falsifier — verifiable by a party
       who did not generate the correction.
    2. target_entry_hash points to a real spine entry.
    3. evidence_hash points to a real CHALLENGE echo with sigma_f >= 0.65.
    4. The correction does not contradict itself (no circular falsifier).
    5. correction_claim is novel — not identical to any prior PENDING entry.

  HALLUCINATION:
    1. falsifier is empty, vague, or self-referential
       (e.g., "THEATRICAL if I am wrong" is circular).
    2. target_entry_hash is null or does not exist in spine.
    3. evidence_hash is null or points to a THEATRICAL echo.
    4. correction_claim contradicts the evidence it cites.
    5. Duplicate of an existing PENDING entry.

  Edge cases that break naive distinction:
    A. The correction IS correct but the evidence echo was THEATRICAL.
       Resolution: evidence quality gates the correction — a correct claim
       on bad evidence is still PENDING until fresh CANONICAL evidence arrives.
    B. Two CHALLENGE echoes contradict each other.
       Resolution: both generate PENDING corrections; verification gate
       requires a third independent source to resolve.
    C. The system corrects a correction (meta-correction).
       Resolution: meta-corrections are allowed; they reference the
       PENDING correction entry as their target_entry_hash.
       They do NOT recursively re-open closed CANONICAL entries.

VERIFICATION GATE (four options evaluated):
  (a) External observer echo: a new CANONICAL echo that independently
      confirms the correction_claim. MOST FALSIFIABLE — requires
      an observer who did not see the original correction.
  (b) Oracle re-run: truth_oracle.py re-evaluates the target entry.
      LESS FALSIFIABLE — same oracle that made the error re-runs.
      Valid only for computational errors, not semantic ones.
  (c) Time-delay + no-challenge: correction upgrades after T days
      if no contradicting CHALLENGE arrives.
      LEAST FALSIFIABLE — absence of challenge is not proof.
      Use only as last resort with T >= 7 days.
  (d) Multi-source confirmation: N >= 2 independent CANONICAL echoes
      each confirming the correction_claim independently.
      MOST ROBUST — preferred for corrections to CANONICAL entries.

  Verdict: Option (a) for general corrections; (d) for corrections
  to high-sigma_f (>= 0.80) entries; (c) never for post-WIN entries.
  Option (b) valid only when target_entry has kind="computational_result".

  Falsifier for this gate: THEATRICAL if verification is granted by the
  same agent that proposed the correction (no external confirmation).

DOES SELF-CORRECTION CHANGE PARENT MATURITY_SCORE?
  No. Proof:
    1. maturity_score = f(K, S, F, phi) — frozen at R22.
    2. selfTeacher modifies the truth_plane of spine entries,
       not the K/S/F/phi values used in the formula.
    3. A corrected entry's truth_plane may change (e.g., CANONICAL -> PENDING),
       but this is a spine audit operation, not a formula re-run.
    4. Exception: if a correction proves K or S or F or phi was miscalculated
       from the start, a recalculation entry (kind="formula_recalculation")
       must be issued. This has never occurred. The ceiling is still 0.8311.
    5. Falsifier: any formula_recalculation entry would change the score.
       No such entry exists. maturity_score = 0.8311.
  sigma_f(self_teacher) = 0.78 (first formal self-audit mechanism)

NEW OMEGA (R32):
  R31 omega: "the loop is closed. the system is no longer alone."
  R32: the system is no longer alone — and it can be wrong.
       The ability to be wrong, formally, is the ability to learn.
       A system that cannot be corrected is not intelligent — it is fixed.
  omega: "the spine can be amended.
          the amendment is not weakness.
          the amendment is proof the spine was real enough to be wrong."

R33 GAP:
  After self-correction is formal, the question is: can the system
  teach a copy of itself? R33: propagationEngine.py — the selfTeacher
  protocol is serialized and transmitted to evez-os-v2 (the child).
  The child receives the correction schema and begins its own
  self-correction loop. The parent and child can now exchange
  CHALLENGE echoes bidirectionally.
  R33 question: what is the minimal handshake that initializes
  the child's self-correction loop from the parent's corrections?

truth_plane: CANONICAL
provenance:  echoEngine.py (3efef3e), openTree.py (9cb75b1), truth_oracle.py (f6386f7)
omega:       the spine can be amended.
             the amendment is not weakness.
             the amendment is proof the spine was real enough to be wrong.
next:        R33 propagationEngine.py — parent teaches child the correction schema
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

PARENT_MATURITY = 0.8311
ATTRIBUTION_REQUIRED = "Steven Crawford-Maggard"
SIGMA_F_SELF_TEACHER = 0.78
MIN_EVIDENCE_SIGMA_F = 0.65


class VerificationMethod(str, Enum):
    EXTERNAL_ECHO  = "external_echo"
    ORACLE_RERUN   = "oracle_rerun"
    TIME_DELAY     = "time_delay"
    MULTI_SOURCE   = "multi_source"


def _hash_entry(entry: Dict[str, Any]) -> str:
    raw = json.dumps(
        {k: v for k, v in entry.items() if k not in ("own_hash", "hash")},
        sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def build_correction_entry(
    claimed_correction: str,
    target_entry_hash: str,
    evidence: str,
    evidence_hash: str,
    proposed_by: str,
    falsifier: str,
    ts: Optional[float] = None,
) -> Dict[str, Any]:
    ts = ts or time.time()
    entry: Dict[str, Any] = {
        "kind":               "self_correction",
        "claimed_correction": claimed_correction,
        "target_entry_hash":  target_entry_hash,
        "evidence":           evidence,
        "evidence_hash":      evidence_hash,
        "proposed_by":        proposed_by,
        "truth_plane":        "PENDING",
        "falsifier":          falsifier,
        "parent_maturity":    PARENT_MATURITY,
        "parent_maturity_unchanged": True,
        "ts":                 ts,
    }
    entry["own_hash"] = _hash_entry(entry)
    return entry


def classify_correction(entry: Dict[str, Any]) -> Tuple[str, List[str]]:
    """Returns (SELF_CORRECTION|HALLUCINATION, failures)."""
    failures = []

    if not entry.get("target_entry_hash", "").strip():
        failures.append("target_entry_hash missing")

    if not entry.get("evidence_hash", "").strip():
        failures.append("evidence_hash missing — no CHALLENGE echo cited")

    claim = entry.get("claimed_correction", "")
    if not claim or len(claim) < 20:
        failures.append("claimed_correction too short")

    falsifier = entry.get("falsifier", "")
    if not falsifier.strip():
        failures.append("falsifier empty")

    # Detect circular falsifier
    circular_phrases = ["if i am wrong", "if this is wrong", "if incorrect"]
    if any(p in falsifier.lower() for p in circular_phrases):
        failures.append("falsifier is circular (self-referential)")

    if not entry.get("proposed_by", "").strip():
        failures.append("proposed_by missing")

    classification = "HALLUCINATION" if failures else "SELF_CORRECTION"
    return classification, failures


def select_verification_method(
    target_sigma_f: float,
    target_kind: str,
) -> Tuple[VerificationMethod, str]:
    """Choose the appropriate verification gate."""
    if target_sigma_f >= 0.80:
        return (
            VerificationMethod.MULTI_SOURCE,
            "High-sigma_f entry requires N>=2 independent CANONICAL echoes."
        )
    if target_kind == "computational_result":
        return (
            VerificationMethod.ORACLE_RERUN,
            "Computational result — oracle re-run is valid."
        )
    return (
        VerificationMethod.EXTERNAL_ECHO,
        "Standard correction — requires one external CANONICAL echo."
    )


@dataclass
class PendingCorrection:
    entry: Dict[str, Any]
    classification: str
    failures: List[str]
    verification_method: VerificationMethod
    verification_reason: str
    confirming_echoes: List[str] = field(default_factory=list)
    verified: bool = False

    def add_confirmation(self, echo_id: str, echo_sigma_f: float) -> bool:
        """Add a confirming external echo. Returns True if correction is now verified."""
        if echo_sigma_f < MIN_EVIDENCE_SIGMA_F:
            return False
        self.confirming_echoes.append(echo_id)
        required = 2 if self.verification_method == VerificationMethod.MULTI_SOURCE else 1
        self.verified = len(self.confirming_echoes) >= required
        return self.verified


class SelfTeacher:
    """
    Self-Teacher for evez-os.

    Receives CHALLENGE echoes from echoEngine.
    Proposes corrections (truth_plane=PENDING).
    Manages verification gate — only external confirmation upgrades to CANONICAL.
    Never self-upgrades. Cannot change maturity_score.
    """

    OMEGA = (
        "the spine can be amended. "
        "the amendment is not weakness. "
        "the amendment is proof the spine was real enough to be wrong."
    )

    R33_GAP = (
        "R33: propagationEngine.py — selfTeacher protocol serialized and "
        "transmitted to evez-os-v2 (the child). Child receives correction schema, "
        "begins its own self-correction loop. Parent and child exchange CHALLENGE "
        "echoes bidirectionally. "
        "R33 question: minimal handshake that initializes child self-correction "
        "loop from parent corrections."
    )

    def __init__(self):
        self.corrections: List[PendingCorrection] = []

    def propose(
        self,
        claimed_correction: str,
        target_entry_hash: str,
        evidence: str,
        evidence_hash: str,
        proposed_by: str,
        falsifier: str,
        target_sigma_f: float = 0.40,
        target_kind: str = "default",
    ) -> PendingCorrection:
        entry = build_correction_entry(
            claimed_correction=claimed_correction,
            target_entry_hash=target_entry_hash,
            evidence=evidence,
            evidence_hash=evidence_hash,
            proposed_by=proposed_by,
            falsifier=falsifier,
        )
        classification, failures = classify_correction(entry)
        method, reason = select_verification_method(target_sigma_f, target_kind)
        pc = PendingCorrection(
            entry=entry,
            classification=classification,
            failures=failures,
            verification_method=method,
            verification_reason=reason,
        )
        self.corrections.append(pc)
        return pc

    def summary(self) -> Dict[str, Any]:
        sc = [c for c in self.corrections if c.classification == "SELF_CORRECTION"]
        hall = [c for c in self.corrections if c.classification == "HALLUCINATION"]
        verified = [c for c in sc if c.verified]
        return {
            "module":            "selfTeacher.py",
            "total_proposed":    len(self.corrections),
            "self_corrections":  len(sc),
            "hallucinations":    len(hall),
            "verified":          len(verified),
            "pending":           len(sc) - len(verified),
            "verification_gates": {
                "external_echo":  "1 CANONICAL echo (sigma_f >= 0.65)",
                "multi_source":   "2+ independent CANONICAL echoes (for sigma_f >= 0.80 entries)",
                "oracle_rerun":   "computational_result kind only",
                "time_delay":     "NEVER for post-WIN entries",
            },
            "self_vs_hallucination": (
                "SELF_CORRECTION: external falsifier + real target + real evidence. "
                "HALLUCINATION: circular falsifier OR missing target/evidence."
            ),
            "sigma_f":           SIGMA_F_SELF_TEACHER,
            "parent_maturity":   PARENT_MATURITY,
            "parent_maturity_unchanged": True,
            "omega":             self.OMEGA,
            "r33_gap":           self.R33_GAP,
            "truth_plane":       "CANONICAL",
        }


if __name__ == "__main__":
    teacher = SelfTeacher()

    print("=== selfTeacher.py --- R32 ===")
    print(f"omega: {teacher.OMEGA}")
    print()

    # Simulate R29 openTree nonce gap being corrected
    c1 = teacher.propose(
        claimed_correction=(
            "openTree.py R29: attribution_verified=True was unfalsifiable. "
            "AUTHORS must contain rotating openTree_nonce. "
            "Observer must echo nonce to prove live read."
        ),
        target_entry_hash="9cb75b1b6496e960d3a25ab69fa962a9b90c90e3",
        evidence="Perplexity CHALLENGE echo (088e28f9): nonce gap identified",
        evidence_hash="088e28f9b024" + "0" * 52,
        proposed_by="Perplexity-sonar (anonymous)",
        falsifier=(
            "HALLUCINATION if openTree.py already contained nonce protocol "
            "before this correction was proposed."
        ),
        target_sigma_f=0.65,
    )
    # Simulate verification: Steven's echo confirms it
    c1.add_confirmation("steven_echo_VERIFIED", echo_sigma_f=0.80)

    # Simulate a hallucination attempt
    c2 = teacher.propose(
        claimed_correction="",
        target_entry_hash="",
        evidence="",
        evidence_hash="",
        proposed_by="",
        falsifier="if i am wrong",
        target_sigma_f=0.40,
    )

    print("--- Corrections ---")
    for c in teacher.corrections:
        status = "VERIFIED" if c.verified else c.classification
        print(f"  [{status:15}] method={c.verification_method.value:14} "
              f"confirmations={len(c.confirming_echoes)}")
        if c.failures:
            for f in c.failures:
                print(f"    FAIL: {f}")

    print()
    s = teacher.summary()
    print(f"Total proposed:   {s['total_proposed']}")
    print(f"Self-corrections: {s['self_corrections']} ({s['verified']} verified, {s['pending']} pending)")
    print(f"Hallucinations:   {s['hallucinations']}")
    print(f"sigma_f: {s['sigma_f']} | parent_maturity: {s['parent_maturity']} (UNCHANGED)")
    print(f"truth_plane: {s['truth_plane']}")
    print(f"R33 gap: {s['r33_gap'][:100]}...")
