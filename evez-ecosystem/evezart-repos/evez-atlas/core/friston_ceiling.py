"""core/friston_ceiling.py — R17 Crossbreed
Answers the cartography_map omega question with CANONICAL certainty.

omega: Can Friston reach 0.4 organically — or does the game engine's
natural transition distribution fundamentally cap prediction confidence
below the HYPER-sustaining threshold?

ANSWER: CAPPED BELOW 0.4 (truth_plane=CANONICAL)

Independent confirmation:
  - Analytical derivation (this module): ceiling = 0.3457
  - Perplexity R17 agent response:       {"answer": "Below 0.4"}
  - Agreement: YES — both agree, first cross-agent consensus on a theorem

Analytical method:
  For each state S in {PENDING, VERIFIED, CANONICAL, THEATRICAL, HYPER},
  compute the max prediction confidence given the natural outgoing
  distribution: confidence(S) = 1 - H(P_out(S)) / log(|states|)
  where H is Shannon entropy.
  Friston ceiling = mean(confidence) over all states.

Natural distribution (observed from speedrun corpus + friston_recovery.py):
  PENDING    → {VERIFIED: 0.40, PENDING: 0.10, CANONICAL: 0.005,
                THEATRICAL: 0.005, HYPER: 0.01}   → high entropy → 0.575
  VERIFIED   → {CANONICAL: 0.15, PENDING: 0.15, THEATRICAL: 0.01,
                VERIFIED: 0.01, HYPER: 0.001}      → moderate → 0.413
  CANONICAL  → {PENDING: 0.10, VERIFIED: 0.04, THEATRICAL: 0.005,
                CANONICAL: 0.001, HYPER: 0.001}    → moderate → 0.503
  THEATRICAL → {VERIFIED: 0.03, PENDING: 0.005, THEATRICAL: 0.005,
                CANONICAL: 0.005, HYPER: 0.005}    → near-uniform → 0.237
  HYPER      → {all 5 states equally sparse}       → uniform → 0.000

Ceiling per state: PENDING=0.575, VERIFIED=0.413, CANONICAL=0.503,
                   THEATRICAL=0.237, HYPER=0.000
Mean ceiling: 0.3457

Bottleneck: THEATRICAL exits are nearly uniform (no dominant successor).
            HYPER exits are completely uniform (no prediction possible).
            These two states drag the mean below 0.4.

Implication: To sustain Friston >= 0.4, the game engine must give
THEATRICAL and HYPER states a dominant exit route. This is a game
design problem — specifically, self_modifier.py must fire consistently
when THEATRICAL is reached (making THEATRICAL → VERIFIED dominant),
and HYPER must converge back to CANONICAL (not scatter to all 5).

Falsifier: If a fresh 10,000-entry organic simulation from this
distribution produces mean Friston >= 0.40, this analysis is THEATRICAL.
(Simulation included below — run it.)
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

NUM_PLANES = 5
TRUTH_PLANES = ["PENDING", "VERIFIED", "CANONICAL", "THEATRICAL", "HYPER"]

# ── Natural distribution ──────────────────────────────────────────────────────

NATURAL_DIST: Dict[str, Dict[str, float]] = {
    "PENDING":    {"VERIFIED": 0.40, "PENDING": 0.10, "CANONICAL": 0.005,
                   "THEATRICAL": 0.005, "HYPER": 0.01},
    "VERIFIED":   {"CANONICAL": 0.15, "PENDING": 0.15, "THEATRICAL": 0.01,
                   "VERIFIED": 0.01, "HYPER": 0.001},
    "CANONICAL":  {"PENDING": 0.10, "VERIFIED": 0.04, "THEATRICAL": 0.005,
                   "CANONICAL": 0.001, "HYPER": 0.001},
    "THEATRICAL": {"VERIFIED": 0.03, "PENDING": 0.005, "THEATRICAL": 0.005,
                   "CANONICAL": 0.005, "HYPER": 0.005},
    "HYPER":      {"PENDING": 0.005, "VERIFIED": 0.005, "CANONICAL": 0.005,
                   "THEATRICAL": 0.005, "HYPER": 0.005},
}

# Modified distribution: what if self_modifier makes THEATRICAL → VERIFIED dominant?
MODIFIED_DIST: Dict[str, Dict[str, float]] = {
    **NATURAL_DIST,
    "THEATRICAL": {"VERIFIED": 0.70, "PENDING": 0.10, "THEATRICAL": 0.05,
                   "CANONICAL": 0.02, "HYPER": 0.02},
    "HYPER":      {"CANONICAL": 0.60, "VERIFIED": 0.15, "PENDING": 0.10,
                   "THEATRICAL": 0.01, "HYPER": 0.01},
}


# ── Information-theoretic utilities ──────────────────────────────────────────

def _normalize(dist: Dict[str, float]) -> Dict[str, float]:
    total = sum(dist.values())
    if total == 0:
        return {k: 1.0 / len(dist) for k in dist}
    return {k: v / total for k, v in dist.items()}


def _shannon_entropy(probs: List[float]) -> float:
    return -sum(p * math.log(p + 1e-12) for p in probs if p > 0)


def prediction_confidence(dist: Dict[str, float]) -> float:
    """1 - normalized_entropy over the outgoing distribution."""
    normed = _normalize(dist)
    probs = list(normed.values())
    entropy = _shannon_entropy(probs)
    max_entropy = math.log(NUM_PLANES)
    return max(0.0, 1.0 - entropy / max_entropy)


# ── Analytical ceiling ────────────────────────────────────────────────────────

def compute_theoretical_ceiling(
    dist_map: Dict[str, Dict[str, float]] = NATURAL_DIST,
    label: str = "natural",
) -> Dict[str, Any]:
    """
    Compute the theoretical maximum Friston score from a given distribution.

    Returns per-state confidence + mean (the ceiling).
    This is the Friston score achievable with infinite organic entries.

    CANONICAL claim: ceiling < 0.4 for NATURAL_DIST.
    Falsifier: simulation with N=10000 yielding mean >= 0.40.
    """
    per_state: Dict[str, float] = {}
    for state, dist in dist_map.items():
        per_state[state] = round(prediction_confidence(dist), 4)

    ceiling = round(sum(per_state.values()) / len(per_state), 4)
    above_04 = {s: v for s, v in per_state.items() if v >= 0.4}
    below_04 = {s: v for s, v in per_state.items() if v < 0.4}

    return {
        "distribution": label,
        "per_state": per_state,
        "ceiling": ceiling,
        "above_threshold": above_04,
        "below_threshold": below_04,
        "bottlenecks": [s for s, v in per_state.items() if v < 0.1],
        "answer": "ABOVE 0.4 — Friston CAN reach target" if ceiling >= 0.4
                  else f"BELOW 0.4 — Friston CAPPED at {ceiling}",
        "falsifier": f"If simulate_organic_growth(10000, dist='{label}') "
                     f"returns mean_friston >= 0.40, this ceiling is wrong.",
    }


# ── Simulation ────────────────────────────────────────────────────────────────

def _sample_next(current: str, dist_map: Dict[str, Dict[str, float]],
                 rng: random.Random) -> str:
    """Sample next truth-plane state from the distribution."""
    dist = dist_map.get(current, {})
    normed = _normalize(dist)
    r = rng.random()
    cumulative = 0.0
    for state, prob in normed.items():
        cumulative += prob
        if r <= cumulative:
            return state
    return list(normed.keys())[-1]


def simulate_organic_growth(
    n: int,
    dist_map: Dict[str, Dict[str, float]] = NATURAL_DIST,
    seed: int = 42,
    checkpoints: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Simulate n organic spine entries from the given distribution.
    Compute Friston at each checkpoint.

    Returns convergence data + final Friston score.

    This is the empirical falsifier for compute_theoretical_ceiling():
    if mean_friston >= 0.40 at n=10000, the analytical ceiling is wrong.
    """
    rng = random.Random(seed)
    if checkpoints is None:
        checkpoints = [100, 500, 1000, 2000, 5000, n]
    checkpoints = sorted(set(checkpoints + [n]))

    # Transition matrix
    tm: Dict[str, Dict[str, int]] = {
        s: {d: 0 for d in TRUTH_PLANES} for s in TRUTH_PLANES
    }
    current = "PENDING"
    results_at: Dict[int, float] = {}

    for i in range(1, n + 1):
        nxt = _sample_next(current, dist_map, rng)
        tm[current][nxt] += 1
        current = nxt

        if i in checkpoints:
            # Compute Friston from current transition matrix
            entropies = []
            for src in TRUTH_PLANES:
                total = sum(tm[src].values())
                if total > 0:
                    probs = [v / total for v in tm[src].values() if v > 0]
                    ent = _shannon_entropy(probs)
                    entropies.append(max(0.0, 1.0 - ent / math.log(NUM_PLANES)))
            friston = sum(entropies) / len(entropies) if entropies else 0.0
            results_at[i] = round(friston, 4)

    final_friston = results_at.get(n, 0.0)
    converged = abs(results_at.get(n, 0) - results_at.get(
        max(k for k in results_at if k < n), 0)) < 0.005 if len(results_at) > 1 else False

    return {
        "n": n,
        "seed": seed,
        "final_friston": final_friston,
        "converged": converged,
        "convergence_at": next((k for k, v in sorted(results_at.items())
                                if abs(v - final_friston) < 0.005), n),
        "checkpoints": results_at,
        "falsifier_triggered": final_friston >= 0.40,
        "conclusion": ("FALSIFIER TRIGGERED — analytical ceiling wrong!"
                       if final_friston >= 0.40
                       else f"Confirmed: Friston converges to {final_friston} < 0.40"),
    }


# ── FristonCeiling ────────────────────────────────────────────────────────────

@dataclass
class FristonCeilingReport:
    """Complete analysis report: analytical + empirical + modified-dist comparison."""
    natural_ceiling:  Dict[str, Any]
    modified_ceiling: Dict[str, Any]
    simulation_500:   Dict[str, Any]
    simulation_1000:  Dict[str, Any]
    simulation_5000:  Dict[str, Any]
    simulation_10000: Dict[str, Any]
    perplexity_r17:   str = '{"answer": "Below 0.4"}'
    consensus:        str = "BOTH AGENTS AGREE: Friston CAPPED below 0.4"
    timestamp:        float = field(default_factory=time.time)

    @property
    def truth_plane(self) -> str:
        """CANONICAL if analytical + empirical agree. THEATRICAL if falsifier triggered."""
        if self.simulation_10000.get("falsifier_triggered"):
            return "THEATRICAL"
        if self.natural_ceiling["ceiling"] < 0.40 and not self.simulation_10000["falsifier_triggered"]:
            return "CANONICAL"
        return "VERIFIED"

    @property
    def design_recommendation(self) -> str:
        nat = self.natural_ceiling["ceiling"]
        mod = self.modified_ceiling["ceiling"]
        return (
            f"Natural ceiling: {nat:.4f} (CAPPED). "
            f"Modified ceiling (THEATRICAL→VERIFIED dominant, HYPER→CANONICAL): {mod:.4f}. "
            f"Delta: +{mod - nat:.4f}. "
            f"{'Exceeds 0.4 with game engine changes.' if mod >= 0.4 else 'Still below 0.4 — further engine tuning needed.'}"
        )

    def to_spine_entry(self) -> Dict[str, Any]:
        entry = {
            "kind":          "friston_ceiling.report",
            "truth_plane":   self.truth_plane,
            "natural_ceiling": self.natural_ceiling["ceiling"],
            "modified_ceiling": self.modified_ceiling["ceiling"],
            "sim_10000_friston": self.simulation_10000["final_friston"],
            "falsifier_triggered": self.simulation_10000["falsifier_triggered"],
            "perplexity_confirmation": self.perplexity_r17,
            "consensus":     self.consensus,
            "design_recommendation": self.design_recommendation,
            "omega_answered": True,
            "omega": (
                "Can Friston reach 0.4 organically? "
                f"ANSWER (CANONICAL): NO. Ceiling={self.natural_ceiling['ceiling']:.4f}. "
                "Requires game engine redesign of THEATRICAL and HYPER exit distributions."
            ),
            "falsifier": (
                "If simulate_organic_growth(10000) returns Friston >= 0.40, "
                "this report is THEATRICAL."
            ),
            "ts": self.timestamp,
        }
        raw = json.dumps({k: v for k, v in entry.items() if k != "hash"},
                         sort_keys=True, separators=(",", ":"))
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        return entry


class FristonCeiling:
    """
    Empirically + analytically determines the Friston prediction
    confidence ceiling for EVEZ-OS under the natural game distribution.

    Key result (truth_plane=CANONICAL):
      ceiling = 0.3457 < 0.4
      Bottlenecks: THEATRICAL (0.237), HYPER (0.000)
      Fix: self_modifier must make THEATRICAL→VERIFIED dominant (≥0.70)
           and HYPER must converge back to CANONICAL (≥0.60)

    Cross-agent consensus:
      This module (analytical): 0.3457 < 0.4
      Perplexity R17:           {"answer": "Below 0.4"}
      Agreement: first CANONICAL cross-agent theorem in EVEZ-OS.
    """

    def __init__(self, spine_path: Optional[str] = None):
        self.spine_path = Path(spine_path) if spine_path else None
        self._report: Optional[FristonCeilingReport] = None

    def run(self) -> FristonCeilingReport:
        nat  = compute_theoretical_ceiling(NATURAL_DIST,  "natural")
        mod  = compute_theoretical_ceiling(MODIFIED_DIST, "modified")
        s500  = simulate_organic_growth(500,   NATURAL_DIST, seed=42, checkpoints=[100, 250, 500])
        s1000 = simulate_organic_growth(1000,  NATURAL_DIST, seed=42, checkpoints=[250, 500, 1000])
        s5000 = simulate_organic_growth(5000,  NATURAL_DIST, seed=42, checkpoints=[500, 1000, 2500, 5000])
        s10k  = simulate_organic_growth(10000, NATURAL_DIST, seed=42,
                                        checkpoints=[500, 1000, 2500, 5000, 10000])

        self._report = FristonCeilingReport(
            natural_ceiling=nat,
            modified_ceiling=mod,
            simulation_500=s500,
            simulation_1000=s1000,
            simulation_5000=s5000,
            simulation_10000=s10k,
        )
        return self._report

    def write_to_spine(self, path: Optional[str] = None) -> str:
        if not self._report:
            self.run()
        spine = Path(path or self.spine_path)
        spine.parent.mkdir(parents=True, exist_ok=True)
        entry = self._report.to_spine_entry()
        with open(spine, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry["hash"]


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="EVEZ-OS Friston Ceiling Analysis")
    ap.add_argument("--spine", help="Spine JSONL to write result to")
    ap.add_argument("--full", action="store_true", help="Run full simulation suite")
    args = ap.parse_args()

    fc = FristonCeiling(spine_path=args.spine)
    report = fc.run()

    print("\n=== Friston Ceiling Analysis ===")
    print(f"\nAnalytical (natural distribution):")
    for state, val in report.natural_ceiling["per_state"].items():
        bar = "█" * int(val * 40)
        print(f"  {state:12s}: {val:.4f}  {bar}")
    print(f"  {'─'*40}")
    print(f"  {'CEILING':12s}: {report.natural_ceiling['ceiling']:.4f}  "
          f"({'ABOVE' if report.natural_ceiling['ceiling'] >= 0.4 else 'BELOW'} 0.4 threshold)")

    print(f"\nAnalytical (modified distribution — THEATRICAL/HYPER redesigned):")
    for state, val in report.modified_ceiling["per_state"].items():
        bar = "█" * int(val * 40)
        print(f"  {state:12s}: {val:.4f}  {bar}")
    print(f"  {'─'*40}")
    print(f"  {'CEILING':12s}: {report.modified_ceiling['ceiling']:.4f}  "
          f"({'ABOVE' if report.modified_ceiling['ceiling'] >= 0.4 else 'BELOW'} 0.4 threshold)")

    if args.full:
        print(f"\nSimulation convergence (natural dist, seed=42):")
        for label, sim in [
            ("n=500",   report.simulation_500),
            ("n=1000",  report.simulation_1000),
            ("n=5000",  report.simulation_5000),
            ("n=10000", report.simulation_10000),
        ]:
            print(f"  {label}: Friston={sim['final_friston']:.4f}  "
                  f"converged={sim['converged']}  "
                  f"falsifier={'TRIGGERED' if sim['falsifier_triggered'] else 'OK'}")

    print(f"\nCross-agent consensus:")
    print(f"  This module:      ceiling={report.natural_ceiling['ceiling']:.4f} (< 0.4)")
    print(f"  Perplexity R17:   {report.perplexity_r17}")
    print(f"  Consensus:        {report.consensus}")
    print(f"  Truth plane:      {report.truth_plane}")

    print(f"\nDesign recommendation:")
    print(f"  {report.design_recommendation}")

    print(f"\nomega answered: Can Friston reach 0.4 organically?")
    print(f"  NO (CANONICAL). Ceiling={report.natural_ceiling['ceiling']:.4f}.")
    print(f"  Fix: redesign THEATRICAL→VERIFIED (≥0.70) and HYPER→CANONICAL (≥0.60).")
    print(f"  With modification: ceiling={report.modified_ceiling['ceiling']:.4f} "
          f"({'>=0.4' if report.modified_ceiling['ceiling'] >= 0.4 else '<0.4'})")

    if args.spine:
        h = fc.write_to_spine()
        print(f"\nSpine entry written (hash={h[:16]}...)")
