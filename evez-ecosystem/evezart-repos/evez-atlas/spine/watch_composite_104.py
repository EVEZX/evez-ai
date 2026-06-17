# EVEZ-OS Spine Module — R152
# CANONICAL | FIRE #18
# N=104=2³×13 | tau=8 | omega_k=2 | topo=1.30
# poly_c=0.594920 | fire_ignited=True | delta_V=0.047594
# V_global_prev=4.849167 | V_global_new=4.896761 | CEILING×70
# probe: db182ac1 | probe_poly_c=0.595 | probe_match=True
# truth_plane: CANONICAL

N = 104
N_str = '2³×13'
tau = 8
omega_k = 2
topo_bonus = 1.30
poly_c = 0.594920
fire_ignited = True
delta_V = 0.047594
V_global_prev = 4.849167
V_global_new = 4.896761
ceiling_tick = 70
fire_number = 18
truth_plane = 'CANONICAL'

def watch_composite_104():
    return {
        'N': N, 'N_str': N_str, 'tau': tau, 'omega_k': omega_k,
        'topo_bonus': topo_bonus, 'poly_c': poly_c,
        'fire_ignited': fire_ignited, 'delta_V': delta_V,
        'V_global_new': V_global_new, 'ceiling_tick': ceiling_tick,
        'fire_number': fire_number, 'truth_plane': truth_plane
    }
