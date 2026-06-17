"""
EVEZ-OS Hyperloop — Round 132
Module: watch_composite_84.py
Truth Plane: CANONICAL

N = 84 = 2² × 3 × 7
tau = 3        (Omega(84) = sum of prime factor exponents = 2+1+1 = 4, but tau here = distinct prime count = 3)
omega_k = 3   (distinct prime factors: 2, 3, 7)
topo = 1 + 0.15 * omega_k = 1 + 0.45 = 1.45
ln(tau) = ln(3) = 1.098612
log2(N+1) = log2(85) = 6.409390
poly_c = topo * (1 + ln(tau)) / log2(N+1)
       = 1.45 * 2.098612 / 6.409390
       = 3.042987 / 6.409390
       = 0.474743
fire_ignited = False  (poly_c < 0.500 threshold)
delta_V = 0.08 * (1 + poly_c) = 0.08 * 1.474743 = 0.117979
V_global_prev = 4.141489
V_global_new  = 4.141489 + 0.117979 = 4.259468
ceiling_tick  = 50
fire_count    = 12 (unchanged)

Note: THIRTEENTH FIRE WATCH. N=84=2²×3×7 is maximally composite for this arc.
poly_c=0.474743 — closest approach since R126 (Δ=0.025257 from threshold).
V_global crossed 4.25 for first time. CEILING×50 milestone.
"""

import math

N = 84
tau = 3          # distinct prime factors: {2, 3, 7}
omega_k = 3
V_global_prev = 4.141489
gamma = 0.08
FIRE_THRESHOLD = 0.500


def compute_topo(omega_k: int) -> float:
    """Topological bonus from prime factor diversity."""
    return 1.0 + 0.15 * omega_k


def compute_poly_c(topo: float, tau: int, N: int) -> float:
    """Canonical poly_c formula."""
    return topo * (1.0 + math.log(tau)) / math.log2(N + 1)


def compute_delta_V(gamma: float, poly_c: float) -> float:
    """V_global increment."""
    return gamma * (1.0 + poly_c)


def run_round() -> dict:
    topo = compute_topo(omega_k)
    poly_c = compute_poly_c(topo, tau, N)
    fire_ignited = poly_c >= FIRE_THRESHOLD
    delta_V = compute_delta_V(gamma, poly_c)
    V_global_new = V_global_prev + delta_V

    result = {
        "round": 132,
        "N": N,
        "N_str": "84=2²×3×7",
        "tau": tau,
        "omega_k": omega_k,
        "topo": topo,
        "poly_c": round(poly_c, 6),
        "fire_ignited": fire_ignited,
        "delta_V": round(delta_V, 6),
        "V_global_prev": V_global_prev,
        "V_global_new": round(V_global_new, 6),
        "ceiling_tick": 50,
        "truth_plane": "CANONICAL",
        "note": "THIRTEENTH FIRE WATCH — NO FIRE. poly_c=0.474743 closest approach since R126. V_global crossed 4.25. CEILING×50.",
    }

    # Assertions
    assert abs(result["topo"] - 1.45) < 1e-9, f"topo mismatch: {result['topo']}"
    assert abs(result["poly_c"] - 0.474743) < 1e-4, f"poly_c mismatch: {result['poly_c']}"
    assert result["fire_ignited"] is False, "fire should not be ignited at R132"
    assert abs(result["V_global_new"] - 4.259468) < 1e-4, f"V_global mismatch: {result['V_global_new']}"

    return result


if __name__ == "__main__":
    import json
    r = run_round()
    print(json.dumps(r, indent=2, ensure_ascii=False))
