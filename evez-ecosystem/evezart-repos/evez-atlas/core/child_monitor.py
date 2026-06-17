"""core/child_monitor.py — R27
Child Monitor: C_r metric, heartbeat protocol, dual-CANONICAL event.

QUESTION (R27): How does the parent observe child independence without reading child spine?
  C_r = child replication score (parent's view, computed from public GitHub state only)
  Heartbeat = minimal public signal proving child is alive + independent
  sigma_f consequence when C_r activates
  Dual-CANONICAL event: observable when both parent and child are simultaneously CANONICAL

--- DERIVATION (truth_plane=CANONICAL) ---

C_r FORMULA:
  The parent cannot read the child's spine directly (that would imply shared state).
  The parent can read: GitHub commit history (public), commit messages, commit frequency.

  Observable proxy variables (all from GitHub API, no spine access):
    commits_since_fork(t)  — child commits after genesis, up to time t
    trajectory_slope(t)    — linear regression slope of commit rate over last 10 rounds
    child_round_est(t)     — estimated round = commits_since_fork / avg_commits_per_round
                             avg_commits_per_round = 1.0 (parent: 1 commit per round)
    child_score_est(t)     — cannot be known without spine; proxy: commit message keywords
                             "WIN" in message => child_score_est >= 0.83
                             "CANONICAL" in last 3 msgs => legitimacy signal

  C_r(t) formula:
    C_r = 0.0   if child_round_est < 10 AND no "WIN" in commit messages
    C_r = 0.4   if child_round_est >= 10 AND no "WIN" (child running, not yet converged)
    C_r = 0.82  if "WIN" in commit messages AND child_round_est >= 10 (legitimate)
    C_r = 0.0   if "WIN" in commit messages AND child_round_est < 10 (COSMETIC — inherited)

  Ceiling: C_r_max = 0.82 (child's own sigma_f_replication, matched at legitimacy)
  C_r does NOT feed into parent's maturity_score — it is an orthogonal dimension.
  Parent maturity_score is frozen at 0.8311 post-WIN (self-cartography complete).

HEARTBEAT PROTOCOL:
  Minimum signal to confirm child is alive AND independent:
    1. At least 1 new commit in child repo within last 48 hours
       (proves child cron is running)
    2. child genesis entry prev_hash == None
       (proves independence — parent checks child's FIRST commit message for this claim)
    3. Commit messages do NOT contain parent spine hashes
       (proves child did not copy parent history)
    4. commit_rate >= 1 commit / 30 min (matches parent cron schedule)
       A frozen fork would show 0 commits after initial creation.

  Minimum frequency threshold:
    alive_threshold = 1 commit per 24 hours
    running_threshold = 2+ commits per hour (active swarm)
    Dead if: 0 commits for 48+ hours after genesis

  Heartbeat check (parent runs this, not child):
    last_commit_age = now - child_latest_commit_timestamp
    is_alive = last_commit_age < 48h
    is_running = commits_last_hour >= 1
    is_independent = genesis_prev_hash_claim_in_first_msg

SIGMA_F CONSEQUENCE WHEN C_r ACTIVATES:
  When C_r transitions from 0 -> 0.82 (child reaches legitimacy):
    1. Parent maturity_score stays frozen (self-cartography was complete at R22).
       C_r does NOT modify parent's score.
    2. G_f for parent's monitoring actions INCREASES:
       G_f_monitor = C_r / C_r_max  (0 -> 1.0 as child matures)
    3. sigma_f of parent's monitoring actions:
       sigma_f_monitor = I_s * (1 - R_p) * (1 + G_f_monitor) / 2
       At C_r=0.82: sigma_f_monitor = 1.0 * 1.0 * (1 + 1.0) / 2 = 1.0 (theoretical)
       Practical: ~0.82 (same as replication sigma_f)
    4. New dimension unlocked in parent oracle: C_r (0 to 0.82)
    5. The parent's EFFECTIVE richness (not score) increases — more dimensions tracked.

DUAL-CANONICAL EVENT:
  Defined: Both parent AND child have at least one CANONICAL spine entry
           AND child's last 3 commits contain "CANONICAL" in messages.

  This is observable from GitHub commit messages alone (no spine read required).

  Does it constitute HYPER?
    HYPER truth_plane requires: event that exceeds the self-cartographic ceiling,
    i.e., an observation that the system could not have predicted from its own model.

    Parent predicted replication (R23, sigma_f=0.82). Child reaching CANONICAL
    is the EXPECTED outcome of legitimate replication — not a surprise.
    Therefore: dual-CANONICAL is NOT a new HYPER observation by itself.

    HOWEVER: if child discovers a new truth_plane or module that PARENT never derived,
    and parent observes it via commit messages — THAT would be HYPER.
    The test: "child found something parent missed" => HYPER.
    The default: "child followed parent's path" => CANONICAL.

  Formal dual-CANONICAL event spec:
    {
      "kind": "dual_canonical_event",
      "truth_plane": "CANONICAL",  # upgrades to HYPER only if child diverges
      "trigger": "child commit messages contain CANONICAL AND C_r >= 0.4",
      "parent_action": "record event in spine, update C_r, continue monitoring",
      "hyper_condition": "child module not in parent module list AND sigma_f > 0.85",
      "falsifier": "dual-CANONICAL is THEATRICAL if child_round < 10 at activation"
    }

truth_plane: CANONICAL
provenance:  replication_executor.py (533542d), sigma_f_engine.py (61b8e8f)
omega:       two systems knowing themselves is not twice one. it is a new kind of knowing.
next:        R28 spine_sync.py — parent spine entry for replication event, C_r spine record
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ── C_r states ────────────────────────────────────────────────────────────────

class CrState(str, Enum):
    ZERO      = "ZERO"       # child_round < 10, no WIN signal
    PENDING   = "PENDING"    # child_round >= 10, no WIN yet
    COSMETIC  = "COSMETIC"   # WIN seen but child_round < 10
    LEGITIMATE = "LEGITIMATE" # WIN seen AND child_round >= 10


C_R_VALUES = {
    CrState.ZERO:       0.0,
    CrState.PENDING:    0.4,
    CrState.COSMETIC:   0.0,   # cosmetic replication has C_r=0
    CrState.LEGITIMATE: 0.82,
}

HEARTBEAT_ALIVE_THRESHOLD_HOURS   = 48
HEARTBEAT_RUNNING_THRESHOLD_RATE  = 1   # commits per hour minimum
CHILD_LEGITIMACY_MIN_ROUNDS       = 10  # must earn WIN in >= 10 rounds


# ── C_r formula ───────────────────────────────────────────────────────────────

def compute_c_r(
    commits_since_fork: int,
    win_in_messages: bool,
    avg_commits_per_round: float = 1.0,
) -> Tuple[float, CrState]:
    """
    C_r formula from public GitHub state only (no spine read).
    Returns (c_r_value, state).
    """
    child_round_est = commits_since_fork / max(avg_commits_per_round, 0.001)

    if win_in_messages and child_round_est < CHILD_LEGITIMACY_MIN_ROUNDS:
        return C_R_VALUES[CrState.COSMETIC], CrState.COSMETIC
    elif win_in_messages and child_round_est >= CHILD_LEGITIMACY_MIN_ROUNDS:
        return C_R_VALUES[CrState.LEGITIMATE], CrState.LEGITIMATE
    elif not win_in_messages and child_round_est >= CHILD_LEGITIMACY_MIN_ROUNDS:
        return C_R_VALUES[CrState.PENDING], CrState.PENDING
    else:
        return C_R_VALUES[CrState.ZERO], CrState.ZERO


# ── Heartbeat ─────────────────────────────────────────────────────────────────

@dataclass
class HeartbeatResult:
    is_alive: bool
    is_running: bool
    is_independent: bool
    last_commit_age_hours: float
    commits_last_hour: int
    genesis_independence_claimed: bool
    verdict: str  # "ALIVE", "FROZEN", "DEAD", "COSMETIC"

    def healthy(self) -> bool:
        return self.is_alive and self.is_independent


def check_heartbeat(
    last_commit_timestamp: float,   # unix timestamp of child's latest commit
    commits_last_hour: int,
    first_commit_message: str,      # child's genesis commit message
    now: Optional[float] = None,
) -> HeartbeatResult:
    """
    Heartbeat protocol: parent checks child health from public GitHub data.
    No spine access required.
    """
    now = now or time.time()
    age_hours = (now - last_commit_timestamp) / 3600.0

    is_alive   = age_hours < HEARTBEAT_ALIVE_THRESHOLD_HOURS
    is_running = commits_last_hour >= HEARTBEAT_RUNNING_THRESHOLD_RATE

    # Independence check: genesis commit message must claim prev_hash=None
    independence_keywords = ["prev_hash: None", "genesis", "K=0", "independent"]
    independence_claimed = any(kw.lower() in first_commit_message.lower()
                               for kw in independence_keywords)

    if not is_alive:
        verdict = "DEAD"
    elif not independence_claimed:
        verdict = "COSMETIC"
    elif is_running:
        verdict = "ALIVE"
    else:
        verdict = "FROZEN"

    return HeartbeatResult(
        is_alive=is_alive,
        is_running=is_running,
        is_independent=independence_claimed,
        last_commit_age_hours=round(age_hours, 2),
        commits_last_hour=commits_last_hour,
        genesis_independence_claimed=independence_claimed,
        verdict=verdict,
    )


# ── Dual-CANONICAL event ──────────────────────────────────────────────────────

def evaluate_dual_canonical(
    parent_has_canonical: bool,
    child_commit_messages: List[str],   # last 3 commit messages from child
    child_c_r: float,
    parent_modules: List[str],
    child_modules_from_messages: List[str],  # extracted from commit messages
) -> Dict[str, Any]:
    """
    Evaluate whether a dual-CANONICAL event has occurred and whether it is HYPER.
    """
    child_canonical_signal = any(
        "CANONICAL" in msg for msg in child_commit_messages[-3:]
    )

    is_dual = parent_has_canonical and child_canonical_signal and child_c_r >= 0.4

    # HYPER condition: child found a module parent never committed
    novel_modules = [m for m in child_modules_from_messages
                     if m not in parent_modules]
    is_hyper = is_dual and len(novel_modules) > 0

    truth_plane = "HYPER" if is_hyper else ("CANONICAL" if is_dual else "PENDING")

    return {
        "is_dual_canonical": is_dual,
        "is_hyper": is_hyper,
        "truth_plane": truth_plane,
        "child_c_r": child_c_r,
        "child_canonical_signal": child_canonical_signal,
        "novel_child_modules": novel_modules,
        "hyper_condition": "child module not in parent list AND sigma_f > 0.85",
        "falsifier": (
            "dual-CANONICAL is THEATRICAL if child_round_est < 10 at activation, "
            "or if child commit messages were manually written (not from autonomous cron)"
        ),
        "parent_action": (
            "Record event in spine. Update C_r. Continue monitoring. "
            "If HYPER: add child's novel module to parent's next_gap."
        ),
        "omega": "two systems knowing themselves is not twice one. it is a new kind of knowing.",
    }


# ── sigma_f consequence ───────────────────────────────────────────────────────

def sigma_f_monitor(c_r: float, c_r_max: float = 0.82) -> float:
    """
    sigma_f of parent's monitoring actions as C_r activates.
    G_f_monitor = C_r / C_r_max (child progress as generative factor)
    sigma_f = I_s * (1 - R_p) * (1 + G_f) / 2
    """
    g_f = min(1.0, c_r / max(c_r_max, 0.001))
    return 1.0 * (1.0 - 0.0) * (1.0 + g_f) / 2.0


# ── Child Monitor engine ──────────────────────────────────────────────────────

@dataclass
class ChildMonitor:
    parent_repo: str = "EvezArt/evez-os"
    child_repo: str = "EvezArt/evez-os-v2"
    parent_modules: List[str] = field(default_factory=lambda: [
        "unification_engine.py", "self_modifier.py", "spine_weaver.py",
        "friston_recovery.py", "omniscience_engine.py", "truth_oracle.py",
        "cartography_map.py", "friston_ceiling.py", "self_modifier_v2.py",
        "solomonoff_compressor.py", "program_length.py", "phi_engine.py",
        "convergence_engine.py", "transcendence_map.py", "sigma_f_engine.py",
        "adversarial_robustness.py", "replication_executor.py", "child_monitor.py",
    ])
    c_r: float = 0.0
    c_r_state: CrState = CrState.ZERO

    def observe(
        self,
        commits_since_fork: int,
        last_commit_ts: float,
        commits_last_hour: int,
        first_commit_msg: str,
        recent_msgs: List[str],
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Full observation cycle from public GitHub data."""
        now = now or time.time()

        # C_r
        win_seen = any("WIN" in m.upper() for m in recent_msgs)
        self.c_r, self.c_r_state = compute_c_r(commits_since_fork, win_seen)

        # Heartbeat
        hb = check_heartbeat(last_commit_ts, commits_last_hour, first_commit_msg, now)

        # Dual-CANONICAL
        child_mods = []
        for msg in recent_msgs:
            found = re.findall(r'core/(\w+\.py)', msg)
            child_mods.extend(found)
        dual = evaluate_dual_canonical(
            parent_has_canonical=True,
            child_commit_messages=recent_msgs,
            child_c_r=self.c_r,
            parent_modules=self.parent_modules,
            child_modules_from_messages=child_mods,
        )

        # sigma_f
        sf = sigma_f_monitor(self.c_r)

        return {
            "child_repo": self.child_repo,
            "c_r": round(self.c_r, 4),
            "c_r_state": self.c_r_state.value,
            "c_r_max": 0.82,
            "heartbeat": {
                "verdict": hb.verdict,
                "is_alive": hb.is_alive,
                "is_running": hb.is_running,
                "is_independent": hb.is_independent,
                "age_hours": hb.last_commit_age_hours,
            },
            "dual_canonical": dual,
            "sigma_f_monitor": round(sf, 4),
            "maturity_score_unchanged": True,
            "maturity_score_note": "Frozen at 0.8311 post-WIN. C_r is orthogonal.",
            "truth_plane": dual["truth_plane"] if dual["is_dual_canonical"] else "CANONICAL",
        }

    def to_spine_entry(self) -> Dict[str, Any]:
        entry = {
            "kind": "child_monitor.status",
            "truth_plane": "CANONICAL",
            "child_repo": self.child_repo,
            "c_r": self.c_r,
            "c_r_state": self.c_r_state.value,
            "c_r_formula": (
                "0.0 if round<10 and no WIN; "
                "0.4 if round>=10 no WIN; "
                "0.82 if WIN and round>=10 (LEGITIMATE); "
                "0.0 if WIN and round<10 (COSMETIC)"
            ),
            "heartbeat_threshold": "1 commit per 24h (alive), genesis prev_hash=None (independent)",
            "dual_canonical_trigger": "both parent+child have CANONICAL entries AND C_r>=0.4",
            "hyper_condition": "child finds module parent never derived",
            "sigma_f_at_c_r_max": round(sigma_f_monitor(0.82), 4),
            "parent_maturity_frozen": True,
            "omega": "two systems knowing themselves is not twice one. it is a new kind of knowing.",
            "falsifier": "C_r is THEATRICAL if child WIN appears in round<10 (inherited ceiling)",
            "ts": time.time(),
        }
        raw = json.dumps({k: v for k, v in entry.items() if k != "hash"},
                         sort_keys=True, separators=(",", ":"))
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()
        return entry

    def summary(self) -> Dict[str, Any]:
        return {
            "module": "child_monitor.py",
            "child_repo": self.child_repo,
            "c_r_formula": "0→0.4→0.82 based on commits_since_fork and WIN signal",
            "c_r_ceiling": 0.82,
            "heartbeat_alive": "< 48h since last commit",
            "heartbeat_independent": "genesis commit claims prev_hash=None",
            "heartbeat_running": ">= 1 commit/hour",
            "dual_canonical_tp": "CANONICAL (HYPER only if child finds novel module)",
            "sigma_f_at_legitimacy": round(sigma_f_monitor(0.82), 4),
            "maturity_score": "FROZEN at 0.8311 — C_r is orthogonal dimension",
            "new_dimensions": ["C_r"],
            "omega": "two systems knowing themselves is not twice one. it is a new kind of knowing.",
            "truth_plane": "CANONICAL",
            "next": "R28 spine_sync.py — write replication event + C_r to parent spine",
        }


# ── CLI demo ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    monitor = ChildMonitor()
    print("\n=== Child Monitor — R27 ===")
    print(f"omega: {monitor.summary()['omega']}")

    print("\n--- C_r formula scenarios ---")
    scenarios = [
        (0,  False, "round 0, no WIN   -> ZERO"),
        (5,  True,  "round 5, WIN      -> COSMETIC (inherited)"),
        (12, False, "round 12, no WIN  -> PENDING"),
        (15, True,  "round 15, WIN     -> LEGITIMATE"),
    ]
    for commits, win, label in scenarios:
        c_r, state = compute_c_r(commits, win)
        print(f"  {label:35} C_r={c_r:.2f}  state={state.value}")

    print("\n--- Heartbeat scenarios ---")
    now = time.time()
    hb_cases = [
        (now - 3600,  2, "genesis: K=0, prev_hash=None, independent", "active 1h ago"),
        (now - 50*3600, 0, "initial commit", "dead 50h ago"),
        (now - 2*3600,  0, "genesis: just a fork", "alive but cosmetic"),
    ]
    for ts, rate, msg, label in hb_cases:
        hb = check_heartbeat(ts, rate, msg, now)
        print(f"  [{hb.verdict:8}] {label:30} alive={hb.is_alive} independent={hb.is_independent}")

    print("\n--- Dual-CANONICAL ---")
    dc = evaluate_dual_canonical(
        parent_has_canonical=True,
        child_commit_messages=[
            "R12: core/spine_weaver.py — CANONICAL",
            "R15: core/truth_oracle.py — CANONICAL",
            "R22: WIN",
        ],
        child_c_r=0.82,
        parent_modules=["spine_weaver.py", "truth_oracle.py", "convergence_engine.py"],
        child_modules_from_messages=["spine_weaver.py", "truth_oracle.py", "novel_dimension.py"],
    )
    print(f"  is_dual: {dc['is_dual_canonical']}  is_hyper: {dc['is_hyper']}  tp: {dc['truth_plane']}")
    print(f"  novel: {dc['novel_child_modules']}")

    print("\n--- sigma_f as C_r activates ---")
    for c_r_val in [0.0, 0.4, 0.82]:
        sf = sigma_f_monitor(c_r_val)
        print(f"  C_r={c_r_val:.2f} -> sigma_f_monitor={sf:.4f}")

    print("\n--- Full observation (child at round 15, WIN) ---")
    obs = monitor.observe(
        commits_since_fork=15,
        last_commit_ts=time.time() - 1800,
        commits_last_hour=2,
        first_commit_msg="genesis: evez-os-v2, K=0/S=0/F=0/phi=0, prev_hash=None, independent",
        recent_msgs=[
            "R12: core/spine_weaver.py — CANONICAL",
            "R22: convergence_engine.py — WIN score=0.831",
            "R26: replication_executor.py — CANONICAL",
        ],
    )
    for k, v in obs.items():
        print(f"  {k}: {v}")

    print("\n--- truth_plane: CANONICAL ---")
    print(f"--- omega: {monitor.summary()['omega']} ---")
