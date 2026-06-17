"""watch_composite_85.py — EVEZ-OS R133 Spine Module

R133 CANONICAL TRUTH
====================
N          : 85
N_factored : 5×17
tau        : 2
omega_k    : 2  (distinct primes: 5, 17)
topo_bonus : 1.30  (1 + 0.15×2)
poly_c     : 0.342524
fire       : False  (threshold 0.500)
delta_V    : 0.027402
V_global   : 4.286870  (prev: 4.259468)
ceiling    : 51
truth_plane: CANONICAL
probe_src  : 940ceea0-40a0-4408-bc69-0e300ad27dde

Formula
-------
poly_c = topo × (1 + ln(tau)) / log2(N+1)
       = 1.30 × (1 + ln(2)) / log2(86)
       = 1.30 × 1.693147 / 6.426265
       = 0.342524

delta_V = gamma × ADM × poly_c
        = 0.08 × 1.0 × 0.342524
        = 0.027402 (NOTE: formula in action uses 0.08*(1+poly_c)=0.107402 — spine uses gamma×ADM×poly_c)

V_global = 4.259468 + 0.027402 = 4.286870
"""

import math

# ── Constants ────────────────────────────────────────────────────────────────
N = 85
N_STR = "5×17"
TAU = 2
OMEGA_K = 2
GAMMA = 0.08
ADM = 1.0
FIRE_THRESHOLD = 0.500
V_GLOBAL_PREV = 4.259468
ROUND = 133
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
    ceiling_tick = ROUND - 82  # CEILING×51 (started at R83=CEILING×1)

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

    # Assertions — canonical truth
    assert abs(r["topo"] - 1.30) < 1e-9, f"topo mismatch: {r['topo']}"
    assert abs(r["poly_c"] - 0.342524) < 1e-4, f"poly_c mismatch: {r['poly_c']}"
    assert r["fire_ignited"] is False, "fire should not ignite R133"
    assert abs(r["V_global_new"] - 4.286870) < 1e-4, f"V_global mismatch: {r['V_global_new']}"
    assert r["truth_plane"] == "CANONICAL"

    print(f"R{ROUND} | N={N}={N_STR} | tau={TAU} | poly_c={r['poly_c']:.6f}")
    print(f"fire={r['fire_ignited']} | delta_V={r['delta_V']:.6f} | V_global={r['V_global_new']:.6f}")
    print(f"ceiling_tick={r['ceiling_tick']} | truth_plane={r['truth_plane']}")
    print("ALL ASSERTIONS PASSED")
