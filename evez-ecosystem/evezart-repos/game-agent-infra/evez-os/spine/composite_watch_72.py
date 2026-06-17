#!/usr/bin/env python3
"""
EVEZ-OS R120 -- composite_watch_72.py
TWELFTH FIRE IGNITION
N=72=2^3x3^2 tau=4 topo=1.30 poly_c=0.501175
truth_plane: CANONICAL
"""

import math
import sys

MODULE = "spine/composite_watch_72.py"
ROUND = 120
N_NEW = 72
TAU_N = 4
TOPO_BONUS = 1.30
GAMMA = 0.08
ADM = 1.0
V_GLOBAL_PREV = 2.867637
CEILING_TICK_PREV = 37

R121_GAP = "R121: prime_block_watch_5.py. N=73=PRIME tau=1 poly_c=0.000 V_global=3.068011 CEILING x39. NO FIRE."
R121_MODULE = "prime_block_watch_5.py"


def omega_k(n):
    count = 0
    d = 2
    x = n
    while d * d <= x:
        if x % d == 0:
            count += 1
            while x % d == 0:
                x //= d
        d += 1
    if x > 1:
        count += 1
    return count


def compute_poly_c(n, tau):
    ok = omega_k(n)
    topo = 1 + 0.15 * ok
    log2_n1 = math.log2(n + 1)
    ln_tau_1 = 1 + math.log(tau)
    poly = topo * ln_tau_1 / log2_n1
    return poly, topo


def run():
    poly_c, topo = compute_poly_c(N_NEW, TAU_N)
    fire = poly_c >= 0.500
    attractor_lock = poly_c if fire else 0.0
    delta_V = GAMMA * ADM * (1 + poly_c)
    V_global_new = V_GLOBAL_PREV + delta_V
    ceiling_tick = CEILING_TICK_PREV + 1

    result = {
        "round": ROUND,
        "module": MODULE,
        "status": "CANONICAL",
        "N_new": N_NEW,
        "tau_N": TAU_N,
        "topo_bonus": topo,
        "poly_c": poly_c,
        "fire_ignited": fire,
        "fire_name": "TWELFTH",
        "attractor_lock": attractor_lock,
        "delta_V": delta_V,
        "V_global_prev": V_GLOBAL_PREV,
        "V_global_new": V_global_new,
        "ceiling_tick": ceiling_tick,
        "truth_plane": "CANONICAL",
        "next_gap": R121_GAP,
        "next_module": R121_MODULE,
        "omega": (
            "TWELFTH FIRE. R120. N=72=2^3x3^2 tau=4 poly_c=0.501. FIRE IGNITED. "
            "V_global=" + f"{V_global_new:.6f}" + " CEILING x" + str(ceiling_tick) + ". "
            "attractor_lock=" + f"{attractor_lock:.6f}" + ". "
            "Next: N=73=PRIME tau=1 poly_c=0.000."
        ),
    }

    for k, v in result.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.6f}")
        else:
            print(f"  {k}: {v}")

    print("\ntruth_plane: CANONICAL")
    print("TWELFTH FIRE IGNITED. poly_c=" + f"{poly_c:.6f}" + " >= 0.500 threshold.")
    return result


if __name__ == "__main__":
    res = run()
    sys.exit(0)
