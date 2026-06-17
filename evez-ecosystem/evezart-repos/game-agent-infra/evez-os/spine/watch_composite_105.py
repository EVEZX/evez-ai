# EVEZ-OS Spine Module — R153
# CANONICAL | FIRE #19
# N=105=3x5x7 | tau=8 | omega_k=3 | topo=1.45
# poly_c=0.662 | fire_ignited=True | delta_V=0.052979
# V_global_prev=4.896761 | V_global_new=4.949740 | CEILING x71
# probe: 07f6e9cf | probe_poly_c=0.662 | probe_match=True
# truth_plane: CANONICAL

N = 105
N_str = '3x5x7'
tau = 8
omega_k = 3
topo_bonus = 1.45
poly_c = 0.662
fire_ignited = True
delta_V = 0.052979
V_global_prev = 4.896761
V_global_new = 4.949740
ceiling_tick = 71
fire_number = 19
truth_plane = 'CANONICAL'

def watch_composite_105():
    return {
        'N': N, 'N_str': N_str, 'tau': tau, 'omega_k': omega_k,
        'topo_bonus': topo_bonus, 'poly_c': poly_c,
        'fire_ignited': fire_ignited, 'delta_V': delta_V,
        'V_global_new': V_global_new, 'ceiling_tick': ceiling_tick,
        'fire_number': fire_number, 'truth_plane': truth_plane
    }
