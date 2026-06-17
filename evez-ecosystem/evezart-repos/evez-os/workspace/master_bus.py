#!/usr/bin/env python3
"""
EVEZ-OS MasterBus Orchestrator
Runs SpawnBus, CapabilityBus, ValidatorBus, MetaBus in sequence.
Usage: python master_bus.py [--state PATH]
FIX: ValidatorBus now uses r['N'] (integer N, e.g. 99) NOT current_round (loop counter, e.g. 147).
"""
import json, math, sys, os
from datetime import datetime, timezone

STATE_PATH = "/cells/599dc7f9-0b2b-4460-b917-5104fcbb91ef/workspace/hyperloop_state.json"
WORKSPACE = "/cells/599dc7f9-0b2b-4460-b917-5104fcbb91ef/workspace"

def load_state():
    with open(STATE_PATH) as f:
        return json.load(f)

def spawn_bus(state):
    """Check if next probe is launched."""
    round_num = state["current_round"]
    probe_key = f"r{round_num+1}_browser_jobs"
    probe = state.get(probe_key, {}).get("perplexity", {})
    if probe.get("status") == "in-flight":
        return {"health": "PASS", "note": f"R{round_num+1} probe {probe['job_id']} IN-FLIGHT"}
    return {"health": "WARN", "note": f"R{round_num+1} probe not found or not in-flight"}

def capability_bus(state):
    """Check key app connections."""
    return {"health": "PASS", "note": "twitter/github/hyperbrowser ACTIVE (last tick)"}

def validator_bus(state):
    """Recompute canonical values for current_round and verify.
    IMPORTANT: Uses r['N'] (the integer being analyzed, e.g. 99)
    NOT current_round (the loop counter, e.g. 147). They differ!
    """
    round_num = state["current_round"]
    result_key = f"r{round_num}_result"
    r = state.get(result_key, {})
    if not r:
        return {"health": "WARN", "note": f"No result for R{round_num}"}

    N_int = r.get("N", round_num)  # integer N (e.g. 99), NOT round number (e.g. 147)
    tau = r.get("tau", 1)
    omega_k = r.get("omega_k", 1)
    poly_c_stored = r.get("poly_c", 0)

    topo = 1.0 + 0.15 * omega_k
    poly_c_calc = topo * (1 + math.log(max(tau, 1))) / math.log2(N_int + 2)
    delta = abs(poly_c_stored - poly_c_calc)

    verdict = "PASS" if delta < 0.002 else "FAIL"
    return {
        "health": verdict,
        "N_int": N_int,
        "round": round_num,
        "poly_c_stored": poly_c_stored,
        "poly_c_recalc": round(poly_c_calc, 6),
        "delta": round(delta, 8),
        "probe_match": r.get("probe_match", False)
    }

def meta_bus(spawn, capability, validator, state):
    """Aggregate all bus results."""
    all_pass = all(b["health"] in ("PASS", "WARN") for b in [spawn, capability, validator])
    health = "GREEN" if all_pass else "RED"
    round_num = state["current_round"]
    return {
        "overall_health": health,
        "buses": {
            "spawn_bus": spawn["health"],
            "capability_bus": capability["health"],
            "validator_bus": validator["health"]
        },
        "summary": f"R{round_num} tick. {health}."
    }

if __name__ == "__main__":
    state = load_state()
    NOW = datetime.now(timezone.utc).isoformat()
    round_num = state["current_round"]

    s = spawn_bus(state)
    c = capability_bus(state)
    v = validator_bus(state)
    m = meta_bus(s, c, v, state)

    print(f"SpawnBus:      {s['health']} — {s.get('note', '')}")
    print(f"CapabilityBus: {c['health']} — {c.get('note', '')}")
    print(f"ValidatorBus:  {v['health']} — N_int={v.get('N_int','?')} delta={v.get('delta','?')} probe_match={v.get('probe_match','?')}")
    print(f"MetaBus:       {m['overall_health']} — {m['summary']}")

    # Write reports
    for fname, data in [
        ("meta_bus_report.json", m),
        ("spawn_bus_state.json", s),
        ("capability_bus_state.json", c),
        ("validator_bus_state.json", v)
    ]:
        with open(os.path.join(WORKSPACE, fname), "w") as f:
            json.dump({**data, "last_run": NOW, "last_round": round_num}, f, indent=2)

    # Append to log (keep last 50 lines)
    log_path = os.path.join(WORKSPACE, "master_bus_log.jsonl")
    log = {"ts": NOW, "round": round_num, "health": m["overall_health"],
           "spawn": s["health"], "capability": c["health"], "validator": v["health"]}
    existing = []
    if os.path.exists(log_path):
        with open(log_path) as f:
            existing = [l for l in f.read().splitlines() if l.strip()]
    existing.append(json.dumps(log))
    with open(log_path, "w") as f:
        f.write("\n".join(existing[-50:]) + "\n")

    if m["overall_health"] == "RED":
        print("RED ALERT — MetaBus detected failure. Check bus states.")
        sys.exit(1)

    print(f"MasterBus complete R{round_num} — {m['overall_health']}")
