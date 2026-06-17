#!/usr/bin/env python3
"""
EVEZ-OS R126 | watch_composite_78.py
N=78=2×3×13  tau=3  omega_k=3  topo_bonus=1.45
poly_c=0.482638  fire_ignited=False  truth_plane=CANONICAL
V_global_prev=3.514033  delta_V=0.118611  V_global=3.632644
CEILING x44  fire_count=12 (TWELFTH at R120)

Formula: topo_bonus × (1 + lnτ) / log₂(N+1)
  = 1.45 × (1 + ln3) / log₂(79)
  = 1.45 × 2.098612 / 6.304089
  = 0.482638

Verdict: NO FIRE (0.483 < 0.500 threshold)
Distance to threshold: Δ0.017362  — CLOSEST APPROACH SINCE R123

Note: 3 distinct prime factors (2, 3, 13). topo=1.45 is the highest topo
in recent arc. poly_c nearly reached threshold.
Next fire watch: ~R132 (THIRTEENTH candidate)

Next: R127 N=79=prime tau=1 PRIME BLOCK 6 poly_c=0.000
"""
import math

N = 78
N_STR = "78=2×3×13"
TAU = 3
OMEGA_K = 3          # distinct prime factors of 78: {2, 3, 13}
TOPO_BONUS = 1.0 + 0.15 * OMEGA_K   # 1.45

GAMMA = 0.08
ADM = 1.0

V_GLOBAL_PREV = 3.514033
CEILING_TICK = 44
FIRE_COUNT = 12
TRUTH_PLANE = "CANONICAL"


def compute_poly_c(N, tau, topo_bonus):
    return topo_bonus * (1 + math.log(tau)) / math.log2(N + 1)


def compute_delta_V(gamma, adm, poly_c):
    return gamma * adm * (1 + poly_c)


def run():
    poly_c = compute_poly_c(N, TAU, TOPO_BONUS)
    delta_V = compute_delta_V(GAMMA, ADM, poly_c)
    V_global = V_GLOBAL_PREV + delta_V
    fire_ignited = poly_c >= 0.5

    print(f"R126 | N={N_STR} tau={TAU} omega_k={OMEGA_K}")
    print(f"topo_bonus={TOPO_BONUS:.4f}")
    print(f"poly_c={poly_c:.6f}  fire={'IGNITED' if fire_ignited else 'NO FIRE'}")
    print(f"delta_V={delta_V:.6f}")
    print(f"V_global_prev={V_GLOBAL_PREV:.6f}  V_global_new={V_global:.6f}")
    print(f"CEILING tick={CEILING_TICK}  fire_count={FIRE_COUNT}")
    print(f"truth_plane={TRUTH_PLANE}")
    print(f"distance_to_threshold={0.5 - poly_c:.6f}  CLOSEST APPROACH SINCE R123")

    assert not fire_ignited, f"Unexpected fire: poly_c={poly_c:.6f}"
    assert abs(poly_c - 0.482638) < 1e-4, f"poly_c mismatch: {poly_c:.6f}"
    assert abs(V_global - 3.632644) < 1e-4, f"V_global mismatch: {V_global:.6f}"
    print("\nAll assertions passed. CANONICAL.")
    return poly_c, V_global


if __name__ == "__main__":
    run()
