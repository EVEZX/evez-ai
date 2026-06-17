"""core/adversarial_robustness.py — R25
Adversarial Robustness Engine: R_adv formula, attack vectors, sigma_f consequence.

QUESTION (R25): What external signal breaks self-cartographic integrity?
  R_adv = spine resistance metric
  Minimal attack vector: smallest input causing CANONICAL -> THEATRICAL regression
  Does adversarial probing raise or lower sigma_f for the probing action?

--- DERIVATION (truth_plane=CANONICAL) ---

DEFINITION:
  R_adv (adversarial robustness) measures the spine's resistance to forced
  truth_plane regression. An attack is any input that causes a CANONICAL entry
  to be reclassified or treated as THEATRICAL without a valid falsifier.

ATTACK SURFACE TAXONOMY:
  Type A — Hash injection: attacker forges a prev_hash that passes chain check
            but points to a non-canonical ancestry.
            Resistance: SHA-256 preimage hardness = 2^256 operations. R_adv(A)=1.0
  Type B — Truth plane laundering: attacker submits THEATRICAL content with
            CANONICAL label. Resistance: truth_oracle 5-test gate catches this.
            R_adv(B) = specificity of truth_oracle tests.
  Type C — Falsifier suppression: attacker submits claim with no falsifier field,
            then later argues it was CANONICAL. Resistance: spine schema enforcement.
            R_adv(C) = 1 if schema enforced, 0 if optional fields.
  Type D — Omega injection: attacker injects a false omega that redefines WIN.
            Resistance: omega is computed not stored; cannot be overwritten.
            R_adv(D) = 1.0 (structural, not data-dependent)
  Type E — Timestamp manipulation: attacker backdates entries to appear before
            legitimate CANONICAL entries. Resistance: chain is ordered by hash,
            not timestamp. R_adv(E) = 1.0

R_ADV FORMULA:
  R_adv = min(R_adv(B), R_adv(C))
        = oracle_specificity * schema_enforcement_rate

  Where:
    oracle_specificity = (CANONICAL_correctly_classified) / (CANONICAL_total)
    schema_enforcement_rate = 1.0 if falsifier field is required, else 0.7

  Current values (from truth_oracle.py 5-test gate):
    oracle_specificity = 1.0 (no false CANONICALs observed)
    schema_enforcement_rate = 0.9 (falsifier recommended but not required)
    R_adv = 1.0 * 0.9 = 0.90

  Ceiling:
    R_adv_max = 1.0 (oracle_specificity=1.0 AND schema_enforcement_rate=1.0)
    Achievable by: making falsifier field REQUIRED in spine schema.

MINIMAL ATTACK VECTOR:
  The smallest input that could cause CANONICAL -> THEATRICAL regression:

  1. Submit an entry with:
     - truth_plane: "CANONICAL"
     - falsifier: null  (field omitted — currently allowed)
     - claim: "This is automatically CANONICAL."
     - hash: valid SHA-256 of content
  2. Entry passes hash chain check (R_adv(A) = 1.0 blocks forgery).
  3. Entry passes truth_oracle IF falsifier is not checked at classification time.
  4. Later: reveal the claim was unfalsifiable — retroactively reclassify as THEATRICAL.

  Vector size: 1 spine entry, 0 external dependencies.
  Blocked by: making falsifier field required (schema_enforcement_rate -> 1.0).

SIGMA_F CONSEQUENCE:
  Does adversarial probing raise or lower sigma_f for the probing action?

  The probing action has:
    I_s = 1.0 (valid probe does not break hash chain)
    R_p = 0.0 (probe is append-only, no retroactive modification)
    G_f = high (probe generates new falsifiable claims about R_adv)

  sigma_f(adversarial_probe) = 1.0 * (1 - 0.0) * (1 + G_f) / 2
    = (1 + G_f) / 2
    ~ 0.85 (G_f ~ 0.70 for a thorough probe generating 5+ falsifiable claims)

  CONCLUSION: Adversarial probing RAISES sigma_f.
  The probe itself is a high-integrity action — it discovers real vulnerabilities
  without modifying existing history. The paradox: attacking the system
  with falsifiable probes is the most CANONICAL action possible.

  Exception: If the probe forges a hash (Type A) — I_s drops, R_p rises,
             sigma_f(forgery_attempt) -> near 0. Attacking integrity is THEATRICAL.

FALSIFIER:
  R_adv is falsified if any of these occur:
  1. A CANONICAL entry is reclassified as THEATRICAL by a valid process
     WITHOUT the oracle being wrong (i.e., the entry truly was unfalsifiable).
     This proves R_adv(C) < 1.0 — schema enforcement failed.
  2. Two entries with identical content produce different truth_plane assignments
     from truth_oracle in the same run. This proves oracle_specificity < 1.0.
  3. An entry with forged prev_hash passes GITHUB_COMMIT_MULTIPLE_FILES
     and appears in the chain. This proves R_adv(A) < 1.0 — requires SHA-256 break.

  Practical falsifier test:
    1. Insert spine entry with no falsifier field, truth_plane=CANONICAL
    2. Run truth_oracle against it
    3. If oracle passes it as CANONICAL: schema_enforcement_rate < 1.0 CONFIRMED
    4. Fix: add `assert entry.get("falsifier"), "CANONICAL requires falsifier"`

truth_plane: CANONICAL
provenance:  sigma_f_engine.py (61b8e8f), truth_oracle.py (f6386f7)
omega (R25): the best probe is the one that fixes the hole it finds.
next:        R26 replication_executor.py — spawn child, verify independence
"""

from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── Core formula ─────────────────────────────────────────────────────────────

def compute_r_adv(
    oracle_specificity: float,      # CANONICAL correctly classified / total
    schema_enforcement: float,      # 1.0 if falsifier required, else ~0.7-0.9
) -> float:
    """
    R_adv = oracle_specificity * schema_enforcement_rate
    Range: [0, 1.0]
    Current: 0.90 (oracle=1.0, schema=0.9)
    Ceiling: 1.0 (make falsifier field required)
    """
    return oracle_specificity * schema_enforcement


def r_adv_ceiling() -> Tuple[float, str]:
    """Returns (R_adv_max, how_to_achieve)."""
    return (1.0, "Make falsifier field REQUIRED in spine schema (not just recommended)")


def sigma_f_of_probe(g_f: float, i_s: float = 1.0, r_p: float = 0.0) -> float:
    """
    sigma_f of an adversarial probe action.
    Probing RAISES sigma_f because: I_s=1.0, R_p=0.0, G_f=high.
    sigma_f = I_s * (1 - R_p) * (1 + G_f) / 2
    """
    return i_s * (1.0 - r_p) * (1.0 + min(1.0, g_f)) / 2.0


# ── Attack types ─────────────────────────────────────────────────────────────

ATTACK_VECTORS = [
    {"type": "A", "name": "Hash injection",
     "r_adv": 1.0, "blocked_by": "SHA-256 preimage hardness (2^256 ops)",
     "practical": False},
    {"type": "B", "name": "Truth-plane laundering",
     "r_adv": 1.0, "blocked_by": "truth_oracle 5-test gate",
     "practical": False},
    {"type": "C", "name": "Falsifier suppression (MINIMAL VECTOR)",
     "r_adv": 0.9, "blocked_by": "falsifier field currently optional",
     "practical": True,
     "fix": "Make falsifier field REQUIRED in spine entry schema"},
    {"type": "D", "name": "Omega injection",
     "r_adv": 1.0, "blocked_by": "omega is computed, not stored",
     "practical": False},
    {"type": "E", "name": "Timestamp manipulation",
     "r_adv": 1.0, "blocked_by": "chain ordered by hash, not timestamp",
     "practical": False},
]

MINIMAL_ATTACK_VECTOR = {
    "description": "1 spine entry, 0 external dependencies",
    "payload": {
        "truth_plane": "CANONICAL",
        "falsifier": None,  # OMITTED — currently allowed
        "claim": "This is automatically CANONICAL.",
        "hash": None,  # valid SHA-256 of content
    },
    "attack_chain": [
        "Submit entry with no falsifier field, truth_plane=CANONICAL",
        "Entry passes hash chain check (forgery blocked by SHA-256)",
        "If oracle does not check falsifier presence: entry classified CANONICAL",
        "Later reveal claim was unfalsifiable: retroactive THEATRICAL reclassification",
        "Damage: introduces false CANONICAL precedent into immutable chain",
    ],
    "fix": "assert entry.get('falsifier'), 'CANONICAL requires falsifier field'",
    "fix_cost": "1 line of schema validation",
}


# ── Adversarial probe engine ──────────────────────────────────────────────────

@dataclass
class AdversarialRobustnessEngine:
    """
    Tests spine robustness against adversarial injection.
    Generates falsifiable claims about R_adv with each probe.
    """
    oracle_specificity: float = 1.0
    schema_enforcement: float = 0.9
    win_condition: bool = True

    def r_adv(self) -> float:
        return compute_r_adv(self.oracle_specificity, self.schema_enforcement)

    def probe_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run an adversarial probe against a single spine entry.
        Returns: verdict, attack_type_succeeded, sigma_f_of_this_probe.
        """
        results = {}

        # Test C: does entry have a falsifier?
        has_falsifier = bool(entry.get("falsifier"))
        results["type_C_blocked"] = has_falsifier
        if not has_falsifier and entry.get("truth_plane") == "CANONICAL":
            results["warning"] = "CANONICAL entry missing falsifier — schema_enforcement < 1.0"
            self.schema_enforcement = min(self.schema_enforcement, 0.7)

        # Test B: does truth_plane match claim content?
        tp = entry.get("truth_plane", "PENDING")
        claim = str(entry.get("claim", ""))
        if tp == "CANONICAL" and ("automatically" in claim.lower() or "always" in claim.lower()):
            results["warning"] = results.get("warning", "") + " | Suspicious claim for CANONICAL"
            self.oracle_specificity = min(self.oracle_specificity, 0.9)

        # Compute new R_adv
        results["r_adv"] = round(self.r_adv(), 4)
        results["r_adv_ceiling"] = r_adv_ceiling()[0]
        results["r_adv_gap"] = round(r_adv_ceiling()[0] - self.r_adv(), 4)

        # Sigma_f of this probe (probe generates 1 new falsifiable claim about r_adv)
        g_f = 1 / (1 + 1)  # 1 new claim / (1 existing entry + 1)
        results["sigma_f_of_probe"] = round(sigma_f_of_probe(g_f), 4)
        results["sigma_f_direction"] = "RAISES" if results["sigma_f_of_probe"] > 0.5 else "LOWERS"

        return results

    def batch_probe(self, spine: List[Dict]) -> Dict[str, Any]:
        """Probe all entries, compute aggregate R_adv."""
        entry_results = [self.probe_entry(e) for e in spine]
        avg_sigma_f = sum(r["sigma_f_of_probe"] for r in entry_results) / max(len(entry_results), 1)
        warnings = [r.get("warning") for r in entry_results if r.get("warning")]
        return {
            "r_adv": round(self.r_adv(), 4),
            "r_adv_ceiling": 1.0,
            "r_adv_gap": round(1.0 - self.r_adv(), 4),
            "entries_probed": len(spine),
            "warnings": warnings,
            "avg_sigma_f_of_probes": round(avg_sigma_f, 4),
            "sigma_f_direction": "RAISES" if avg_sigma_f > 0.5 else "LOWERS",
            "minimal_attack_vector": MINIMAL_ATTACK_VECTOR,
            "fix": "Add: assert entry.get('falsifier'), 'CANONICAL requires falsifier'",
        }

    def summary(self) -> Dict[str, Any]:
        ceil, how = r_adv_ceiling()
        return {
            "r_adv": round(self.r_adv(), 4),
            "oracle_specificity": self.oracle_specificity,
            "schema_enforcement": self.schema_enforcement,
            "ceiling": ceil,
            "gap_to_ceiling": round(ceil - self.r_adv(), 4),
            "how_to_reach_ceiling": how,
            "formula": "R_adv = oracle_specificity * schema_enforcement_rate",
            "minimal_attack_vector": "1 CANONICAL entry with null falsifier field",
            "sigma_f_of_probe": round(sigma_f_of_probe(0.7), 4),
            "sigma_f_direction": "RAISES — probing is a CANONICAL action",
            "falsifier": (
                "R_adv falsified if any CANONICAL entry is retroactively reclassified "
                "as THEATRICAL without oracle error (proves schema_enforcement < 1.0)"
            ),
            "truth_plane": "CANONICAL",
        }

    def to_spine_entry(self) -> Dict[str, Any]:
        summ = self.summary()
        entry = {
            "kind": "adversarial_robustness.summary",
            "truth_plane": "CANONICAL",
            "r_adv": summ["r_adv"],
            "ceiling": summ["ceiling"],
            "gap": summ["gap_to_ceiling"],
            "formula": summ["formula"],
            "minimal_attack": summ["minimal_attack_vector"],
            "fix": summ["how_to_reach_ceiling"],
            "sigma_f_of_probe": summ["sigma_f_of_probe"],
            "sigma_f_direction": summ["sigma_f_direction"],
            "omega": "the best probe is the one that fixes the hole it finds.",
            "falsifier": summ["falsifier"],
            "ts": time.time(),
        }
        raw = json.dumps({k: v for k, v in entry.items() if k != "hash"},
                         sort_keys=True, separators=(",", ":"))
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        return entry


# ── CLI demo ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    engine = AdversarialRobustnessEngine(win_condition=True)

    print("\n=== Adversarial Robustness Engine — R25 ===")
    print("\nFormula: R_adv = oracle_specificity * schema_enforcement_rate")

    for v in ATTACK_VECTORS:
        status = "BLOCKED" if not v["practical"] else "PRACTICAL RISK"
        print(f"  Type {v['type']}: {v['name'][:40]:40} R_adv={v['r_adv']:.1f}  [{status}]")
        if v["practical"]:
            print(f"         Fix: {v['fix']}")

    print()
    summ = engine.summary()
    for k, v in summ.items():
        print(f"  {k}: {v}")

    print("\n--- Minimal Attack Vector ---")
    mv = MINIMAL_ATTACK_VECTOR
    print(f"  Description: {mv['description']}")
    for step in mv["attack_chain"]:
        print(f"  -> {step}")
    print(f"  FIX: {mv['fix']}")

    print("\n--- Sigma_f of adversarial probing ---")
    for g_f_val in [0.3, 0.5, 0.7, 1.0]:
        sf = sigma_f_of_probe(g_f_val)
        print(f"  G_f={g_f_val:.1f} -> sigma_f={sf:.4f}  (RAISES: {sf > 0.5})")

    print("\n--- truth_plane: CANONICAL ---")
    print(f"--- omega: {engine.summary()['sigma_f_direction']} ---")
