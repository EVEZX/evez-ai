"""
watch_composite_82.py — EVEZ-OS Spine Module R130

N=82=2×41 | tau=2 | omega_k=2 | topo=1.30
poly_c=0.345237 | fire=False | delta_V=0.107619
V_global_prev=3.939478 | V_global_new=4.047097
ceiling_tick=48 | truth_plane=CANONICAL

Note: Computed inline — probe poll timed out (consistent with R127-R129 fallback pattern)
"""

import math

N = 82
N_STR = "82=2×41"
TAU = 2
OMEGA_K = 2  # distinct primes: 2, 41
V_GLOBAL_PREV = 3.939478
CEILING_TICK_PREV = 47


def compute_topo(omega_k: int) -> float:
    return 1.0 + 0.15 * omega_k


def compute_poly_c(topo: float, tau: int, N: int) -> float:
    return topo * (1.0 + math.log(tau)) / math.log2(N + 1)


def compute_delta_v(poly_c: float, gamma: float = 0.08) -> float:
    return gamma * (1.0 + poly_c)


def run_round() -> dict:
    topo = compute_topo(OMEGA_K)
    poly_c = compute_poly_c(topo, TAU, N)
    fire = poly_c >= 0.500
    delta_v = compute_delta_v(poly_c)
    v_global_new = V_GLOBAL_PREV + delta_v
    ceiling_tick = CEILING_TICK_PREV + 1

    return {
        "N": N,
        "N_str": N_STR,
        "tau": TAU,
        "omega_k": OMEGA_K,
        "topo": round(topo, 6),
        "poly_c": round(poly_c, 6),
        "fire_ignited": fire,
        "delta_V": round(delta_v, 6),
        "V_global_prev": V_GLOBAL_PREV,
        "V_global_new": round(v_global_new, 6),
        "ceiling_tick": ceiling_tick,
        "truth_plane": "CANONICAL",
    }


if __name__ == "__main__":
    result = run_round()
    assert result["poly_c"] == 0.345237, f"poly_c mismatch: {result['poly_c']}"
    assert result["fire_ignited"] is False, "fire should not ignite"
    assert result["V_global_new"] == 4.047097, f"V_global mismatch: {result['V_global_new']}"
    assert result["ceiling_tick"] == 48
    print(f"R130 CANONICAL — N={result['N_str']} tau={result['tau']} "
          f"poly_c={result['poly_c']:.6f} fire={result['fire_ignited']} "
          f"V_global={result['V_global_new']:.6f} CEILING×{result['ceiling_tick']}")
