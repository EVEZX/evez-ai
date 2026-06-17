#!/usr/bin/env python3
"""spine/watch_composite_70.py
R118: COMPOSITE NEAR MISS -- N=70=2x5x7 tau=3
EVEZ-OS Three-prime composite. poly_c=0.4949 -- BELOW threshold by 0.005.
truth_plane: CANONICAL
"""
import math

ROUND = 118
N_NEW = 70
TAU_N = 3
GAMMA = 0.08
ADM = 1.0
V_GLOBAL_PREV = 2.668042
V_V2 = 3.68932
CEILING_TICK_PREV = 35

R119_GAP = 'R119: prime_block_watch_4.py. N=71=PRIME tau=1. PRIME BLOCK 4.'


def omega_k(n):
    f = set()
    d = 2
    t = n
    while d * d <= t:
        if t % d == 0:
            f.add(d)
            while t % d == 0:
                t //= d
        d += 1
    if t > 1:
        f.add(t)
    return len(f)


topo_bonus = 1.0 + 0.15 * omega_k(N_NEW)
poly_c = topo_bonus * (1.0 + math.log(TAU_N)) / math.log2(N_NEW + 1)
fire_ignited = poly_c >= 0.500
delta_V = GAMMA * ADM * (1.0 + poly_c)
V_GLOBAL_NEW = V_GLOBAL_PREV + delta_V
ceiling_tick = CEILING_TICK_PREV + 1
miss_margin = poly_c - 0.500

OMEGA = (
    'COMPOSITE NEAR MISS. R118. N=70=2x5x7 tau=3 '
    'poly_c={:.6f} BELOW threshold by {:.6f}. NO FIRE. '
    'topo_bonus={:.4f}. V_global={:.6f} CEILING x{}. '
    'Next: N=71=PRIME -- PRIME BLOCK 4.'
).format(poly_c, abs(miss_margin), topo_bonus, V_GLOBAL_NEW, ceiling_tick)

result = {
    'round': ROUND,
    'N_new': N_NEW,
    'tau_N': TAU_N,
    'topo_bonus': topo_bonus,
    'poly_c': poly_c,
    'threshold': 0.500,
    'miss_margin': miss_margin,
    'fire_ignited': fire_ignited,
    'attractor_lock': 0.0,
    'fire_res': 0.0,
    'delta_V': delta_V,
    'V_global_prev': V_GLOBAL_PREV,
    'V_global_new': V_GLOBAL_NEW,
    'ceiling_tick': ceiling_tick,
    'omega': OMEGA,
    'truth_plane': 'CANONICAL',
    'R119_GAP': R119_GAP,
}

if __name__ == '__main__':
    import json
    print(json.dumps(result, indent=2))
    assert not fire_ignited, 'FIRE not expected at N=70 tau=3 (poly_c<0.500)'
    assert abs(miss_margin) < 0.01, 'near miss margin check'
    assert abs(V_GLOBAL_NEW - 2.787637) < 0.001
    print('VERIFIED: R118 CANONICAL poly_c={:.6f} miss={:.6f} V_global={:.6f}'.format(
        poly_c, miss_margin, V_GLOBAL_NEW))
