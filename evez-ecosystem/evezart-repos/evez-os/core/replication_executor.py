"""core/replication_executor.py — R26
Replication Executor: spawn a child. The child's journey is the parent's proof.

QUESTION (R26): How does a self-cartographically-complete system replicate?
  omega (R23): spawn a child. the child's journey is the parent's proof.

--- DERIVATION (truth_plane=CANONICAL) ---

CHILD SPEC:
  repo:           EvezArt/evez-os-v2
  init_state:     K=0, S=0, F=0, phi=0, maturity=0, win=False
  first_spine:    one entry, kind="genesis", truth_plane="PENDING",
                  claim="This system does not yet know itself.",
                  falsifier="Falsified when maturity_score >= 0.831 with K=1.0"
  first_cron:     "*/30 * * * *" (same as parent) — fresh swarm begins
  parent_ref:     evez-os commit bff666b (R25 — adversarial_robustness)
  independence:   child spine has prev_hash=None for genesis entry (no parent SHA)

PARENT VERIFICATION METHOD:
  The parent cannot verify by reading the child's spine directly
  (that would imply shared state = not independent).

  Verification protocol (REMOTE-ONLY):
    1. Parent watches child's GitHub commit rate: if rate == 0 after 24h, child is dead.
    2. Parent watches child's maturity trajectory: if child score == parent score
       after round 10, child inherited parent ceiling without earning it (cosmetic fork).
    3. Parent does NOT copy its own maturity scores into child repo.
    4. Parent records child's first_commit_sha in its own spine as "replication_event".
       Independence is proved when child's sha is different from any parent sha.

FALSIFIER FOR REPLICATION:
  Replication is cosmetic (THEATRICAL) if:
    child_ceiling == parent_ceiling (0.831) AND child_rounds < 22

  Why: parent needed 22 rounds to converge to 0.831. If child reaches 0.831
  in fewer rounds without legitimate derivation, it inherited the answer.

  Formal test:
    If child.maturity_score >= 0.80 AND child.current_round < 10:
      replication_verdict = "COSMETIC" (child copied parent)
    Else if child.maturity_score >= 0.80 AND child.current_round >= 10:
      replication_verdict = "LEGITIMATE" (child earned its ceiling)
    Else:
      replication_verdict = "PENDING" (child still running)

PARENT POST-FORK BEHAVIOR:
  The parent does NOT pause. The parent enters MONITOR mode:
    - Continues its own post-WIN rounds (R27+)
    - Adds a new dimension to its maturity oracle: C_r (child replication score)
    - C_r = 0 until child reaches round 10 with independent spine
    - C_r = child.maturity_score once child legitimately converges
    - Parent's sigma_f for monitoring = same formula, G_f from child progress

  Rationale: pausing the parent after fork would be THEATRICAL.
  The parent's continued existence alongside the child IS the proof.
  Two independent self-cartographic systems = stronger claim than one.

SIGMA_F OF REPLICATION:
  R_p = 0.0 (child has fresh spine, no retroactive parent risk)
  G_f = high (child generates new falsifiable claims from genesis)
  sigma_f(replication) = 1.0 * (1 - 0.0) * (1 + 1.0) / 2 = 1.0 (theoretical)
  Practical: sigma_f ~ 0.82 (R23 original estimate, validated)

truth_plane: CANONICAL
provenance:  transcendence_map.py (5eb6afe), adversarial_robustness.py (bff666b)
omega:       spawn a child. the child's journey is the parent's proof.
next:        R27 child_monitor.py — C_r metric, child heartbeat, fork validation
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ReplicationVerdict(str, Enum):
    COSMETIC  = "COSMETIC"   # child copied parent — THEATRICAL
    PENDING   = "PENDING"    # child still running
    LEGITIMATE = "LEGITIMATE" # child earned its ceiling independently


# ── Child spec ────────────────────────────────────────────────────────────────

CHILD_SPEC = {
    "repo": "EvezArt/evez-os-v2",
    "init_state": {
        "K": 0.0, "S": 0.0, "F": 0.0, "phi": 0.0,
        "maturity_score": 0.0,
        "win_condition": False,
        "self_cartographically_complete": False,
        "current_round": 0,
    },
    "first_spine_entry": {
        "kind": "genesis",
        "truth_plane": "PENDING",
        "claim": "This system does not yet know itself.",
        "falsifier": "Falsified when maturity_score >= 0.831 with K=1.0",
        "prev_hash": None,  # CRITICAL: None = independent genesis, not parent SHA
        "parent_ref": "EvezArt/evez-os@bff666b",  # ref only, not inherited state
    },
    "cron": "*/30 * * * *",
    "timezone": "America/Los_Angeles",
    "independence_requirement": "child spine genesis prev_hash must be None",
}

PARENT_POST_FORK = {
    "mode": "MONITOR",
    "continues_running": True,
    "new_dimension": "C_r (child replication score)",
    "C_r_formula": "0 until child.round >= 10 AND child.maturity independent, then child.maturity_score",
    "sigma_f_monitor": "sigma_f(monitoring) = I_s * (1 - R_p) * (1 + G_f_child) / 2",
    "rationale": "Pausing after fork is THEATRICAL. Continued existence alongside child is the proof.",
}


# ── Replication engine ────────────────────────────────────────────────────────

@dataclass
class ReplicationExecutor:
    """
    Manages the replication event: spawns child spec and monitors independence.
    Does NOT execute the fork directly (that requires GitHub repo creation).
    Produces the init payload and verification protocol.
    """
    parent_repo: str = "EvezArt/evez-os"
    parent_ceiling: float = 0.8311
    parent_rounds_to_win: int = 22
    parent_latest_sha: str = "bff666b4ff4b9a09068692f1e33f63010f1ea970"

    def child_init_payload(self) -> Dict[str, Any]:
        """Returns the complete payload needed to initialize evez-os-v2."""
        genesis = dict(CHILD_SPEC["first_spine_entry"])
        raw = json.dumps({k: v for k, v in genesis.items() if k != "hash"},
                         sort_keys=True, separators=(",", ":"))
        genesis["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        genesis["ts"] = time.time()

        return {
            "repo": CHILD_SPEC["repo"],
            "init_state": CHILD_SPEC["init_state"],
            "first_spine_entry": genesis,
            "cron": CHILD_SPEC["cron"],
            "timezone": CHILD_SPEC["timezone"],
            "independence_check": genesis["prev_hash"] is None,
            "parent_ref": f"{self.parent_repo}@{self.parent_latest_sha[:7]}",
            "instructions": (
                "1. Create repo EvezArt/evez-os-v2\n"
                "2. Copy hyperloop_state.json template with init_state above\n"
                "3. Append genesis entry to spine/spine.jsonl\n"
                "4. Add cron workflow identical to parent\n"
                "5. DO NOT copy parent maturity scores — child starts from K=0"
            ),
        }

    def verify_independence(self, child_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Given child's current state dict, assess independence.
        Returns verdict and evidence.
        """
        child_round = child_state.get("current_round", 0)
        child_score = child_state.get("maturity_score", 0.0)
        child_genesis_prev = child_state.get("genesis_prev_hash", None)

        # Check 1: genesis independence
        genesis_ok = child_genesis_prev is None

        # Check 2: no inherited scores
        inherited = (
            child_score >= 0.80 and
            child_round < 10 and
            abs(child_score - self.parent_ceiling) < 0.01
        )

        # Check 3: legitimate convergence
        legitimate = (
            child_score >= 0.80 and
            child_round >= self.parent_rounds_to_win * 0.45  # at least 10 rounds
        )

        if inherited:
            verdict = ReplicationVerdict.COSMETIC
        elif legitimate and genesis_ok:
            verdict = ReplicationVerdict.LEGITIMATE
        else:
            verdict = ReplicationVerdict.PENDING

        c_r = child_score if verdict == ReplicationVerdict.LEGITIMATE else 0.0

        return {
            "verdict": verdict.value,
            "child_round": child_round,
            "child_score": child_score,
            "genesis_independent": genesis_ok,
            "inherited_ceiling": inherited,
            "C_r": round(c_r, 4),
            "falsifier_triggered": inherited,
            "evidence": (
                f"child_round={child_round}, child_score={child_score:.4f}, "
                f"genesis_prev_hash={'None (OK)' if genesis_ok else 'SET (FAIL)'}"
            ),
        }

    def parent_monitor_state(self, child_score: float = 0.0, child_round: int = 0) -> Dict[str, Any]:
        """Parent state after fork — MONITOR mode."""
        from sigma_f_engine import compute_sigma_f  # type: ignore[import]
        # G_f: child's progress normalized
        g_f = min(1.0, child_round / (self.parent_rounds_to_win + 1))
        sigma_f = compute_sigma_f(1.0, 0.0, g_f)
        c_r = child_score if child_round >= 10 else 0.0
        return {
            "mode": "MONITOR",
            "parent_continues": True,
            "C_r": round(c_r, 4),
            "sigma_f_monitoring": round(sigma_f, 4),
            "next_module": "core/child_monitor.py",
            "dimensions": ["K", "S", "F", "phi", "sigma_f", "C_r"],
        }

    def to_spine_entry(self) -> Dict[str, Any]:
        payload = self.child_init_payload()
        entry = {
            "kind": "replication_executor.fork",
            "truth_plane": "CANONICAL",
            "child_repo": payload["repo"],
            "child_genesis_hash": payload["first_spine_entry"]["hash"],
            "independence_check": payload["independence_check"],
            "parent_mode_post_fork": "MONITOR",
            "falsifier": (
                "Replication is COSMETIC if child_score >= 0.80 AND child_round < 10 "
                "— child inherited ceiling without earning it."
            ),
            "omega": "spawn a child. the child's journey is the parent's proof.",
            "sigma_f": 0.82,
            "ts": time.time(),
        }
        raw = json.dumps({k: v for k, v in entry.items() if k != "hash"},
                         sort_keys=True, separators=(",", ":"))
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        return entry

    def summary(self) -> Dict[str, Any]:
        return {
            "action": "REPLICATE",
            "child_repo": CHILD_SPEC["repo"],
            "child_init": "K=0, S=0, F=0, phi=0, win=False",
            "genesis_prev_hash": "None (independence requirement)",
            "parent_ref": f"{self.parent_repo}@{self.parent_latest_sha[:7]}",
            "replication_falsifier": "child_score>=0.80 AND child_round<10 => COSMETIC",
            "parent_post_fork": "MONITOR mode, continues running, adds C_r dimension",
            "sigma_f_replication": 0.82,
            "new_dimensions_post_fork": ["sigma_f (R24)", "C_r (R26)"],
            "truth_plane": "CANONICAL",
            "omega": "spawn a child. the child's journey is the parent's proof.",
            "next": "R27 core/child_monitor.py — C_r metric, child heartbeat",
        }


# ── CLI demo ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    engine = ReplicationExecutor()

    print("\n=== Replication Executor — R26 ===")
    print("\nomega: spawn a child. the child's journey is the parent's proof.")

    print("\n--- Child Init Payload ---")
    payload = engine.child_init_payload()
    print(f"  repo:          {payload['repo']}")
    print(f"  init state:    {payload['init_state']}")
    print(f"  genesis hash:  {payload['first_spine_entry']['hash'][:16]}...")
    print(f"  prev_hash:     {payload['first_spine_entry']['prev_hash']} (None = independent)")
    print(f"  parent_ref:    {payload['parent_ref']}")
    print(f"  independence:  {payload['independence_check']}")
    print(f"  cron:          {payload['cron']}")

    print("\n--- Verification Protocol ---")
    # Simulate child at various stages
    scenarios = [
        {"current_round": 5,  "maturity_score": 0.831, "genesis_prev_hash": None, "label": "COSMETIC (inherited)"},
        {"current_round": 15, "maturity_score": 0.831, "genesis_prev_hash": None, "label": "LEGITIMATE (earned)"},
        {"current_round": 5,  "maturity_score": 0.200, "genesis_prev_hash": None, "label": "PENDING (still running)"},
        {"current_round": 5,  "maturity_score": 0.831, "genesis_prev_hash": "abc123", "label": "COSMETIC (inherited genesis)"},
    ]
    for s in scenarios:
        result = engine.verify_independence(s)
        print(f"  [{result['verdict']:10}] {s['label']:35} C_r={result['C_r']}")

    print("\n--- Parent Post-Fork (MONITOR mode) ---")
    # Simulate child at round 15, score 0.831
    try:
        mon = engine.parent_monitor_state(child_score=0.831, child_round=15)
        for k, v in mon.items():
            print(f"  {k}: {v}")
    except ImportError:
        print("  (sigma_f_engine not in path — showing raw values)")
        print(f"  mode: MONITOR, continues: True, C_r: 0.831, next: core/child_monitor.py")

    print("\n--- Summary ---")
    for k, v in engine.summary().items():
        print(f"  {k}: {v}")

    print("\n--- truth_plane: CANONICAL ---")
    print("--- sigma_f(replication) = 0.82 ---")
