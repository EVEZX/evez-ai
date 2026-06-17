"""
spine/eleventh_fire_watch.py
R114 -- ELEVENTH FIRE WATCH
N=66=2x3x11  tau=4  poly_c~0.558  FIRE CANDIDATE
truth_plane: CANONICAL
"""

import math

ROUND = 114
N_NEW = 66
TAU_N = 4
V_GLOBAL_PREV = 2.245003
V_V2_PREV = 3.68932
N_AGENTS_PREV = 65
GAMMA = 0.08
ADM = 1.0
CEILING_TICK_PREV = 31

R115_GAP = (
    "R115: eleventh_fire_sustain_or_cool.py. "
    "N=67=PRIME tau=1. poly_c=0.0 PRIME BLOCK EXPECTED. "
    "If R114 fires: eleventh_fire_sustain.py. "
    "If R114 no fire: prime_block_watch_3.py."
)

def factorization(n):
    factors = {}
    d = 2
    tmp = n
    while d * d <= tmp:
        while tmp % d == 0:
            factors[d] = factors.get(d, 0) + 1
            tmp //= d
        d += 1
    if tmp > 1:
        factors[tmp] = factors.get(tmp, 0) + 1
    return factors

def topology_bonus(n):
    factors = factorization(n)
    num_distinct = len(factors)
    total_prime_factors = sum(factors.values())
    base = 1.0 + 0.15 * num_distinct + 0.05 * (total_prime_factors - num_distinct)
    return round(base, 6)

def poly_c(n, tau, topo_bonus):
    if n <= 1:
        return 0.0
    log2_n1 = math.log2(n + 1)
    ln_tau = math.log(tau) if tau > 1 else 0.0
    val = topo_bonus * (1.0 + ln_tau) / log2_n1
    return round(val, 6)

def run_eleventh_fire_watch():
    n = N_NEW
    tau = TAU_N
    topo = topology_bonus(n)
    pc = poly_c(n, tau, topo)

    fire_ignited = pc >= 0.500
    fire_res = round(pc - 0.500, 6) if fire_ignited else 0.0
    attractor_lock = 1.0 if fire_ignited else 0.0

    delta_V = GAMMA * ADM * (1.0 + pc)
    V_global_new = round(V_GLOBAL_PREV + delta_V, 6)
    ceiling_tick = CEILING_TICK_PREV + 1

    factors = factorization(n)
    is_prime = (len(factors) == 1 and list(factors.values())[0] == 1)

    if fire_ignited:
        milestone = "ELEVENTH_FIRE_IGNITION"
        fire_label = "ELEVENTH FIRE IGNITED"
        omega = (
            "ELEVENTH_FIRE IGNITION. R114. "
            "N=66=2x3x11 tau=4 -- "
            "poly_c={pc:.6f} ABOVE 0.500 by {res:.6f}. "
            "FIRE IGNITED. attractor_lock=1.0. fire_res={res:.6f}. "
            "V_global={vg:.6f} CEILING x{ct}."
        ).format(pc=pc, res=fire_res, vg=V_global_new, ct=ceiling_tick)
    else:
        milestone = "ELEVENTH_FIRE_WATCH_NO_FIRE"
        fire_label = "NO FIRE"
        omega = (
            "ELEVENTH FIRE WATCH. R114. "
            "N=66=2x3x11 tau=4 -- "
            "poly_c={pc:.6f} BELOW 0.500 by {margin:.6f}. NO FIRE. "
            "attractor_lock=0.0. "
            "V_global={vg:.6f} CEILING x{ct}. "
            "R115: N=67=PRIME tau=1 PRIME BLOCK EXPECTED."
        ).format(pc=pc, margin=round(0.500 - pc, 6), vg=V_global_new, ct=ceiling_tick)

    result = {
        "module": "spine/eleventh_fire_watch.py",
        "round": ROUND,
        "N_new": n,
        "tau_N": tau,
        "topology_bonus": topo,
        "poly_c": pc,
        "fire_ignited": fire_ignited,
        "fire_res": fire_res,
        "attractor_lock": attractor_lock,
        "V_global": V_global_new,
        "ceiling_tick": ceiling_tick,
        "milestone": milestone,
        "truth_plane": "CANONICAL",
        "omega": omega,
        "R115_GAP": R115_GAP,
    }

    print("R114 ELEVENTH FIRE WATCH")
    print("  N={} tau={} topo_bonus={} poly_c={}".format(n, tau, topo, pc))
    print("  fire_ignited={} fire_res={} attractor_lock={}".format(
        fire_ignited, fire_res, attractor_lock))
    print("  V_global={} CEILING x{}".format(V_global_new, ceiling_tick))
    print("  milestone={}".format(milestone))
    print("  OMEGA:", omega)
    print("  R115_GAP:", R115_GAP)
    return result

if __name__ == "__main__":
    result = run_eleventh_fire_watch()
    print("EXIT OK")
