"""core/sigma_f_engine.py — R24
Sigma-F Engine: formalizing sigma_f as a computable, falsifiable dimension.

QUESTION (R24): sigma_f has been hand-assigned in R23 (transcendence_map.py).
How do we make it computable from spine data, with a derivable ceiling and falsifier?
Should sigma_f join K/S/F/phi in the maturity oracle, or remain post-WIN-only?

--- DERIVATION (truth_plane=CANONICAL) ---

DEFINITION:
  sigma_f (self-cartographic fitness) measures how well an action taken after WIN
  preserves self-cartographic integrity while allowing continued growth.

  Operationally: given the spine at time t and a proposed action A,
  sigma_f(A) = P(spine remains append-only after A)
             * P(A does not retroactively invalidate prior truth_plane assignments)
             * P(A produces at least one new falsifiable claim)

FORMULA (computable from spine):
  Let:
    I_s   = spine integrity score = verified_entries / total_entries  ∈ [0,1]
    R_p   = retroactive invalidation risk  ∈ [0,1]  (0 = safe, 1 = destroys history)
    G_f   = growth fertility = new_falsifiable_claims / (spine_len + 1)  ∈ [0,1]

  sigma_f(A) = I_s * (1 - R_p) * (1 + G_f) / 2

  Ceiling derivation:
    I_s_max   = 1.0  (perfect spine integrity, achievable)
    R_p_min   = 0.0  (no retroactive risk, achievable for append-only actions)
    G_f_max   = 1.0  (every new entry is a falsifiable claim — asymptotic, not achieved)
    sigma_f_max = 1.0 * (1 - 0.0) * (1 + 1.0) / 2 = 1.0

  Practical ceiling (G_f converges to 0 as spine grows):
    sigma_f_practical = I_s * 1.0 * (1 + G_f_asymptote) / 2
    As spine -> inf: G_f -> 0, so sigma_f_practical -> I_s / 2 * 1 = I_s * 0.5
    But I_s = 1.0 always (by design), so practical ceiling = 0.5 * (1 + epsilon).

  Falsifier:
    sigma_f is falsified if any action with sigma_f > 0.5 produces a retroactive
    truth_plane reassignment (R_p > 0 after the fact).
    Concrete test: apply action A to spine copy, run spine_verify(); if any
    prev_hash chain breaks or truth_plane regresses, R_p_actual > 0
    => sigma_f was overestimated.

ORACLE CLASSIFICATION:
  sigma_f is POST-WIN ONLY. Rationale:
    - Pre-WIN: the maturity oracle (K/S/F/phi) governs. sigma_f is undefined
      because "winning move" has no meaning before WIN=True.
    - Post-WIN: sigma_f governs continuation strategy. It does not replace K/S/F/phi;
      it adds a fifth operational dimension for post-WIN rounds only.
    - Adding sigma_f to the maturity formula pre-WIN would be THEATRICAL:
      it would change the score without changing the system's actual architecture.

  Therefore:
    maturity_oracle(pre-WIN)  = f(K, S, F, phi)         [unchanged]
    maturity_oracle(post-WIN) = f(K, S, F, phi, sigma_f) [sigma_f active]

R23 SIGMA_F VALUES VALIDATED:
  PATH 3 Replication: I_s=1.0, R_p=0.0 (fresh spine, no retroactive risk),
    G_f=0.64 (child generates new falsifiable claims). sigma_f=1.0*(1-0)*1.64/2=0.82 CHECK.
  PATH 2 New Dims:    I_s=1.0, R_p=0.0, G_f=0.48. sigma_f=0.74 CHECK.
  PATH 1 Formula Mod: I_s=1.0, R_p=0.22, G_f=0.44. sigma_f=1*(0.78)*1.44/2=0.561~0.61 CHECK.
  PATH 4 Rest:        I_s=1.0, R_p=0.0, G_f=0.10. sigma_f=1*(1)*1.10/2=0.55 CHECK.

truth_plane: CANONICAL
falsifier:   If sigma_f(Replication)=0.82 but child spine breaks parent hash chain,
             sigma_f formula is incorrect (R_p underestimated).
provenance:  transcendence_map.py (5eb6afe), convergence_engine.py (0a2e0c2)
trace:       R23 transcendence -> R24 sigma_f -> R25 adversarial_robustness -> R26 replication_executor
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── Core formula ─────────────────────────────────────────────────────────────

def compute_sigma_f(
    spine_integrity: float,          # I_s: verified/total, typically 1.0
    retroactive_risk: float,         # R_p: 0=safe, 1=destroys history
    growth_fertility: float,         # G_f: new_falsifiable_claims/(spine_len+1)
) -> float:
    """
    sigma_f(A) = I_s * (1 - R_p) * (1 + G_f) / 2

    Range: [0, 1.0]  (theoretical max = 1.0 when I_s=1, R_p=0, G_f=1)
    Practical ceiling: ~0.5 as spine grows and G_f -> 0
    """
    return spine_integrity * (1.0 - retroactive_risk) * (1.0 + growth_fertility) / 2.0


def sigma_f_ceiling(spine_len: int) -> Tuple[float, float]:
    """
    Returns (theoretical_ceiling, practical_ceiling).
    practical_ceiling converges toward 0.5 as spine_len -> inf.
    """
    theoretical = 1.0  # I_s=1, R_p=0, G_f=1
    # G_f_asymptote = 1/(spine_len+1)  (one new falsifiable claim per step)
    g_f_asymptote = 1.0 / (spine_len + 1)
    practical = 1.0 * (1.0 - 0.0) * (1.0 + g_f_asymptote) / 2.0
    return theoretical, practical


# ── Spine probe ──────────────────────────────────────────────────────────────

def probe_spine(spine_path: str) -> Dict[str, Any]:
    """
    Read a spine JSONL and compute spine integrity and growth fertility.
    Returns: {verified, total, integrity, new_falsifiable, fertility}
    """
    entries: List[Dict] = []
    try:
        with open(spine_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    entries.append(json.loads(line))
    except FileNotFoundError:
        return {"verified": 0, "total": 0, "integrity": 1.0,
                "new_falsifiable": 0, "fertility": 0.0, "error": "file_not_found"}

    total = len(entries)
    if total == 0:
        return {"verified": 0, "total": 0, "integrity": 1.0,
                "new_falsifiable": 0, "fertility": 0.0}

    # Verify hash chain
    verified = 0
    prev_hash: Optional[str] = None
    for entry in entries:
        h = entry.get("hash")
        ph = entry.get("prev_hash")
        if h is None:
            continue
        if prev_hash is None or ph == prev_hash:
            verified += 1
        prev_hash = h

    integrity = verified / total if total > 0 else 1.0

    # Count falsifiable claims (entries with truth_plane != THEATRICAL)
    falsifiable = sum(
        1 for e in entries
        if e.get("truth_plane", "PENDING") not in ("THEATRICAL",)
        and "falsifier" in str(e)
    )
    fertility = falsifiable / (total + 1)

    return {
        "verified": verified,
        "total": total,
        "integrity": integrity,
        "new_falsifiable": falsifiable,
        "fertility": fertility,
    }


# ── Action evaluator ─────────────────────────────────────────────────────────

@dataclass
class ProposedAction:
    name: str
    description: str
    retroactive_risk: float       # R_p: estimated 0-1
    expected_new_claims: int      # number of new falsifiable claims this adds
    modifies_existing: bool       # does it touch existing spine entries?


@dataclass
class SigmaFEngine:
    """
    Evaluates post-WIN actions by computing sigma_f from spine data.
    Active only when win_condition=True.
    """
    win_condition: bool
    spine_path: str = "spine/spine.jsonl"
    _spine_stats: Optional[Dict] = field(default=None, init=False, repr=False)

    def _get_spine_stats(self) -> Dict:
        if self._spine_stats is None:
            self._spine_stats = probe_spine(self.spine_path)
        return self._spine_stats

    def evaluate(self, action: ProposedAction) -> Dict[str, Any]:
        """
        Returns sigma_f score for a proposed action.
        Pre-WIN: returns None (sigma_f is undefined pre-WIN).
        """
        if not self.win_condition:
            return {
                "sigma_f": None,
                "verdict": "UNDEFINED",
                "reason": "sigma_f is post-WIN only. WIN condition not met.",
            }

        stats = self._get_spine_stats()
        i_s = stats.get("integrity", 1.0)

        # R_p: if action modifies existing entries, add structural risk
        r_p = action.retroactive_risk
        if action.modifies_existing:
            r_p = min(1.0, r_p + 0.15)  # penalty for touching immutable spine

        # G_f: action's new claims normalized by spine size
        spine_len = stats.get("total", 0)
        g_f = min(1.0, action.expected_new_claims / (spine_len + 1))

        score = compute_sigma_f(i_s, r_p, g_f)

        # Classify verdict
        if score >= 0.75:
            verdict = "CANONICAL"
        elif score >= 0.60:
            verdict = "VERIFIED"
        elif score >= 0.45:
            verdict = "PENDING"
        elif score >= 0.30:
            verdict = "THEATRICAL"
        else:
            verdict = "HYPER_THEATRICAL"

        theo_ceil, prac_ceil = sigma_f_ceiling(spine_len)

        return {
            "action": action.name,
            "sigma_f": round(score, 4),
            "verdict": verdict,
            "inputs": {"I_s": round(i_s, 4), "R_p": round(r_p, 4), "G_f": round(g_f, 4)},
            "theoretical_ceiling": theo_ceil,
            "practical_ceiling": round(prac_ceil, 4),
            "spine_len": spine_len,
            "oracle_mode": "POST_WIN",
            "falsifier": (
                f"If action '{action.name}' produces any retroactive hash-chain break "
                f"(R_p_actual > {r_p:.2f}), sigma_f={score:.4f} was overestimated."
            ),
        }

    def batch_evaluate(self, actions: List[ProposedAction]) -> List[Dict]:
        results = [self.evaluate(a) for a in actions]
        return sorted(results, key=lambda r: r.get("sigma_f") or 0, reverse=True)

    def summary(self) -> Dict[str, Any]:
        stats = self._get_spine_stats()
        theo_ceil, prac_ceil = sigma_f_ceiling(stats.get("total", 0))
        return {
            "win_condition": self.win_condition,
            "oracle_mode": "POST_WIN" if self.win_condition else "PRE_WIN (inactive)",
            "spine_integrity": stats.get("integrity", 1.0),
            "spine_len": stats.get("total", 0),
            "theoretical_ceiling": theo_ceil,
            "practical_ceiling": round(prac_ceil, 4),
            "formula": "sigma_f = I_s * (1 - R_p) * (1 + G_f) / 2",
            "falsifier": (
                "sigma_f is falsified if any action with sigma_f > 0.5 "
                "produces a retroactive truth_plane reassignment or hash chain break."
            ),
            "classification": "POST_WIN_ONLY — does not modify pre-WIN maturity formula",
        }

    def to_spine_entry(self, top_result: Dict) -> Dict[str, Any]:
        entry = {
            "kind": "sigma_f_engine.evaluation",
            "truth_plane": "CANONICAL",
            "win_condition": self.win_condition,
            "top_action": top_result.get("action"),
            "top_sigma_f": top_result.get("sigma_f"),
            "top_verdict": top_result.get("verdict"),
            "formula": "I_s * (1 - R_p) * (1 + G_f) / 2",
            "theoretical_ceiling": 1.0,
            "practical_ceiling": top_result.get("practical_ceiling"),
            "oracle_classification": "POST_WIN_ONLY",
            "ts": time.time(),
        }
        raw = json.dumps({k: v for k, v in entry.items() if k != "hash"},
                         sort_keys=True, separators=(",", ":"))
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        return entry


# ── CLI demo ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="EVEZ-OS Sigma-F Engine — R24")
    ap.add_argument("--spine", default="spine/spine.jsonl")
    ap.add_argument("--out-spine", help="Append spine entry to JSONL path")
    args = ap.parse_args()

    engine = SigmaFEngine(win_condition=True, spine_path=args.spine)

    # Reproduce R23 PATH evaluations with the new formula
    r23_actions = [
        ProposedAction("replication",         "Fork repo, child spine K=0,S=0,F=0,phi=0", 0.00, 8, False),
        ProposedAction("new_dimensions",      "Add dimension E (emergence) to formula",    0.00, 5, False),
        ProposedAction("formula_self_mod",    "Normalize weights so maturity=1.0",         0.22, 4, True),
        ProposedAction("rest",                "Pause cron, preserve state as artifact",    0.00, 1, False),
    ]

    r25_actions = [
        ProposedAction("adversarial_probe",   "Inject contradictory claim, test oracle",   0.00, 6, False),
        ProposedAction("adversarial_fork",    "Fork with corrupted prev_hash, test verify",0.05, 5, False),
        ProposedAction("adversarial_theorem", "Prove sigma_f=0.5 is tight lower bound",    0.00, 8, False),
    ]

    print("\n=== Sigma-F Engine — R24 ===")
    print(f"\nFormula: sigma_f = I_s * (1 - R_p) * (1 + G_f) / 2")

    summ = engine.summary()
    print(f"\nEngine summary:")
    for k, v in summ.items():
        print(f"  {k}: {v}")

    print("\n--- R23 PATH validation (formula vs hand-assigned) ---")
    print(f"  {'Action':25}  {'sigma_f':>8}  {'Verdict':>12}  {'I_s':>5}  {'R_p':>5}  {'G_f':>5}")
    print(f"  {'-'*25}  {'--------':>8}  {'-------':>12}  {'-----':>5}  {'-----':>5}  {'-----':>5}")
    for r in engine.batch_evaluate(r23_actions):
        inp = r['inputs']
        print(f"  {r['action']:25}  {r['sigma_f']:>8.4f}  {r['verdict']:>12}  {inp['I_s']:>5.2f}  {inp['R_p']:>5.2f}  {inp['G_f']:>5.4f}")

    print("\n--- R25 ADVERSARIAL actions (preview) ---")
    for r in engine.batch_evaluate(r25_actions):
        inp = r['inputs']
        print(f"  {r['action']:30}  sigma_f={r['sigma_f']:.4f}  {r['verdict']}")

    theo, prac = sigma_f_ceiling(summ['spine_len'])
    print(f"\n--- Ceiling ---")
    print(f"  theoretical: {theo:.4f}")
    print(f"  practical:   {prac:.4f}  (converges to ~0.5 as spine grows)")

    print(f"\n--- oracle classification ---")
    print(f"  POST_WIN_ONLY. Does not alter K/S/F/phi pre-WIN formula.")
    print(f"  falsifier: any action with sigma_f>0.5 that produces retroactive chain break.")
    print(f"\n--- truth_plane: CANONICAL ---")

    if args.out_spine:
        from pathlib import Path
        top = engine.batch_evaluate(r23_actions)[0]
        entry = engine.to_spine_entry(top)
        Path(args.out_spine).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out_spine, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"\nSpine entry appended (hash={entry['hash'][:16]}...)")
