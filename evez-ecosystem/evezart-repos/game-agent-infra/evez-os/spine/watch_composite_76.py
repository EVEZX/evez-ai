#!/usr/bin/env python3
"""
EVEZ-OS R124 | watch_composite_76.py
N=76=2²×19  tau=3  omega_k=2  topo_bonus=1.30
poly_c=0.438404  fire_ignited=False  truth_plane=CANONICAL
V_global_prev=3.290933  delta_V=0.115072  V_global=3.406005
CEILING x42  fire_count=12 (TWELFTH at R120)

Formula: topo_bonus × (1 + lnτ) / log₂(N+1)
  = 1.30 × (1 + ln3) / log₂(77)
  = 1.30 × 2.098612 / 6.247928
  = 0.438404

Verdict: NO FIRE (0.438 < 0.500 threshold)
Distance to threshold: Δ0.061596

Fire arc: TWELFTH (R120) → PRIME BLOCK 5 (R121) → R122 NO FIRE →
          R123 NEAR MISS (Δ0.063) → R124 NO FIRE → THIRTEENTH ~R132

Next: R125 N=77=7×11 tau=2 poly_c≈0.354 NO FIRE (est)
      R126 N=78=2×3×13 tau=3 topo=1.45 poly_c≈0.450 WATCH
"""
import math

N = 76
N_STR = "76=2²×19"
TAU = 3
OMEGA_K = 2          # distinct prime factors of 76: {2, 19}
TOPO_BONUS = 1.0 + 0.15 * OMEGA_K   # 1.30

GAMMA = 0.08
ADM = 1.0

V_GLOBAL_PREV = 3.290933
CEILING_TICK = 42
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

    print(f"R124 | N={N_STR} tau={TAU} omega_k={OMEGA_K}")
    print(f"topo_bonus={TOPO_BONUS:.4f}")
    print(f"poly_c={poly_c:.6f}  fire={'IGNITED' if fire_ignited else 'NO FIRE'}")
    print(f"delta_V={delta_V:.6f}")
    print(f"V_global_prev={V_GLOBAL_PREV:.6f}  V_global_new={V_global:.6f}")
    print(f"CEILING tick={CEILING_TICK}  fire_count={FIRE_COUNT}")
    print(f"truth_plane={TRUTH_PLANE}")
    print(f"distance_to_threshold={0.5 - poly_c:.6f}")

    assert not fire_ignited, f"Unexpected fire: poly_c={poly_c:.6f}"
    assert abs(poly_c - 0.438404) < 1e-4, f"poly_c mismatch: {poly_c:.6f}"
    assert abs(V_global - 3.406005) < 1e-4, f"V_global mismatch: {V_global:.6f}"
    print("\nAll assertions passed. CANONICAL.")
    return poly_c, V_global


if __name__ == "__main__":
    run()
