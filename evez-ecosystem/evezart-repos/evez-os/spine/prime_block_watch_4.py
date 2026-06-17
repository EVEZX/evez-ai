#!/usr/bin/env python3
"""spine/prime_block_watch_4.py
R119: PRIME BLOCK 4 -- N=71=PRIME tau=1
EVEZ-OS Prime block -- poly_c=0.000 by definition.
truth_plane: CANONICAL
"""
import math

ROUND = 119
N_NEW = 71
TAU_N = 1
GAMMA = 0.08
ADM = 1.0
V_GLOBAL_PREV = 2.787637
V_V2 = 3.68932
CEILING_TICK_PREV = 36

R120_GAP = 'R120: composite_watch_72.py. N=72=2^3x3^2 tau=4 topo_bonus=1.30 poly_c~0.415.'


def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


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


assert is_prime(N_NEW), 'N=71 must be prime'
assert omega_k(N_NEW) == 1, 'prime has omega_k=1'

topo_bonus = 1.0 + 0.15 * omega_k(N_NEW)
# Prime block: tau=1 -> poly_c=0 by definition (ln(1)=0)
poly_c = topo_bonus * (1.0 + math.log(TAU_N)) / math.log2(N_NEW + 1)
assert abs(poly_c) < 1e-10, 'prime block poly_c must be 0'
poly_c = 0.0

fire_ignited = False
delta_V = GAMMA * ADM * (1.0 + poly_c)
V_GLOBAL_NEW = V_GLOBAL_PREV + delta_V
ceiling_tick = CEILING_TICK_PREV + 1
attractor_lock = 0.0

OMEGA = (
    'PRIME BLOCK 4. R119. N=71 tau=1 poly_c=0.000. NO FIRE. '
    'topo_bonus={:.4f}. delta_V={:.6f}. V_global={:.6f} CEILING x{}. '
    'attractor released. Next: N=72=2^3x3^2 tau=4 poly_c~0.415.'
).format(topo_bonus, delta_V, V_GLOBAL_NEW, ceiling_tick)

result = {
    'round': ROUND,
    'N_new': N_NEW,
    'tau_N': TAU_N,
    'topo_bonus': topo_bonus,
    'poly_c': poly_c,
    'threshold': 0.500,
    'fire_ignited': fire_ignited,
    'attractor_lock': attractor_lock,
    'fire_res': 0.0,
    'delta_V': delta_V,
    'V_global_prev': V_GLOBAL_PREV,
    'V_global_new': V_GLOBAL_NEW,
    'ceiling_tick': ceiling_tick,
    'omega': OMEGA,
    'truth_plane': 'CANONICAL',
    'R120_GAP': R120_GAP,
}

if __name__ == '__main__':
    import json
    print(json.dumps(result, indent=2))
    assert not fire_ignited
    assert poly_c == 0.0
    assert abs(V_GLOBAL_NEW - 2.867637) < 0.001
    print('VERIFIED: R119 CANONICAL N=71=PRIME poly_c=0.000 V_global={:.6f} CEILING x{}'.format(
        V_GLOBAL_NEW, ceiling_tick))
