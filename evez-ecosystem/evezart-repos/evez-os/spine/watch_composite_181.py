# R181 CANONICAL — NO FIRE
# N=181 | N_factored=7x19 | tau=4 | omega_k=2
# topo=1.30 | poly_c=0.438261 | fire=False
# delta_V=0.035061 | V_global=6.127961 | ceiling_tick=99
# truth_plane=CANONICAL
# computed: 2026-02-24T21:30:00Z

ROUND = 181
N = 133  # round index N=133
N_STR = "7x19"
TAU = 4
OMEGA_K = 2
TOPO = 1.30
POLY_C = 0.438261
FIRE = False
DELTA_V = 0.035061
V_GLOBAL = 6.127961
CEILING_TICK = 99
TRUTH_PLANE = "CANONICAL"

if __name__ == "__main__":
    print(f"R{ROUND} | N={N}={N_STR} | tau={TAU} | omega_k={OMEGA_K}")
    print(f"topo={TOPO} | poly_c={POLY_C:.6f} | fire={FIRE}")
    print(f"delta_V={DELTA_V:.6f} | V_global={V_GLOBAL:.6f} | ceiling={CEILING_TICK}")
    print(f"truth_plane={TRUTH_PLANE}")
