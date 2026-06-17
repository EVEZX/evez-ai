#!/usr/bin/env python3
"""
EVEZ-OS Spine Module: watch_composite_74.py
Round: R122 | N=74=2x37 | tau=2 | COMPOSITE WATCH
V_global: 3.067731 -> 3.176001 | CEILING x40 | truth_plane: CANONICAL
"""
import json, math, sys

ROUND = 122
N = 74
TAU = 2
GAMMA = 0.08
ADM = 1.0

def omega_k(n):
    count = 0; d = 2; x = n
    while d * d <= x:
        if x % d == 0:
            count += 1
            while x % d == 0: x //= d
        d += 1
    if x > 1: count += 1
    return count

def compute():
    ok = omega_k(N)           # N=74=2*37 -> omega_k=2
    topo_bonus = round(1 + 0.15 * ok, 6)  # 1.30
    poly_c = round(topo_bonus * (1 + math.log(TAU)) / math.log2(N + 1), 6)
    fire_ignited = poly_c >= 0.500
    V_global_prev = 3.067731
    delta_V = round(GAMMA * ADM * (1 + poly_c), 6)
    V_global_new = round(V_global_prev + delta_V, 6)
    ceiling_tick = 40
    return {
        "round": ROUND,
        "N": N, "N_str": "74=2x37", "tau": TAU,
        "omega_k": ok, "topo_bonus": topo_bonus,
        "poly_c": poly_c, "fire_ignited": fire_ignited,
        "fire_name": "", "attractor_lock": 0.0, "fire_res": 0.0,
        "delta_V": delta_V,
        "V_global_prev": V_global_prev,
        "V_global_new": V_global_new,
        "ceiling_tick": ceiling_tick,
        "milestone": "COMPOSITE_WATCH",
        "truth_plane": "CANONICAL",
        "omega": (
            f"R{ROUND}. N=74=2x37 tau=2 topo=1.30 poly_c={poly_c:.6f}. "
            f"NO FIRE. V_global={V_global_new:.6f} CEILING x{ceiling_tick}. "
            f"Next: N=75=3x5^2 tau=3 topo=1.30 poly_c~0.437."
        )
    }

if __name__ == "__main__":
    r = compute()
    print(json.dumps(r, indent=2))
    assert r["V_global_new"] == 3.176001, f"V mismatch: {r['V_global_new']}"
    assert r["poly_c"] == 0.353372, f"poly_c mismatch: {r['poly_c']}"
    assert r["fire_ignited"] == False
    assert r["ceiling_tick"] == 40
    print("R122 CANONICAL. COMPOSITE WATCH. EXIT 0.", file=sys.stderr)
    sys.exit(0)
