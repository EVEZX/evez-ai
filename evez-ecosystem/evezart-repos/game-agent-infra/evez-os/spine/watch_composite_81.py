"""watch_composite_81.py — EVEZ-OS R129 CANONICAL

Round      : 129
N          : 81 = 3⁴
tau        : 2
omega_k    : 1  (distinct primes: {3})
topo_bonus : 1.15
poly_c     : 0.306267
fire       : False  (0.306267 < 0.500)
delta_V    : 0.104501
V_global   : 3.834977 → 3.939478
ceiling_tick: 47
truth_plane: CANONICAL

Formula:
  topo  = 1 + 0.15 * omega_k               = 1 + 0.15*1 = 1.15
  poly_c= topo * (1 + ln(tau)) / log2(N+1) = 1.15*(1+ln(2))/log2(82)
         = 1.15*1.693147/6.35755           = 0.306267
  fire  = poly_c >= 0.500                  = False
  dV    = 0.08 * (1 + poly_c)              = 0.08*1.306267 = 0.104501
  V_new = V_prev + dV                      = 3.834977 + 0.104501 = 3.939478
"""

import math

# ── Constants ──────────────────────────────────────────────────────────────────
ROUND        = 129
N            = 81
N_STR        = "81=3\u2074"
TAU          = 2
OMEGA_K      = 1
GAMMA        = 0.08
ADM          = 1.0
FIRE_THRESH  = 0.500
V_GLOBAL_PREV = 3.834977
CEILING_TICK_PREV = 46

# ── Compute ────────────────────────────────────────────────────────────────────
TOPO_BONUS  = 1 + 0.15 * OMEGA_K
POLY_C      = TOPO_BONUS * (1 + math.log(TAU)) / math.log2(N + 1)
FIRE        = POLY_C >= FIRE_THRESH
DELTA_V     = GAMMA * ADM * (1 + POLY_C)
V_GLOBAL    = V_GLOBAL_PREV + DELTA_V
CEILING_TICK = CEILING_TICK_PREV + 1

# ── Assertions ─────────────────────────────────────────────────────────────────
assert abs(TOPO_BONUS - 1.15) < 1e-9,       f"topo mismatch: {TOPO_BONUS}"
assert abs(POLY_C - 0.306267) < 1e-4,       f"poly_c mismatch: {POLY_C:.6f}"
assert FIRE is False,                        "fire should be False"
assert abs(DELTA_V - 0.104501) < 1e-5,      f"delta_V mismatch: {DELTA_V:.6f}"
assert abs(V_GLOBAL - 3.939478) < 1e-4,     f"V_global mismatch: {V_GLOBAL:.6f}"
assert CEILING_TICK == 47,                   f"ceiling_tick mismatch: {CEILING_TICK}"

# ── Report ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"R{ROUND} | N={N_STR} | tau={TAU} | omega_k={OMEGA_K}")
    print(f"topo={TOPO_BONUS:.4f} poly_c={POLY_C:.6f} fire={FIRE}")
    print(f"dV={DELTA_V:.6f} V_global={V_GLOBAL:.6f} CEILING\u00d7{CEILING_TICK}")
    print("TRUTH_PLANE: CANONICAL")
