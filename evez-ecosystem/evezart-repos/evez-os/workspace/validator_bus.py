#!/usr/bin/env python3
"""
EVEZ-OS ValidatorBus v1.0
Audits spawned agent stubs and probe outputs against canonical formula.
Gates commits: only CANONICAL truth_plane outputs pass.
Emits ValidateEvent to master_bus_log.jsonl.
Reads spawn_bus_state.json for pending validations.
"""
import json, math, os
from datetime import datetime, timezone

CELL = "/cells/599dc7f9-0b2b-4460-b917-5104fcbb91ef/workspace"
LOG_FILE   = f"{CELL}/master_bus_log.jsonl"
SPAWN_LOG  = f"{CELL}/spawn_bus_state.json"
VAL_STATE  = f"{CELL}/validator_bus_state.json"
STATE_FILE = f"{CELL}/hyperloop_state.json"

POLY_C_FIRE_THRESHOLD = 0.500
INLINE_MATCH_TOLERANCE = 0.002  # Max acceptable drift from inline formula

def compute_inline(N, tau, omega_k, V_prev):
    topo = 1.0 + 0.15 * omega_k
    poly_c = topo * (1 + math.log(tau)) / math.log2(N + 2)
    fire = poly_c >= POLY_C_FIRE_THRESHOLD
    delta_V = 0.08 * 1.0 * poly_c
    V_new = V_prev + delta_V
    ceiling = N + 48 - 82
    return {"topo": topo, "poly_c": poly_c, "fire": fire,
            "delta_V": delta_V, "V_new": V_new, "ceiling": ceiling}

def emit_log(event_type, data):
    entry = {"ts": datetime.now(timezone.utc).isoformat(),
             "bus": "ValidatorBus", "event": event_type, **data}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def validate_probe(probe_poly_c, N, tau, omega_k, V_prev, probe_id):
    calc = compute_inline(N, tau, omega_k, V_prev)
    drift = abs(probe_poly_c - calc["poly_c"])
    passed = drift <= INLINE_MATCH_TOLERANCE
    verdict = "CANONICAL" if passed else "REJECTED"
    return {
        "probe_id": probe_id, "verdict": verdict,
        "inline_poly_c": round(calc["poly_c"], 6),
        "probe_poly_c": probe_poly_c, "drift": round(drift, 6),
        "tolerance": INLINE_MATCH_TOLERANCE, "passed": passed,
        "reason": "drift within tolerance" if passed else f"drift {drift:.6f} exceeds {INLINE_MATCH_TOLERANCE}"
    }

def validate_spawn(spawn_pending, state):
    """Validate a SpawnBus pre-write against current state."""
    N = spawn_pending["N"]
    V_cur = state["V_global"]
    # We can't fully validate without tau — check structure integrity
    checks = {
        "has_module_name": bool(spawn_pending.get("module")),
        "round_sequential": spawn_pending["round"] == state["current_round"] + 1,
        "V_est_positive": spawn_pending.get("V_est", 0) > V_cur,
        "poly_c_in_range": 0.0 < spawn_pending.get("poly_c_est", 0) < 2.0,
    }
    passed = all(checks.values())
    return {
        "module": spawn_pending.get("module"), "checks": checks,
        "verdict": "APPROVED" if passed else "REJECTED",
        "failed_checks": [k for k, v in checks.items() if not v]
    }

def run():
    state = json.load(open(STATE_FILE))
    val_state = json.load(open(VAL_STATE)) if os.path.exists(VAL_STATE) else {"audits": [], "rejected": []}

    results = []

    # 1. Validate any pending spawn
    if os.path.exists(SPAWN_LOG):
        spawn_state = json.load(open(SPAWN_LOG))
        pending = spawn_state.get("pending_validation")
        if pending and pending.get("module") not in [a.get("module") for a in val_state.get("audits", [])]:
            r = validate_spawn(pending, state)
            results.append(r)
            val_state["audits"].append({**r, "ts": datetime.now(timezone.utc).isoformat()})
            emit_log("SPAWN_VALIDATED", r)
            print(f"ValidatorBus: spawn {r['module']} → {r['verdict']}")
            if r["verdict"] == "REJECTED":
                val_state["rejected"].append(r)

    # 2. Validate latest probe result from state
    round_key = f"r{state['current_round']}_result"
    result = state.get(round_key, {})
    if result and result.get("probe_id"):
        probe_r = validate_probe(
            result.get("probe_poly_c", result.get("poly_c")),
            result["N"], result.get("tau", 2), result.get("omega_k", 2),
            result.get("V_global_prev", state["V_global"] - result.get("delta_V", 0)),
            result["probe_id"]
        )
        results.append(probe_r)
        val_state["last_probe_validation"] = probe_r
        emit_log("PROBE_VALIDATED", probe_r)
        print(f"ValidatorBus: probe {probe_r['probe_id']} → {probe_r['verdict']} (drift={probe_r['drift']:.6f})")

    # 3. Capability gate — check spawned caps
    cap_dir = f"{CELL}/spawned_capabilities"
    if os.path.exists(cap_dir):
        from importlib.util import spec_from_file_location, module_from_spec
        cap_results = {}
        for f in os.listdir(cap_dir):
            if not f.endswith(".py"): continue
            try:
                spec = spec_from_file_location(f[:-3], f"{cap_dir}/{f}")
                mod = module_from_spec(spec)
                spec.loader.exec_module(mod)
                ok, reason = mod.capability_test()
                cap_results[f[4:-3]] = {"pass": ok, "reason": reason}  # strip cap_ prefix
            except Exception as e:
                cap_results[f] = {"pass": False, "reason": str(e)}
        active = [k for k, v in cap_results.items() if v["pass"]]
        blocked = [k for k, v in cap_results.items() if not v["pass"]]
        val_state["capability_gate"] = {"active": active, "blocked": blocked,
                                         "ts": datetime.now(timezone.utc).isoformat()}
        emit_log("CAPABILITY_GATE", {"active_count": len(active), "blocked_count": len(blocked),
                                      "active": active[:5], "blocked": blocked[:5]})
        print(f"ValidatorBus: capability gate — {len(active)} active, {len(blocked)} blocked")

    val_state["last_run"] = datetime.now(timezone.utc).isoformat()
    with open(VAL_STATE, "w") as f:
        json.dump(val_state, f, indent=2)

    return results

if __name__ == "__main__":
    run()
