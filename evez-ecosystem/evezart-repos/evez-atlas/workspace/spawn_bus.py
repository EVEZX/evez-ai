#!/usr/bin/env python3
"""
EVEZ-OS SpawnBus v1.0
Watches current_round in hyperloop_state.json.
When round advances, pre-writes the NEXT round's agent definition file,
updates PROMPT_QUEUE.md with queued compute prompt, and emits a
SpawnEvent to master_bus_log.jsonl.

Gap routing: if module file already exists for N+1, emits NOOP.
"""
import json, math, os, re
from datetime import datetime, timezone

CELL = "/cells/599dc7f9-0b2b-4460-b917-5104fcbb91ef/workspace"
STATE_FILE   = CELL + "/hyperloop_state.json"
QUEUE_FILE   = CELL + "/PROMPT_QUEUE.md"
LOG_FILE     = CELL + "/master_bus_log.jsonl"
SPAWN_LOG    = CELL + "/spawn_bus_state.json"

def factored_str(n):
    """Return prime factorization string like 2^2x23"""
    factors = {}
    d, tmp = 2, n
    while d * d <= tmp:
        while tmp % d == 0:
            factors[d] = factors.get(d, 0) + 1
            tmp //= d
        d += 1
    if tmp > 1:
        factors[tmp] = factors.get(tmp, 0) + 1
    parts = []
    for p in sorted(factors):
        parts.append(f"{p}^{factors[p]}" if factors[p] > 1 else str(p))
    return "×".join(parts) if parts else str(n)

def tau_of(n):
    """Divisor count as tau proxy (project convention)"""
    count = 0
    for i in range(1, int(n**0.5)+1):
        if n % i == 0:
            count += 2 if i != n//i else 1
    return count

def omega_k_of(n):
    """Distinct prime factor count"""
    tmp, d, count = n, 2, 0
    while d * d <= tmp:
        if tmp % d == 0:
            count += 1
            while tmp % d == 0: tmp //= d
        d += 1
    if tmp > 1: count += 1
    return count

def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5)+1):
        if n % i == 0: return False
    return True

def compute_inline(N, tau, omega_k, V_prev):
    topo = 1.0 + 0.15 * omega_k
    poly_c = topo * (1 + math.log(tau)) / math.log2(N + 2)
    fire = poly_c >= 0.500
    delta_V = 0.08 * 1.0 * poly_c
    V_new = V_prev + delta_V
    ceiling = N + 48 - 82  # round = N+48, ceiling = round-82
    return {"topo": round(topo, 4), "poly_c": round(poly_c, 6),
            "fire": fire, "delta_V": round(delta_V, 6),
            "V_new": round(V_new, 6), "ceiling": ceiling}

def emit_log(event_type, data):
    entry = {"ts": datetime.now(timezone.utc).isoformat(),
             "bus": "SpawnBus", "event": event_type, **data}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def run():
    state = json.load(open(STATE_FILE))
    N_cur = state["current_round"]
    V_cur = state["V_global"]

    # Load spawn state
    if os.path.exists(SPAWN_LOG):
        spawn_state = json.load(open(SPAWN_LOG))
    else:
        spawn_state = {"last_spawned_round": 0}

    N_next = N_cur + 1  # The module number = N (math index, not round)
    # N in module is the pure integer: round 141 → N=93
    # round = N + 48, so N = round - 48
    N_math = N_cur - 48  # N for current round
    N_math_next = N_math + 1

    if spawn_state.get("last_spawned_round") == N_cur:
        emit_log("NOOP", {"reason": f"R{N_cur} already spawned", "current_round": N_cur})
        print(f"SpawnBus: NOOP — R{N_cur} already spawned")
        return

    # Compute preview for N+1
    tau_next = tau_of(N_math_next)
    omega_next = omega_k_of(N_math_next)
    fac_next = factored_str(N_math_next)
    prime_next = is_prime(N_math_next)
    calc = compute_inline(N_math_next, tau_next, omega_next, V_cur)
    module_type = "prime_block" if prime_next else "watch_composite"
    module_name = f"{module_type}_{N_math_next}.py"

    # Build agent stub (pre-write for next round)
    agent_content = f"""# EVEZ-OS — R{N_cur+1} Agent Stub (SpawnBus pre-write)
# N={N_math_next}={fac_next}  tau={tau_next}  omega_k={omega_next}  topo={calc["topo"]}
# poly_c_est={calc["poly_c"]}  fire_est={calc["fire"]}  V_est={calc["V_new"]}  ceiling={calc["ceiling"]}
# Spawned by: SpawnBus at {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")} UTC
# Status: PRE-SPAWNED — awaiting probe confirmation
ROUND = {N_cur+1}
N = {N_math_next}
N_FACTORED = "{fac_next}"
TAU = {tau_next}
OMEGA_K = {omega_next}
TOPO = {calc["topo"]}
POLY_C_EST = {calc["poly_c"]}
FIRE_EST = {calc["fire"]}
V_GLOBAL_PREV_EST = {V_cur}
V_GLOBAL_EST = {calc["V_new"]}
CEILING_TICK_EST = {calc["ceiling"]}
TRUTH_PLANE = "CANONICAL"
SPAWNED_BY = "SpawnBus"
"""

    # Save stub locally (not committed — ValidatorBus gates commits)
    stub_path = CELL + "/spawned_agents/" + module_name
    os.makedirs(CELL + "/spawned_agents", exist_ok=True)
    with open(stub_path, "w") as f:
        f.write(agent_content)

    # Update spawn state
    spawn_state["last_spawned_round"] = N_cur
    spawn_state["last_spawned_module"] = module_name
    spawn_state["last_spawned_at"] = datetime.now(timezone.utc).isoformat()
    spawn_state["pending_validation"] = {
        "module": module_name, "round": N_cur+1,
        "N": N_math_next, "poly_c_est": calc["poly_c"],
        "fire_est": calc["fire"], "V_est": calc["V_new"]
    }
    with open(SPAWN_LOG, "w") as f:
        json.dump(spawn_state, f, indent=2)

    emit_log("SPAWNED", {
        "module": module_name, "round": N_cur+1,
        "N": N_math_next, "N_str": fac_next,
        "poly_c_est": calc["poly_c"], "fire_est": calc["fire"],
        "V_est": calc["V_new"], "ceiling": calc["ceiling"],
        "stub_path": stub_path
    })
    print(f"SpawnBus: SPAWNED {module_name} R{N_cur+1} N={N_math_next}={fac_next} poly_c_est={calc['poly_c']} fire_est={calc['fire']}")

if __name__ == "__main__":
    run()
