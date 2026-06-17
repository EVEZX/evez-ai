# EVEZ-OS Spine Module — R154
# CANONICAL | NO FIRE
# N=106=2x53 | tau=4 | omega_k=2 | topo=1.30
# poly_c=0.459074 | fire_ignited=False | delta_V=0.036726
# V_global_prev=4.949740 | V_global_new=4.986466 | CEILINGx72
# probe: d5a18dfd | truth_plane: CANONICAL

N = 106
N_str = '2x53'
tau = 4
omega_k = 2
topo_bonus = 1.30
poly_c = 0.459074
fire_ignited = False
delta_V = 0.036726
V_global_prev = 4.949740
V_global_new = 4.986466
ceiling_tick = 72
fire_number = None
truth_plane = 'CANONICAL'

def watch_composite_106():
    return {
        'N': N, 'N_str': N_str, 'tau': tau, 'omega_k': omega_k,
        'topo_bonus': topo_bonus, 'poly_c': poly_c,
        'fire_ignited': fire_ignited, 'delta_V': delta_V,
        'V_global_new': V_global_new, 'ceiling_tick': ceiling_tick,
        'fire_number': fire_number, 'truth_plane': truth_plane
    }
