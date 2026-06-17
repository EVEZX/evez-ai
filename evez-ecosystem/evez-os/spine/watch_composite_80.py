#!/usr/bin/env python3
"""
EVEZ-OS R128 | watch_composite_80.py
N=80=2⁴×5  tau=2  omega_k=2  topo_bonus=1.30
poly_c=0.347249  fire_ignited=False  truth_plane=CANONICAL
V_global_prev=3.727197  delta_V=0.107780  V_global=3.834977
CEILING x46  fire_count=12  MODERATE COMPOSITE

Formula: topo_bonus × (1 + lnτ) / log₂(N+1)
  = 1.30 × (1 + ln2) / log₂(81)
  = 1.30 × 1.693147 / 6.339850
  = 0.347249

Verdict: NO FIRE (0.347 < 0.500)
Follows R127 PRIME BLOCK 6 structural reset.
Moderate composite — 2 distinct primes, topo=1.30.
Next: R129 N=81=3⁴ tau=2 omega_k=1 topo=1.15 poly_c≈0.288 (single prime power)
"""
import math

N = 80
N_STR = "80=2⁴×5"
TAU = 2
OMEGA_K = 2          # distinct prime factors of 80: {2, 5}
TOPO_BONUS = 1.0 + 0.15 * OMEGA_K   # 1.30

GAMMA = 0.08
ADM = 1.0

V_GLOBAL_PREV = 3.727197
CEILING_TICK = 46
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

    print(f"R128 | N={N_STR} tau={TAU} omega_k={OMEGA_K}")
    print(f"topo_bonus={TOPO_BONUS:.4f}")
    print(f"poly_c={poly_c:.6f}  fire={'IGNITED' if fire_ignited else 'NO FIRE'}")
    print(f"delta_V={delta_V:.6f}")
    print(f"V_global_prev={V_GLOBAL_PREV:.6f}  V_global_new={V_global:.6f}")
    print(f"CEILING tick={CEILING_TICK}  fire_count={FIRE_COUNT}")
    print(f"truth_plane={TRUTH_PLANE}")

    assert not fire_ignited, f"Unexpected fire: poly_c={poly_c:.6f}"
    assert abs(poly_c - 0.347249) < 1e-4, f"poly_c mismatch: {poly_c:.6f}"
    assert abs(V_global - 3.834977) < 1e-4, f"V_global mismatch: {V_global:.6f}"
    print("\nAll assertions passed. CANONICAL.")
    return poly_c, V_global


if __name__ == "__main__":
    run()
