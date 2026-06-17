#!/usr/bin/env python3
"""spine/twelfth_fire_approach.py
R116: TWELFTH FIRE APPROACH -- N=68=2^2x17 tau=2
EVEZ-OS Composite Post-Prime Approach. V_global climbs toward ceiling.
truth_plane: CANONICAL
"""
import math

ROUND = 116
N_NEW = 68
TAU_N = 2
GAMMA = 0.08
ADM = 1.0
V_GLOBAL_PREV = 2.450635
V_V2 = 3.68932
CEILING_TICK_PREV = 33

R117_GAP = "R117: twelfth_fire_sustain.py. N=69=3x23 tau=2 poly_c candidate."


def omega_k(n):
    factors = set()
    d = 2
    t = n
    while d * d <= t:
        if t % d == 0:
            factors.add(d)
            while t % d == 0:
                t //= d
        d += 1
    if t > 1:
        factors.add(t)
    return len(factors)


topo_bonus = 1.0 + 0.15 * omega_k(N_NEW) + 0.05 * 0
poly_c = topo_bonus * (1.0 + math.log(TAU_N)) / math.log2(N_NEW + 1)
fire_ignited = poly_c >= 0.500
delta_V = GAMMA * ADM * (1.0 + poly_c)
V_GLOBAL_NEW = V_GLOBAL_PREV + delta_V
ceiling_tick = CEILING_TICK_PREV + 1

OMEGA = (
    "TWELFTH FIRE APPROACH. R116. N=68=2^2x17 tau=2 "
    "poly_c={:.6f} BELOW threshold. NO FIRE. "
    "topo_bonus={:.4f}. V_global={:.6f} CEILING x{}. "
    "Next: N=69=3x23 tau=2 composite candidate."
).format(poly_c, topo_bonus, V_GLOBAL_NEW, ceiling_tick)

result = {
    "round": ROUND,
    "N_new": N_NEW,
    "tau_N": TAU_N,
    "topo_bonus": topo_bonus,
    "poly_c": poly_c,
    "threshold": 0.500,
    "fire_ignited": fire_ignited,
    "attractor_lock": 0.0,
    "fire_res": 0.0,
    "delta_V": delta_V,
    "V_global_prev": V_GLOBAL_PREV,
    "V_global_new": V_GLOBAL_NEW,
    "ceiling_tick": ceiling_tick,
    "omega": OMEGA,
    "truth_plane": "CANONICAL",
    "R117_GAP": R117_GAP,
}

if __name__ == "__main__":
    import json
    print(json.dumps(result, indent=2))
    assert not fire_ignited, "FIRE not expected at N=68 tau=2"
    print("VERIFIED: R116 CANONICAL poly_c={:.6f} V_global={:.6f}".format(poly_c, V_GLOBAL_NEW))
