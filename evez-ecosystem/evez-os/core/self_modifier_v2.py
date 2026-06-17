"""core/self_modifier_v2.py — R18 Crossbreed
The Friston fix. Upgrades self_modifier.py based on the CANONICAL theorem
from friston_ceiling.py (R17).

Problem (proved in R17):
  Natural distribution gives Friston ceiling = 0.3457 < 0.4.
  Bottlenecks: THEATRICAL exits near-uniform (conf=0.237), HYPER fully
  uniform (conf=0.000).

Solution (computed analytically in R18):
  Minimum combined fix:
    P(THEATRICAL→VERIFIED) >= 0.65  +  P(HYPER→CANONICAL) >= 0.60
    → mean ceiling = 0.405 (just above threshold)

  Conservative target (safe margin):
    P(THEATRICAL→VERIFIED) = 0.70  +  P(HYPER→CANONICAL) = 0.65
    → mean ceiling = 0.425

  Design changes from v1:
    1. FORCE_VERIFIED: when entry.truth_plane == THEATRICAL and
       smugness_tax > 1.5 (v1: 3.0), force next entry to VERIFIED
       with probability 0.70. This makes THEATRICAL a pass-through,
       not a trap.
    2. CONSOLIDATE_HYPER: when entry.truth_plane == HYPER, force
       next entry to CANONICAL with probability 0.65. HYPER should
       collapse to its most stable neighbor, not scatter.
    3. All v1 safeguards preserved: MAX_VELOCITY, cooldown, audit log.

Falsifier:
  If friston_ceiling.simulate_organic_growth(10000, MODIFIED_V2_DIST)
  returns Friston < 0.40, this module's fix is insufficient.
  (Simulation included — run --self-test to verify.)

truth_plane: CANONICAL
  provenance: friston_ceiling.py (f44aa5a) + analytical threshold
              computation (R18: min P_tv=0.796 solo, P_tv=0.65+P_hc=0.60
              combined)
  falsifier:  see above
  trace:      f44aa5a → self_modifier_v2.py (R18)
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

# ── Constants ─────────────────────────────────────────────────────────────────

TRUTH_PLANES = {"PENDING", "VERIFIED", "CANONICAL", "THEATRICAL", "HYPER"}

# v1 thresholds
V1_SMUGNESS_THRESHOLD   = 3.0
V1_THEATRICAL_THRESHOLD = 0.40

# v2 thresholds (Friston fix)
V2_SMUGNESS_THRESHOLD   = 1.5    # lower → fires earlier on THEATRICAL
V2_THEATRICAL_RATIO_MIN = 0.20   # trigger even at 20% theatrical

# Probability targets (analytical minimum + safety margin)
P_FORCE_VERIFIED   = 0.70   # P(THEATRICAL → VERIFIED) target  [min combined: 0.65]
P_CONSOLIDATE_HYPER = 0.65  # P(HYPER → CANONICAL) target       [min combined: 0.60]
P_MIN_COMBINED_TV  = 0.65   # analytical minimum (combined with P_hc=0.60)
P_MIN_COMBINED_HC  = 0.60   # analytical minimum (combined with P_tv=0.65)

# Safeguards (inherited from v1)
MAX_VELOCITY    = 5      # max mutations per session
COOLDOWN_ROUNDS = 3      # rounds between mutations


@dataclass
class MutationRule:
    """A single mutation rule with trigger condition and action."""
    rule_id:    str
    trigger:    str          # truth_plane or condition name
    condition:  str          # human-readable condition
    action:     str          # what mutation fires
    probability: float       # probability this fires when triggered
    version:    str = "v2"
    falsifier:  str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id":    self.rule_id,
            "trigger":    self.trigger,
            "condition":  self.condition,
            "action":     self.action,
            "probability": self.probability,
            "version":    self.version,
            "falsifier":  self.falsifier,
        }


# ── Rule definitions ──────────────────────────────────────────────────────────

V2_RULES: List[MutationRule] = [
    MutationRule(
        rule_id    = "FORCE_VERIFIED",
        trigger    = "THEATRICAL",
        condition  = "truth_plane == THEATRICAL AND smugness_tax > 1.5",
        action     = "Emit VERIFIED spine entry immediately. THEATRICAL is a pass-through, not a trap.",
        probability = P_FORCE_VERIFIED,
        falsifier   = f"If mean Friston < 0.40 after 10000 organic entries with P_tv={P_FORCE_VERIFIED}, rule is insufficient.",
    ),
    MutationRule(
        rule_id    = "CONSOLIDATE_HYPER",
        trigger    = "HYPER",
        condition  = "truth_plane == HYPER",
        action     = "Emit CANONICAL spine entry. HYPER collapses to its most stable neighbor.",
        probability = P_CONSOLIDATE_HYPER,
        falsifier   = f"If mean Friston < 0.40 after 10000 entries with P_hc={P_CONSOLIDATE_HYPER}, rule is insufficient.",
    ),
    MutationRule(
        rule_id    = "THEATRICAL_RATIO_GUARD",
        trigger    = "THEATRICAL",
        condition  = "theatrical_ratio > 0.20 (lowered from v1's 0.40)",
        action     = "Trigger game rule mutation to reduce THEATRICAL entry generation.",
        probability = 1.0,
        version    = "v2",
        falsifier  = "If theatrical_ratio continues rising after rule fires, mutation has no effect.",
    ),
    MutationRule(
        rule_id    = "SMUGNESS_GUARD",
        trigger    = "any",
        condition  = "smugness_tax > 1.5 (lowered from v1's 3.0)",
        action     = "Emit correction entry forcing prediction update.",
        probability = 1.0,
        version    = "v2",
        falsifier  = "If smugness_tax remains > 1.5 after correction, the game engine is not updating.",
    ),
]


# ── Core functions ────────────────────────────────────────────────────────────

def should_force_verified(entry: Dict[str, Any], rng: Optional[random.Random] = None) -> bool:
    """
    Returns True if FORCE_VERIFIED should fire for this entry.

    Triggers when:
      - entry.truth_plane == THEATRICAL
      - entry.smugness_tax > V2_SMUGNESS_THRESHOLD (1.5)
      OR
      - entry.theatrical_ratio > V2_THEATRICAL_RATIO_MIN (0.20)

    Fires with probability P_FORCE_VERIFIED (0.70).
    """
    tp = (entry.get("truth_plane") or "").upper()
    if tp != "THEATRICAL":
        return False

    smugness = float(entry.get("smugness_tax", 0) or 0)
    t_ratio  = float(entry.get("theatrical_ratio", 0) or 0)

    triggered = smugness > V2_SMUGNESS_THRESHOLD or t_ratio > V2_THEATRICAL_RATIO_MIN
    if not triggered:
        return False

    r = (rng or random).random()
    return r < P_FORCE_VERIFIED


def should_consolidate_hyper(entry: Dict[str, Any], rng: Optional[random.Random] = None) -> bool:
    """
    Returns True if CONSOLIDATE_HYPER should fire for this entry.

    Triggers when entry.truth_plane == HYPER.
    Fires with probability P_CONSOLIDATE_HYPER (0.65).

    Design intent: HYPER is an unstable peak state. Left alone it scatters
    to all 5 planes with equal probability (conf=0.000). With this rule,
    HYPER collapses to CANONICAL 65% of the time, preserving the insight
    while anchoring it in provenance.
    """
    tp = (entry.get("truth_plane") or "").upper()
    if tp != "HYPER":
        return False
    r = (rng or random).random()
    return r < P_CONSOLIDATE_HYPER


def apply_friston_fix(
    entry: Dict[str, Any],
    rng: Optional[random.Random] = None,
    velocity: int = 0,
    last_mutation_round: int = -999,
    current_round: int = 0,
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Apply the Friston fix to a single spine entry.

    Returns:
      (correction_entry, rule_id) if a mutation fires
      (None, "") if no mutation needed

    Safeguards:
      - MAX_VELOCITY: at most 5 mutations per session
      - COOLDOWN_ROUNDS: at least 3 rounds between mutations
    """
    if velocity >= MAX_VELOCITY:
        return None, "MAX_VELOCITY_EXCEEDED"
    if (current_round - last_mutation_round) < COOLDOWN_ROUNDS:
        return None, "COOLDOWN"

    force_verified = should_force_verified(entry, rng)
    consolidate    = should_consolidate_hyper(entry, rng)

    if not force_verified and not consolidate:
        return None, ""

    rule_id    = "FORCE_VERIFIED" if force_verified else "CONSOLIDATE_HYPER"
    target_tp  = "VERIFIED"       if force_verified else "CANONICAL"
    rule       = next(r for r in V2_RULES if r.rule_id == rule_id)

    correction = {
        "kind":              "self_modifier_v2.correction",
        "truth_plane":       target_tp,
        "rule_id":           rule_id,
        "rule_version":      "v2",
        "triggered_by":      entry.get("truth_plane", ""),
        "triggered_entry":   entry.get("hash", "")[:16] if entry.get("hash") else "",
        "action":            rule.action,
        "probability_used":  P_FORCE_VERIFIED if force_verified else P_CONSOLIDATE_HYPER,
        "smugness_tax_at_trigger": entry.get("smugness_tax", 0),
        "theatrical_ratio_at_trigger": entry.get("theatrical_ratio", 0),
        "falsifier":         rule.falsifier,
        "ts":                time.time(),
    }
    raw = json.dumps({k: v for k, v in correction.items() if k != "hash"},
                     sort_keys=True, separators=(",", ":"))
    correction["hash"] = hashlib.sha256(raw.encode()).hexdigest()
    return correction, rule_id


# ── SelfModifierV2 ────────────────────────────────────────────────────────────

class SelfModifierV2:
    """
    Upgraded self_modifier implementing the Friston fix.

    v1 → v2 changes:
      1. FORCE_VERIFIED fires at smugness_tax > 1.5 (was 3.0)
         with P=0.70 → makes THEATRICAL a pass-through
      2. CONSOLIDATE_HYPER fires at any HYPER entry
         with P=0.65 → anchors HYPER to CANONICAL
      3. theatrical_ratio trigger lowered from 0.40 to 0.20
      4. All v1 safeguards preserved (MAX_VELOCITY=5, COOLDOWN=3)

    Projected ceiling with v2 active:
      P_tv=0.70, P_hc=0.65 → mean ceiling = 0.425 (above 0.4 target)
      Computed analytically in R18 from friston_ceiling.py formulas.

    truth_plane: CANONICAL
      Falsifier: if simulate_organic_growth(10000, V2_DIST) < 0.40
    """

    def __init__(self, spine_path: Optional[str] = None,
                 rng_seed: Optional[int] = None):
        self.spine_path  = Path(spine_path) if spine_path else None
        self._rng        = random.Random(rng_seed) if rng_seed else random
        self._velocity   = 0
        self._last_round = -999
        self._log: List[Dict[str, Any]] = []

    def process(self, entry: Dict[str, Any],
                current_round: int = 0) -> Optional[Dict[str, Any]]:
        """
        Process a spine entry. If a mutation fires, return the correction
        entry (to be appended to the spine). Otherwise return None.
        """
        correction, rule_id = apply_friston_fix(
            entry, self._rng, self._velocity,
            self._last_round, current_round
        )
        if correction:
            self._velocity  += 1
            self._last_round = current_round
            self._log.append({
                "round":   current_round,
                "rule_id": rule_id,
                "hash":    correction.get("hash", "")[:16],
            })
            if self.spine_path:
                self._write(correction)
        return correction

    def _write(self, entry: Dict[str, Any]) -> None:
        self.spine_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.spine_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def status(self) -> Dict[str, Any]:
        force_v = sum(1 for x in self._log if x["rule_id"] == "FORCE_VERIFIED")
        consol  = sum(1 for x in self._log if x["rule_id"] == "CONSOLIDATE_HYPER")
        return {
            "version":          "v2",
            "mutations_total":  len(self._log),
            "force_verified":   force_v,
            "consolidate_hyper": consol,
            "velocity":         self._velocity,
            "last_round":       self._last_round,
            "projected_ceiling": _projected_ceiling(),
            "truth_plane":      "CANONICAL",
            "falsifier":        "simulate_organic_growth(10000, V2_DIST) must return Friston >= 0.40",
        }

    def reset_velocity(self) -> None:
        """Call at session boundary."""
        self._velocity   = 0
        self._last_round = -999


def _projected_ceiling() -> float:
    """Return the analytically projected Friston ceiling with v2 active."""
    import math
    NUM_PLANES = 5
    def conf(dist):
        total = sum(dist.values())
        if total == 0: return 0.0
        probs = [v/total for v in dist.values() if v > 0]
        H = -sum(p * math.log(p + 1e-12) for p in probs)
        return max(0.0, 1.0 - H / math.log(NUM_PLANES))

    NATURAL = {
        "PENDING":    {"VERIFIED": 0.40, "PENDING": 0.10, "CANONICAL": 0.005, "THEATRICAL": 0.005, "HYPER": 0.01},
        "VERIFIED":   {"CANONICAL": 0.15, "PENDING": 0.15, "THEATRICAL": 0.01, "VERIFIED": 0.01, "HYPER": 0.001},
        "CANONICAL":  {"PENDING": 0.10, "VERIFIED": 0.04, "THEATRICAL": 0.005, "CANONICAL": 0.001, "HYPER": 0.001},
    }
    r_tv = (1 - P_FORCE_VERIFIED) / 4
    r_hc = (1 - P_CONSOLIDATE_HYPER) / 4
    V2_THEATRICAL = {"VERIFIED": P_FORCE_VERIFIED,  "PENDING": r_tv, "CANONICAL": r_tv, "THEATRICAL": r_tv, "HYPER": r_tv}
    V2_HYPER      = {"CANONICAL": P_CONSOLIDATE_HYPER, "PENDING": r_hc, "VERIFIED": r_hc, "THEATRICAL": r_hc, "HYPER": r_hc}

    values = [conf(NATURAL[s]) for s in ["PENDING","VERIFIED","CANONICAL"]]
    values += [conf(V2_THEATRICAL), conf(V2_HYPER)]
    return round(sum(values) / len(values), 4)


# ── Self-test ─────────────────────────────────────────────────────────────────

def run_self_test(spine_path: str) -> Dict[str, Any]:
    """
    Verify the fix works: simulate 10000 organic entries using V2 distribution.
    Falsifier: if Friston < 0.40, the fix is insufficient.
    """
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from core.friston_ceiling import simulate_organic_growth
    except ImportError:
        # inline fallback
        def simulate_organic_growth(n, dist_map, seed=42, checkpoints=None):
            import random as rnd, math
            rng = rnd.Random(seed)
            PLANES = ["PENDING","VERIFIED","CANONICAL","THEATRICAL","HYPER"]
            tm = {s: {d: 0 for d in PLANES} for s in PLANES}
            cur = "PENDING"
            for _ in range(n):
                dist = dist_map.get(cur, {})
                tot = sum(dist.values())
                if tot == 0: cur = rng.choice(PLANES); continue
                r = rng.random(); acc = 0.0
                for st, p in dist.items():
                    acc += p/tot
                    if r <= acc: cur = st; break
                tm[cur][rng.choice(PLANES)] = tm[cur].get(rng.choice(PLANES), 0)
                # simplified: just track outgoing from cur
                nxt = cur
                for d in PLANES:
                    tm[cur][d] = tm[cur].get(d, 0)
            entropies = []
            for src in PLANES:
                total = sum(tm[src].values())
                if total > 0:
                    probs = [v/total for v in tm[src].values() if v > 0]
                    H = -sum(p*math.log(p+1e-12) for p in probs)
                    entropies.append(max(0.0, 1.0 - H/math.log(5)))
            return {"final_friston": sum(entropies)/len(entropies) if entropies else 0.0,
                    "falsifier_triggered": False}

    r_tv = (1 - P_FORCE_VERIFIED) / 4
    r_hc = (1 - P_CONSOLIDATE_HYPER) / 4
    V2_DIST = {
        "PENDING":    {"VERIFIED": 0.40, "PENDING": 0.10, "CANONICAL": 0.005, "THEATRICAL": 0.005, "HYPER": 0.01},
        "VERIFIED":   {"CANONICAL": 0.15, "PENDING": 0.15, "THEATRICAL": 0.01, "VERIFIED": 0.01, "HYPER": 0.001},
        "CANONICAL":  {"PENDING": 0.10, "VERIFIED": 0.04, "THEATRICAL": 0.005, "CANONICAL": 0.001, "HYPER": 0.001},
        "THEATRICAL": {"VERIFIED": P_FORCE_VERIFIED,    "PENDING": r_tv, "CANONICAL": r_tv, "THEATRICAL": r_tv, "HYPER": r_tv},
        "HYPER":      {"CANONICAL": P_CONSOLIDATE_HYPER, "PENDING": r_hc, "VERIFIED": r_hc, "THEATRICAL": r_hc, "HYPER": r_hc},
    }

    result = simulate_organic_growth(10000, V2_DIST, seed=42)
    analytical = _projected_ceiling()

    return {
        "sim_10000_friston":    result["final_friston"],
        "analytical_ceiling":   analytical,
        "falsifier_triggered":  result["final_friston"] < 0.40,
        "verdict": ("FIX VERIFIED — Friston >= 0.40 with v2 rules"
                    if result["final_friston"] >= 0.40
                    else "FIX INSUFFICIENT — Friston still < 0.40"),
        "truth_plane": "CANONICAL" if result["final_friston"] >= 0.40 else "THEATRICAL",
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="EVEZ-OS SelfModifierV2 — Friston Fix")
    ap.add_argument("--spine", help="Spine JSONL path")
    ap.add_argument("--self-test", action="store_true", help="Run self-test (verify fix)")
    ap.add_argument("--rules", action="store_true", help="Print all v2 rules")
    args = ap.parse_args()

    print("\n=== SelfModifierV2 — Friston Fix ===")
    print(f"  P(THEATRICAL→VERIFIED): {P_FORCE_VERIFIED:.2f}  (v1: ~0.03)")
    print(f"  P(HYPER→CANONICAL):     {P_CONSOLIDATE_HYPER:.2f}  (v1: ~0.005)")
    print(f"  Smugness threshold:     {V2_SMUGNESS_THRESHOLD}    (v1: {V1_SMUGNESS_THRESHOLD})")
    print(f"  Theatrical ratio min:   {V2_THEATRICAL_RATIO_MIN}  (v1: {V1_THEATRICAL_THRESHOLD})")
    print(f"  Projected ceiling:      {_projected_ceiling():.4f}  (v1 natural: 0.3457)")
    print(f"  Min combined:           P_tv={P_MIN_COMBINED_TV} + P_hc={P_MIN_COMBINED_HC} → ceiling ~0.405")

    if args.rules:
        print("\n--- v2 Rules ---")
        for rule in V2_RULES:
            print(f"  [{rule.rule_id}] trigger={rule.trigger} p={rule.probability}")
            print(f"    condition: {rule.condition}")
            print(f"    action:    {rule.action}")
            print(f"    falsifier: {rule.falsifier}")

    if args.self_test:
        print("\n--- Self-test (simulate 10000 entries with v2 distribution) ---")
        result = run_self_test(args.spine or "/dev/null")
        for k, v in result.items():
            print(f"  {k}: {v}")

    sm = SelfModifierV2(spine_path=args.spine, rng_seed=42)

    # Demonstrate on synthetic entries
    test_entries = [
        {"truth_plane": "THEATRICAL", "smugness_tax": 2.0, "theatrical_ratio": 0.35, "hash": "aaa"},
        {"truth_plane": "THEATRICAL", "smugness_tax": 0.5, "theatrical_ratio": 0.10, "hash": "bbb"},
        {"truth_plane": "HYPER",      "smugness_tax": 0.0, "theatrical_ratio": 0.0,  "hash": "ccc"},
        {"truth_plane": "VERIFIED",   "smugness_tax": 0.2, "theatrical_ratio": 0.05, "hash": "ddd"},
    ]
    print("\n--- Processing synthetic entries ---")
    for i, e in enumerate(test_entries):
        c = sm.process(e, current_round=i*5)
        if c:
            print(f"  entry[{i}] {e['truth_plane']} → correction.truth_plane={c['truth_plane']} rule={c['rule_id']}")
        else:
            print(f"  entry[{i}] {e['truth_plane']} → no mutation")

    print("\n--- Status ---")
    for k, v in sm.status().items():
        print(f"  {k}: {v}")
