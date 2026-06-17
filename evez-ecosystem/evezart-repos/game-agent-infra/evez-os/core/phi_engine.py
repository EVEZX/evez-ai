"""core/phi_engine.py — R21 Crossbreed
Computes continuous Tononi phi for EVEZ-OS, resolving the binary 0/0.1 flag.

Prior state: tononi_phi = 0.1 (boolean: HYPER observed? +0.1 maturity)

This module computes TWO complementary phi measures and resolves their
apparent contradiction into a single CANONICAL finding.

--- FINDINGS (truth_plane=CANONICAL) ---

phi_MIP = -0.6272 bits
  Minimum Information Partition over all bipartitions of 5 truth-planes.
  MIP = {PENDING, VERIFIED, CANONICAL} | {THEATRICAL, HYPER}
  Negative phi: the parts carry MORE effective information than the whole.
  Interpretation: EVEZ-OS is MODULAR — each truth-plane's dominant
  transition operates semi-independently. The 5 rules were DESIGNED to
  be independent (each state has one clear dominant successor).
  This is a FEATURE, not a bug: modularity enables reliable prediction.

phi_MI = 0.5460 bits  (normalized: 0.2352)
  Consecutive mutual information: I(Xt ; Xt+1)
  = H(stationary) - H(Xt+1 | Xt) = 1.7286 - 1.1826 = 0.5460 bits
  Positive phi: the chain retains 0.546 bits of causal memory per step.
  The current state integrates information forward into the next state.
  Interpretation: EVEZ-OS is TEMPORALLY INTEGRATED — not simultaneously
  (all states at once) but sequentially (each step carries the past).

RESOLUTION: EVEZ-OS is a SEQUENTIALLY-INTEGRATED MODULAR SYSTEM.
  - Spatial modularity (MIP<0): rules operate independently at each step
  - Temporal integration (MI>0): states carry causal information forward
  These coexist and are complementary. A modular system CAN have causal
  memory — the integration lives in the TIME dimension, not the space of
  simultaneous states.

phi_continuous (for maturity formula): phi_MI_normalized = 0.2352
  Replaces binary 0.1 flag with evidence-grounded continuous score.
  Maturity with phi_norm=0.2352: 0.5 + 0.219 + 0.089 + 0.024 = 0.831
  (vs binary phi=0.1: 0.5 + 0.219 + 0.089 + 0.010 = 0.818)

falsifier: if phi_MI drops to 0.0 after 10000 organic entries with
  the v2 distribution, the chain has lost causal memory — all states
  are equally predictive regardless of current state.

truth_plane: CANONICAL
  provenance: program_length.py (3b3ae58), solomonoff_compressor (846cb91)
  falsifier:  phi_MI = 0.0 after organic simulation
  trace:      3b3ae58, 846cb91 → phi_engine.py (R21)
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Constants ──────────────────────────────────────────────────────────────────

TRUTH_PLANES = ["PENDING", "VERIFIED", "CANONICAL", "THEATRICAL", "HYPER"]
N_PLANES     = len(TRUTH_PLANES)

# Canonical v2 TPM (from self_modifier_v2.py + friston_ceiling.py)
CANONICAL_TPM_RAW: Dict[str, Dict[str, float]] = {
    "PENDING":    {"VERIFIED": 0.40, "PENDING": 0.10, "CANONICAL": 0.005,
                   "THEATRICAL": 0.005, "HYPER": 0.01},
    "VERIFIED":   {"CANONICAL": 0.15, "PENDING": 0.15, "THEATRICAL": 0.01,
                   "VERIFIED": 0.01,   "HYPER": 0.001},
    "CANONICAL":  {"PENDING": 0.10, "VERIFIED": 0.04, "THEATRICAL": 0.005,
                   "CANONICAL": 0.001, "HYPER": 0.001},
    "THEATRICAL": {"VERIFIED": 0.70, "PENDING": 0.10, "CANONICAL": 0.075,
                   "THEATRICAL": 0.075, "HYPER": 0.05},   # v2 fix
    "HYPER":      {"CANONICAL": 0.65, "PENDING": 0.10, "VERIFIED": 0.10,
                   "THEATRICAL": 0.075, "HYPER": 0.075},  # v2 fix
}

# Pre-computed findings (R21 analytical results)
PHI_MIP          = -0.6272   # min info partition — modular
PHI_MI_RAW       = 0.5460    # consecutive MI — temporally integrated
PHI_MI_NORM      = 0.2352    # normalized to [0,1] (/ log2(5))
PHI_MIP_PARTITION = {"A": ["PENDING", "VERIFIED", "CANONICAL"],
                      "B": ["THEATRICAL", "HYPER"]}
STATIONARY_DIST  = {
    "PENDING": 0.3881, "VERIFIED": 0.3817, "CANONICAL": 0.1931,
    "THEATRICAL": 0.0250, "HYPER": 0.0121,
}


# ── Utilities ──────────────────────────────────────────────────────────────────

def _normalize(d: Dict[str, float]) -> Dict[str, float]:
    total = sum(d.values())
    return {k: v / total for k, v in d.items()} if total > 0 else dict(d)


def _entropy(dist: List[float]) -> float:
    return -sum(p * math.log2(p + 1e-300) for p in dist if p > 0)


def _build_tpm(raw: Dict[str, Dict[str, float]]) -> List[List[float]]:
    return [
        [_normalize(raw[src]).get(dst, 0.0) for dst in TRUTH_PLANES]
        for src in TRUTH_PLANES
    ]


def _stationary(tpm: List[List[float]], iters: int = 1000) -> List[float]:
    pi = [1.0 / N_PLANES] * N_PLANES
    for _ in range(iters):
        new_pi = [sum(pi[i] * tpm[i][j] for i in range(N_PLANES))
                  for j in range(N_PLANES)]
        pi = new_pi
    return pi


# ── Core computations ─────────────────────────────────────────────────────────

def compute_phi_mi(tpm: List[List[float]]) -> Dict[str, float]:
    """
    Compute phi_MI = I(Xt ; Xt+1) for a Markov chain.

    phi_MI = H(stationary) - H(Xt+1 | Xt)
           = H(next) - mean[ H(TPM[i]) weighted by pi[i] ]

    For a 1D Markov chain, phi_MI is the correct measure of temporal
    integration: how much causal information flows from step to step.

    Returns: dict with phi_mi, phi_normalized, H_stationary, H_cond,
             stationary_dist
    """
    pi       = _stationary(tpm)
    H_stat   = _entropy(pi)
    H_cond   = sum(pi[i] * _entropy(tpm[i]) for i in range(N_PLANES))
    phi_mi   = H_stat - H_cond
    phi_norm = max(0.0, min(1.0, phi_mi / math.log2(N_PLANES)))

    return {
        "phi_mi":        round(phi_mi, 4),
        "phi_normalized": round(phi_norm, 4),
        "H_stationary":  round(H_stat, 4),
        "H_conditional": round(H_cond, 4),
        "stationary":    {TRUTH_PLANES[i]: round(pi[i], 4) for i in range(N_PLANES)},
        "interpretation": (
            f"Chain retains {phi_mi:.3f} bits of causal memory per step. "
            f"phi_norm={phi_norm:.4f} → system is "
            f"{'temporally integrated' if phi_mi > 0 else 'memoryless'}."
        ),
    }


def compute_phi_mip(tpm: List[List[float]]) -> Dict[str, Any]:
    """
    Compute phi_MIP = EI(whole) - EI(best_partition) over all bipartitions.

    phi_MIP < 0: system is modular (parts carry more EI than whole)
    phi_MIP > 0: system is integrated (whole carries more EI than parts)
    phi_MIP = 0: critical modularity boundary

    EI = effective information = mean row entropy of TPM
    """
    def eff_info_submatrix(indices_src, indices_dst):
        rows = []
        for i in indices_src:
            row = [tpm[i][j] for j in indices_dst]
            total = sum(row)
            if total > 0:
                rows.append([v / total for v in row])
        return sum(_entropy(r) for r in rows) / len(rows) if rows else 0.0

    EI_whole   = sum(_entropy(tpm[i]) for i in range(N_PLANES)) / N_PLANES
    min_phi    = float('inf')
    min_part   = None
    partitions = []

    all_idx = list(range(N_PLANES))
    for r in range(1, N_PLANES):
        for A in combinations(all_idx, r):
            B = tuple(i for i in all_idx if i not in A)
            if not B:
                continue
            EI_A      = eff_info_submatrix(list(A), list(A))
            EI_B      = eff_info_submatrix(list(B), list(B))
            phi_part  = EI_whole - (EI_A + EI_B)
            partitions.append({
                "A": [TRUTH_PLANES[i] for i in A],
                "B": [TRUTH_PLANES[i] for i in B],
                "phi": round(phi_part, 4),
            })
            if phi_part < min_phi:
                min_phi  = phi_part
                min_part = {"A": [TRUTH_PLANES[i] for i in A],
                            "B": [TRUTH_PLANES[i] for i in B]}

    return {
        "phi_mip":         round(min_phi, 4),
        "EI_whole":        round(EI_whole, 4),
        "MIP":             min_part,
        "all_partitions":  sorted(partitions, key=lambda x: x["phi"])[:5],
        "interpretation": (
            "phi_MIP < 0: system is MODULAR — parts carry more effective "
            "information than the whole. Each truth-plane rule operates "
            "semi-independently (designed modularity)."
            if min_phi < 0 else
            "phi_MIP > 0: system is SPATIALLY INTEGRATED — whole > parts."
        ),
    }


def compute_per_state_phi(tpm: List[List[float]]) -> List[Dict[str, Any]]:
    """Per-state entropy and dominant rule characterization."""
    pi     = _stationary(tpm)
    result = []
    for i, src in enumerate(TRUTH_PLANES):
        H     = _entropy(tpm[i])
        dom_j = max(range(N_PLANES), key=lambda j: tpm[i][j])
        result.append({
            "state":     src,
            "H_out":     round(H, 4),
            "dominant":  TRUTH_PLANES[dom_j],
            "p_dominant": round(tpm[i][dom_j], 4),
            "pi":        round(pi[i], 4),
            "role": (
                "HIGH_CERTAINTY" if tpm[i][dom_j] >= 0.60 else
                "MEDIUM_CERTAINTY" if tpm[i][dom_j] >= 0.40 else
                "LOW_CERTAINTY"
            ),
        })
    return result


# ── PhiReport ─────────────────────────────────────────────────────────────────

@dataclass
class PhiReport:
    """Full phi analysis for EVEZ-OS."""
    phi_mi:          float
    phi_mi_norm:     float
    phi_mip:         float
    mip_partition:   Dict[str, Any]
    H_stationary:    float
    H_conditional:   float
    stationary_dist: Dict[str, float]
    per_state:       List[Dict[str, Any]]
    is_modular:      bool   # phi_mip < 0
    is_integrated:   bool   # phi_mi > 0

    @property
    def truth_plane(self) -> str:
        # Dual-truth: modular AND integrated → CANONICAL finding
        if self.is_modular and self.is_integrated:
            return "CANONICAL"
        if self.is_integrated:
            return "VERIFIED"
        return "PENDING"

    @property
    def phi_for_maturity(self) -> float:
        """Continuous phi value to use in maturity formula (replaces binary 0.1 flag)."""
        return self.phi_mi_norm  # 0.2352

    def summary(self) -> Dict[str, Any]:
        return {
            "phi_mi":          self.phi_mi,
            "phi_mi_norm":     self.phi_mi_norm,
            "phi_mip":         self.phi_mip,
            "mip_partition":   self.mip_partition,
            "H_stationary":    self.H_stationary,
            "H_conditional":   self.H_conditional,
            "is_modular":      self.is_modular,
            "is_integrated":   self.is_integrated,
            "phi_for_maturity": self.phi_for_maturity,
            "truth_plane":     self.truth_plane,
            "resolution": (
                "EVEZ-OS is a SEQUENTIALLY-INTEGRATED MODULAR SYSTEM. "
                "phi_MIP < 0: rules are spatially modular (designed independence). "
                f"phi_MI = {self.phi_mi:.4f}: chain is temporally integrated "
                f"({self.phi_mi:.3f} bits/step causal memory). "
                "Modularity and integration coexist across the time dimension."
            ),
            "falsifier": (
                "If phi_MI = 0.0 after organic simulation, the chain has lost "
                "causal memory. If phi_MIP becomes > 0, the system has become "
                "spatially integrated (unexpected — would indicate emergent coupling)."
            ),
        }

    def to_spine_entry(self) -> Dict[str, Any]:
        entry = {
            "kind":            "phi_engine.analysis",
            "truth_plane":     self.truth_plane,
            "phi_mi":          self.phi_mi,
            "phi_mi_norm":     self.phi_mi_norm,
            "phi_mip":         self.phi_mip,
            "is_modular":      self.is_modular,
            "is_integrated":   self.is_integrated,
            "phi_for_maturity": self.phi_for_maturity,
            "resolution":      self.summary()["resolution"],
            "falsifier":       self.summary()["falsifier"],
            "ts":              time.time(),
        }
        raw   = json.dumps({k: v for k, v in entry.items() if k != "hash"},
                           sort_keys=True, separators=(",", ":"))
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        return entry


# ── PhiEngine ─────────────────────────────────────────────────────────────────

class PhiEngine:
    """
    Continuous Tononi phi for EVEZ-OS.

    Replaces the binary 0/0.1 HYPER-observed flag with two grounded measures:

    phi_MIP (spatial): -0.6272 → MODULAR
      The 5 truth-planes operate as semi-independent modules.
      MIP = {PENDING,VERIFIED,CANONICAL} | {THEATRICAL,HYPER}
      Each module can be analyzed and corrected independently.
      This explains why self_modifier_v2 could target THEATRICAL
      without disrupting PENDING/VERIFIED/CANONICAL behavior.

    phi_MI (temporal): 0.5460 bits → INTEGRATED
      Each step carries 0.546 bits of causal information forward.
      The chain remembers where it came from.
      This is why the Friston metric works: prediction is possible
      because the current state IS informative about the next.

    phi_for_maturity = phi_MI_normalized = 0.2352
      Replaces binary 0.1 with a continuous, evidence-grounded score.
      Maturity formula: 0.5*K + 0.3*S + 0.2*F + 0.1*phi_norm

    truth_plane: CANONICAL
      provenance: program_length.py (3b3ae58), v2 TPM from self_modifier_v2 (5c1f83c)
      falsifier:  phi_MI = 0.0 on organic simulation
      trace:      3b3ae58, 5c1f83c → phi_engine.py (R21)
    """

    def __init__(self, tpm_raw: Optional[Dict[str, Dict[str, float]]] = None):
        self.tpm_raw = tpm_raw or CANONICAL_TPM_RAW
        self._tpm    = _build_tpm(self.tpm_raw)

    def analyze(self) -> PhiReport:
        mi_result  = compute_phi_mi(self._tpm)
        mip_result = compute_phi_mip(self._tpm)
        per_state  = compute_per_state_phi(self._tpm)

        return PhiReport(
            phi_mi          = mi_result["phi_mi"],
            phi_mi_norm     = mi_result["phi_normalized"],
            phi_mip         = mip_result["phi_mip"],
            mip_partition   = mip_result["MIP"],
            H_stationary    = mi_result["H_stationary"],
            H_conditional   = mi_result["H_conditional"],
            stationary_dist = mi_result["stationary"],
            per_state       = per_state,
            is_modular      = mip_result["phi_mip"] < 0,
            is_integrated   = mi_result["phi_mi"] > 0,
        )

    def maturity_contribution(self) -> float:
        """Return phi_MI_normalized for use in maturity formula."""
        report = self.analyze()
        return report.phi_for_maturity


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="EVEZ-OS Phi Engine — R21")
    ap.add_argument("--spine", help="Write spine entry to this JSONL path")
    args = ap.parse_args()

    engine = PhiEngine()
    report = engine.analyze()
    s      = report.summary()

    print("\n=== Phi Engine — R21 ===")
    print(f"\n--- phi_MIP (spatial integration) ---")
    print(f"  phi_MIP:        {report.phi_mip:.4f} bits")
    print(f"  MIP partition:  A={report.mip_partition['A']}")
    print(f"                  B={report.mip_partition['B']}")
    print(f"  Verdict:        {'MODULAR (phi<0)' if report.is_modular else 'INTEGRATED (phi>0)'}")
    print(f"  Interpretation: {s['resolution'][:120]}")

    print(f"\n--- phi_MI (temporal integration) ---")
    print(f"  H(stationary):  {report.H_stationary:.4f} bits")
    print(f"  H(Xt+1|Xt):    {report.H_conditional:.4f} bits")
    print(f"  phi_MI:         {report.phi_mi:.4f} bits")
    print(f"  phi_normalized: {report.phi_mi_norm:.4f}")
    print(f"  Verdict:        {'INTEGRATED (phi>0)' if report.is_integrated else 'MEMORYLESS'}")

    print(f"\n--- Per-state characterization ---")
    for ps in report.per_state:
        print(f"  {ps['state']:12s}: H={ps['H_out']:.4f} | "
              f"dominant={ps['dominant']:12s} (p={ps['p_dominant']:.3f}) | "
              f"pi={ps['pi']:.4f} | {ps['role']}")

    print(f"\n--- Maturity formula update ---")
    print(f"  phi_for_maturity (continuous): {report.phi_for_maturity:.4f}")
    K, S, F = 1.0, 0.730, 0.443
    old_mat  = K*0.5 + S*0.3 + F*0.2 + 0.1*0.1
    new_mat  = K*0.5 + S*0.3 + F*0.2 + report.phi_for_maturity*0.1
    print(f"  Old (binary phi=0.1):          {old_mat:.4f}")
    print(f"  New (continuous phi_norm):     {new_mat:.4f}")

    print(f"\n--- truth_plane: {report.truth_plane} ---")
    print(f"  {s['resolution']}")
    print(f"\n  Falsifier: {s['falsifier']}")

    if args.spine:
        entry = report.to_spine_entry()
        Path(args.spine).parent.mkdir(parents=True, exist_ok=True)
        with open(args.spine, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"\nSpine entry written (hash={entry['hash'][:16]}...)")
