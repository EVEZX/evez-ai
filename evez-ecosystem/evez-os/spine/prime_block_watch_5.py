#!/usr/bin/env python3
"""
EVEZ-OS Spine Module: prime_block_watch_5.py
Round: R121 | N=73=PRIME | tau=1 | PRIME BLOCK 5
V_global: 2.987731 -> 3.067731 | CEILING x39 | truth_plane: CANONICAL
"""
import json, math, sys

ROUND = 121
N = 73
TAU = 1
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
    ok = omega_k(N)
    topo_bonus = round(1 + 0.15 * ok, 6)
    poly_c = 0.0
    V_global_prev = 2.987731
    delta_V = round(GAMMA * ADM * (1 + poly_c), 6)
    V_global_new = round(V_global_prev + delta_V, 6)
    return {
        "round": ROUND,
        "N": N, "N_str": "73=PRIME", "tau": TAU,
        "omega_k": ok, "topo_bonus": topo_bonus,
        "poly_c": poly_c, "fire_ignited": False,
        "fire_name": "", "attractor_lock": 0.0, "fire_res": 0.0,
        "delta_V": delta_V,
        "V_global_prev": V_global_prev,
        "V_global_new": V_global_new,
        "ceiling_tick": 39,
        "milestone": "PRIME_BLOCK_5",
        "truth_plane": "CANONICAL",
        "omega": (
            f"PRIME BLOCK 5. R{ROUND}. N=73=PRIME tau=1 poly_c=0.000. "
            f"NO FIRE. V_global={V_global_new} CEILING x39. "
            f"Next: N=74=2x37 tau=2 topo=1.30 poly_c~0.353."
        )
    }

if __name__ == "__main__":
    r = compute()
    print(json.dumps(r, indent=2))
    assert r["V_global_new"] == 3.067731
    assert r["poly_c"] == 0.0
    assert r["fire_ignited"] == False
    assert r["ceiling_tick"] == 39
    print("R121 CANONICAL. PRIME BLOCK 5. EXIT 0.", file=sys.stderr)
    sys.exit(0)
