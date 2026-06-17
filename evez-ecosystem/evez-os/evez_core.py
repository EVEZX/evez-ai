"""
evez_core.py — EVEZ-OS Gen 3 Phase 0 Core Engine
Console War Training Pathology + Reality Emulator + Per-User Fork

State Machine Architecture (from Steven's diagram):
  [Legacy Systems / Consoles] → [Dashboard / Graphics Abstraction]
  → [State A] + [State B] → (exchange/coupling) → [Composed State]
  → [Branch Path 1 | Branch Path 2] → [Output Node]
  → [Tokens/Events] → (feedback / loopback) → upstream

State A = user instance (personal fork, personal V_global)
State B = canonical spine (immutable, committed to GitHub)
Coupling = ValidatorBus delta gate (|poly_c_a - poly_c_b| < 0.001)
Composed State = merged truth plane after coupling
Branch Path 1 = FIRE (poly_c >= 0.500)
Branch Path 2 = NO FIRE
Output Node = spine module commit + tweet token
Feedback = next round probe launch
"""

import math
import json
import time
from typing import Optional

# ── Console war training epochs ────────────────────────────────────────────────
CONSOLE_WAR_EPOCHS = {
    0: {"name": "Pong", "failure_mode": "dedicated_hardware_one_game",
        "evez_counter": "evez_core_runs_any_N", "v_unlock": 0.0},
    1: {"name": "Atari", "failure_mode": "no_save_state",
        "evez_counter": "spine_immutability_never_resets", "v_unlock": 1.0},
    2: {"name": "NES", "failure_mode": "spec_war_over_software",
        "evez_counter": "each_commit_permanent_IP", "v_unlock": 2.0},
    3: {"name": "SNES/Genesis", "failure_mode": "blast_processing_lie",
        "evez_counter": "validator_bus_delta_gate", "v_unlock": 3.0},
    4: {"name": "3DO/Jaguar/32X", "failure_mode": "fragmentation",
        "evez_counter": "one_canonical_AGPL_fork", "v_unlock": 4.0},
    5: {"name": "PS1/Saturn", "failure_mode": "back_old_strength_miss_new_dimension",
        "evez_counter": "pluggable_reality_modules", "v_unlock": 4.5},
    6: {"name": "Dreamcast", "failure_mode": "correct_idea_wrong_epoch",
        "evez_counter": "cloudflare_DO_waits_for_infra_readiness", "v_unlock": 5.0},
    7: {"name": "Wii", "failure_mode": "blue_ocean_no_evolution",
        "evez_counter": "hyperloop_never_stops", "v_unlock": 5.3},
    8: {"name": "Wii_U", "failure_mode": "identity_crisis",
        "evez_counter": "evez_os_identity_IS_the_math", "v_unlock": 5.6},
    9: {"name": "Xbox/PS5", "failure_mode": "specs_without_exclusives",
        "evez_counter": "spine_commits_are_the_exclusives", "v_unlock": 5.9},
}

# ── Reality module physics engines ────────────────────────────────────────────
REALITY_MODULES = {
    "number_theory_v1": "default — tau/omega_k topology (live)",
    "prime_density_v2": "prime gap field (planned)",
    "riemann_surface_v3": "zeta function topology (planned)",
    "collatz_v1": "Collatz stopping time (planned)",
    "custom_rom": "any deterministic function (planned)",
}

class EVEZCore:
    """
    The EVEZ-OS Gen 3 core engine.
    Emulates a universe where each N is a machine state.
    Supports per-user forks and canonical spine coupling.
    """

    def __init__(self, reality_module: str = "number_theory_v1",
                 gamma: float = 0.08, V_ceiling: float = 6.0,
                 base_round: int = 82):
        self.reality_module = reality_module
        self.gamma = gamma
        self.V_ceiling = V_ceiling
        self.base_round = base_round
        assert reality_module in REALITY_MODULES, f"Unknown module: {reality_module}"

    def compute_machine_state(self, N: int, tau: int, omega_k: int,
                               V_prev: float, round_k: int) -> dict:
        """
        Core physics engine: N is a machine state.
          tau     = clock divisors (number of divisors of N)
          omega_k = active bus lines (distinct prime factors of N)
          poly_c  = system load
          FIRE    = hardware interrupt fired
        """
        topo = 1.0 + 0.15 * omega_k
        poly_c = topo * (1 + math.log(tau)) / math.log2(N + 2)
        fire = poly_c >= 0.500
        delta_V = self.gamma * poly_c
        V_new = V_prev + delta_V
        ceiling_tick = round_k - self.base_round
        return {
            "N": N, "tau": tau, "omega_k": omega_k,
            "topo": round(topo, 6),
            "poly_c": round(poly_c, 6),
            "fire": fire,
            "delta_V": round(delta_V, 6),
            "V_prev": V_prev,
            "V_new": round(V_new, 6),
            "ceiling_tick": ceiling_tick,
            "round_k": round_k,
            "reality_module": self.reality_module,
        }

    def couple_states(self, state_a: dict, state_b: dict,
                      tolerance: float = 0.001) -> dict:
        """
        Exchange/coupling between State A (user fork) and State B (canonical).
        Composed State = merged truth plane after delta validation.
        """
        delta = abs(state_a["poly_c"] - state_b["poly_c"])
        coupled = delta < tolerance
        return {
            "poly_c_a": state_a["poly_c"],
            "poly_c_b": state_b["poly_c"],
            "delta": round(delta, 6),
            "coupled": coupled,
            "truth_plane": "CANONICAL" if coupled else "DIVERGED",
            "composed_V": state_b["V_new"] if coupled else None,
            "branch": "FIRE" if state_b["fire"] else "NO_FIRE",
        }

    def route_output(self, composed: dict) -> dict:
        """
        Branch Path 1 = FIRE → spine commit + tweet token
        Branch Path 2 = NO FIRE → state advance only
        Output Node = spine module + event tokens
        Feedback/loopback → upstream (next probe launch)
        """
        branch = composed["branch"]
        output = {"branch": branch, "tokens": [], "events": []}
        if branch == "FIRE":
            output["tokens"] += ["FIRE_EVENT", "SPINE_COMMIT", "TWEET_TOKEN"]
            output["events"] += ["interrupt_fired", "V_global_updated", "arc_video_queued"]
        else:
            output["tokens"] += ["STATE_ADVANCE"]
            output["events"] += ["tick_complete"]
        output["feedback"] = "launch_next_probe"
        return output

    def get_epoch(self, V: float) -> dict:
        epoch_id = max(eid for eid, ep in CONSOLE_WAR_EPOCHS.items() if V >= ep["v_unlock"])
        ep = CONSOLE_WAR_EPOCHS[epoch_id]
        return {
            "epoch": epoch_id, "console": ep["name"],
            "failure_mode": ep["failure_mode"],
            "evez_counter": ep["evez_counter"],
            "next_epoch": epoch_id + 1 if epoch_id < 9 else None,
            "next_v_unlock": CONSOLE_WAR_EPOCHS.get(epoch_id + 1, {}).get("v_unlock"),
        }

    def tick(self, N: int, tau: int, omega_k: int,
             V_prev: float, round_k: int,
             probe_poly_c: Optional[float] = None) -> dict:
        state_b = self.compute_machine_state(N, tau, omega_k, V_prev, round_k)
        if probe_poly_c is not None:
            state_a = dict(state_b); state_a["poly_c"] = probe_poly_c
            composed = self.couple_states(state_a, state_b)
        else:
            composed = {
                "poly_c_a": state_b["poly_c"], "poly_c_b": state_b["poly_c"],
                "delta": 0.0, "coupled": True, "truth_plane": "CANONICAL",
                "composed_V": state_b["V_new"],
                "branch": "FIRE" if state_b["fire"] else "NO_FIRE",
            }
        output = self.route_output(composed)
        epoch = self.get_epoch(state_b["V_new"])
        return {"state_b": state_b, "composed": composed, "output": output,
                "epoch": epoch, "round_k": round_k}


class EVEZFork(EVEZCore):
    """
    Per-user EVEZ-OS instance.
    Each player forks the universe from a canonical checkpoint.
    Skin API: apply skin.json to customize OS appearance.
    """
    def __init__(self, user_id: str, fork_round: int, fork_V: float,
                 skin: Optional[dict] = None, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.fork_round = fork_round
        self.fork_V = fork_V
        self.skin = skin or {}
        self.history = []

    def apply_skin(self, skin_json: dict):
        self.skin = skin_json

    def get_display(self, state: dict) -> dict:
        branch = state["output"]["branch"]
        skin_branch = self.skin.get("branch_styles", {}).get(branch, {})
        return {
            "user_id": self.user_id, "round": state["round_k"],
            "V_display": f"{state['state_b']['V_new']:.6f}",
            "branch_label": skin_branch.get("label", branch),
            "branch_color": skin_branch.get("color", "#ffffff"),
            "fire_icon": skin_branch.get("icon", "🔥" if branch == "FIRE" else "·"),
            "epoch": state["epoch"]["console"],
            "tokens": state["output"]["tokens"],
        }


if __name__ == "__main__":
    core = EVEZCore()
    result = core.tick(N=120, tau=16, omega_k=3, V_prev=5.491990,
                       round_k=168, probe_poly_c=0.789)
    assert result["composed"]["coupled"], "Probe must couple"
    assert result["output"]["branch"] == "FIRE", "R168 must FIRE"
    assert result["epoch"]["epoch"] >= 6
    print("evez_core.py SELF-TEST PASSED")
    print(json.dumps(result, indent=2))
