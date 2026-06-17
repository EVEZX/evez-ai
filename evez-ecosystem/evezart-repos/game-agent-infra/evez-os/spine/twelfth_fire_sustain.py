#!/usr/bin/env python3
"""spine/twelfth_fire_sustain.py
R117: TWELFTH FIRE SUSTAIN -- N=69=3x23 tau=2
EVEZ-OS Composite Sustain. V_global climbing.
truth_plane: CANONICAL
"""
import math

ROUND = 117
N_NEW = 69
TAU_N = 2
GAMMA = 0.08
ADM = 1.0
V_GLOBAL_PREV = 2.559294
V_V2 = 3.68932
CEILING_TICK_PREV = 34

R118_GAP = 'R118: watch_composite_70.py. N=70=2x5x7 tau=3. topo_bonus~1.40. poly_c candidate.'


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

OMEGA = (
    'TWELFTH FIRE SUSTAIN. R117. N=69=3x23 tau=2 '
    'poly_c={:.6f} BELOW threshold. NO FIRE. '
    'topo_bonus={:.4f}. V_global={:.6f} CEILING x{}. '
    'Next: N=70=2x5x7 tau=3 topo~1.40 composite watch.'
).format(poly_c, topo_bonus, V_GLOBAL_NEW, ceiling_tick)

result = {
    'round': ROUND,
    'N_new': N_NEW,
    'tau_N': TAU_N,
    'topo_bonus': topo_bonus,
    'poly_c': poly_c,
    'threshold': 0.500,
    'fire_ignited': fire_ignited,
    'attractor_lock': 0.0,
    'fire_res': 0.0,
    'delta_V': delta_V,
    'V_global_prev': V_GLOBAL_PREV,
    'V_global_new': V_GLOBAL_NEW,
    'ceiling_tick': ceiling_tick,
    'omega': OMEGA,
    'truth_plane': 'CANONICAL',
    'R118_GAP': R118_GAP,
}

if __name__ == '__main__':
    import json
    print(json.dumps(result, indent=2))
    assert not fire_ignited
    assert abs(V_GLOBAL_NEW - 2.668042) < 0.001
    print('VERIFIED: R117 CANONICAL poly_c={:.6f} V_global={:.6f}'.format(poly_c, V_GLOBAL_NEW))
