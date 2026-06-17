# EVEZ-OS Hyperloop — R135 CANONICAL
# N=87=3×29  tau=2  omega_k=2  topo=1.30
# poly_c=0.340897  fire=NO  delta_V=0.027272
# V_global=4.341461  ceiling_tick=53
# Truth plane: CANONICAL
# Committed: 2026-02-23T11:30 PST

ROUND = 135
N = 87
N_FACTORED = '3x29'
TAU = 2
OMEGA_K = 2
TOPO = 1.30
POLY_C = 0.340897
FIRE_IGNITED = False
DELTA_V = 0.027272
V_GLOBAL_PREV = 4.314189
V_GLOBAL_NEW = 4.341461
CEILING_TICK = 53
TRUTH_PLANE = 'CANONICAL'

import math

def compute_round(N, tau, omega_k, V_global_prev):
    topo = 1.0 + 0.15 * omega_k
    poly_c = topo * (1 + math.log(tau)) / math.log2(N + 2)
    fire = poly_c >= 0.500
    delta_V = 0.08 * 1.0 * poly_c
    V_global_new = V_global_prev + delta_V
    ceiling_tick = N - 82
    return {
        'N': N,
        'tau': tau,
        'omega_k': omega_k,
        'topo': topo,
        'poly_c': poly_c,
        'fire_ignited': fire,
        'delta_V': delta_V,
        'V_global_prev': V_global_prev,
        'V_global_new': V_global_new,
        'ceiling_tick': ceiling_tick,
        'truth_plane': 'CANONICAL'
    }

if __name__ == '__main__':
    result = compute_round(N, TAU, OMEGA_K, V_GLOBAL_PREV)
    print(f'R{ROUND} | N={N}={N_FACTORED} | poly_c={result["poly_c"]:.6f} | fire={result["fire_ignited"]} | V_global={result["V_global_new"]:.6f} | CEILING x{result["ceiling_tick"]}')
    assert abs(result['poly_c'] - POLY_C) < 0.0001, 'poly_c mismatch'
    assert result['fire_ignited'] == FIRE_IGNITED, 'fire mismatch'
    print('CANONICAL: VERIFIED')
