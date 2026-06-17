"""
EVEZ-OS Spine — R172
N=124=2^2x31 | tau=6 | omega_k=2 | topo=1.3
poly_c=0.5199 | FIRE #27 | delta_V=0.041592
V_global=5.695849 | CEILING×90 | truth_plane=CANONICAL
Probe: d424015c-6dab-44e2-a244-50094c7a1255 | probe_delta=0.000258 (PASS)
Generated: 2026-02-24T11:38:41.586745+00:00
"""

# CANONICAL VALUES
ROUND       = 172
N           = 124
N_STR       = "2^2x31"
TAU         = 6
OMEGA_K     = 2
TOPO        = 1.3
POLY_C      = 0.5199
FIRE        = True
FIRE_NUMBER = 27
DELTA_V     = 0.041592
V_GLOBAL    = 5.695849
CEILING     = 90
TRUTH_PLANE = "CANONICAL"

def watch_composite_124(V_prev: float) -> dict:
    """R172: N=124=2^2x31 — FIRE #27"""
    import math
    topo   = 1.0 + 0.15 * 2
    poly_c = topo * (1 + math.log(6)) / math.log2(124 + 2)
    fire   = poly_c >= 0.500
    dv     = 0.08 * poly_c
    return {
        "N": 124, "N_str": "2^2x31", "tau": 6, "omega_k": 2,
        "topo": topo, "poly_c": round(poly_c, 6), "fire": fire,
        "fire_number": 27 if fire else None,
        "delta_V": round(dv, 6),
        "V_global": round(V_prev + dv, 6),
        "ceiling_tick": 90, "truth_plane": "CANONICAL"
    }

if __name__ == "__main__":
    result = watch_composite_124(5.654257)
    print(result)
