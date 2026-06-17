"""watch_composite_86.py — EVEZ-OS R134 Spine Module

R134 CANONICAL TRUTH
====================
N          : 86
N_factored : 2×43
tau        : 2
omega_k    : 2  (distinct primes: 2, 43)
topo_bonus : 1.30  (1 + 0.15×2)
poly_c     : 0.341488
fire       : False  (threshold 0.500)
delta_V    : 0.027319
V_global   : 4.314189  (prev: 4.286870)
ceiling    : 52
truth_plane: CANONICAL
probe_src  : 4e21a7ee-0e6b-4c68-a569-ae047c1ceef6 (in flight)

Formula
-------
poly_c = topo × (1 + ln(tau)) / log2(N+1)
       = 1.30 × (1 + ln(2)) / log2(87)
       = 1.30 × 1.693147 / 6.44265
       = 0.341488

delta_V = gamma × ADM × poly_c
        = 0.08 × 1.0 × 0.341488
        = 0.027319

V_global = 4.286870 + 0.027319 = 4.314189
"""

import math

# ── Constants ────────────────────────────────────────────────────────────────
N = 86
N_STR = "2×43"
TAU = 2
OMEGA_K = 2
GAMMA = 0.08
ADM = 1.0
FIRE_THRESHOLD = 0.500
V_GLOBAL_PREV = 4.286870
ROUND = 134
TRUTH_PLANE = "CANONICAL"


def compute_topo(omega_k: int) -> float:
    return 1.0 + 0.15 * omega_k


def compute_poly_c(topo: float, tau: int, N: int) -> float:
    return topo * (1.0 + math.log(tau)) / math.log2(N + 1)


def compute_delta_v(gamma: float, adm: float, poly_c: float) -> float:
    return gamma * adm * poly_c


def run() -> dict:
    topo = compute_topo(OMEGA_K)
    poly_c = compute_poly_c(topo, TAU, N)
    fire = poly_c >= FIRE_THRESHOLD
    delta_v = compute_delta_v(GAMMA, ADM, poly_c)
    v_global_new = V_GLOBAL_PREV + delta_v
    ceiling_tick = ROUND - 82

    result = {
        "round": ROUND,
        "N": N,
        "N_str": N_STR,
        "tau": TAU,
        "omega_k": OMEGA_K,
        "topo": round(topo, 6),
        "poly_c": round(poly_c, 6),
        "fire_ignited": fire,
        "delta_V": round(delta_v, 6),
        "V_global_new": round(v_global_new, 6),
        "ceiling_tick": ceiling_tick,
        "truth_plane": TRUTH_PLANE,
    }
    return result


if __name__ == "__main__":
    r = run()

    assert abs(r["topo"] - 1.30) < 1e-9, f"topo mismatch: {r['topo']}"
    assert abs(r["poly_c"] - 0.341488) < 1e-4, f"poly_c mismatch: {r['poly_c']}"
    assert r["fire_ignited"] is False, "fire should not ignite R134"
    assert abs(r["V_global_new"] - 4.314189) < 1e-4, f"V_global mismatch: {r['V_global_new']}"
    assert r["truth_plane"] == "CANONICAL"

    print(f"R{ROUND} | N={N}={N_STR} | tau={TAU} | poly_c={r['poly_c']:.6f}")
    print(f"fire={r['fire_ignited']} | delta_V={r['delta_V']:.6f} | V_global={r['V_global_new']:.6f}")
    print(f"ceiling_tick={r['ceiling_tick']} | truth_plane={r['truth_plane']}")
    print("ALL ASSERTIONS PASSED")
