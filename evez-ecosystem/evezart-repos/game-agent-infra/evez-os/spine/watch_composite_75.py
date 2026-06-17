#!/usr/bin/env python3
"""
EVEZ-OS Spine Module: watch_composite_75.py
Round: R123 | N=75=3×5² | tau=3 | omega_k=2 | topo=1.30
poly_c: 0.436656 | fire: False | V_global: 3.176001 -> 3.290933
ceiling_tick: 41 | truth_plane: CANONICAL
"""
import json, math, sys

ROUND=123; N=75; TAU=3; GAMMA=0.08; ADM=1.0

def omega_k(n):
    count=0; d=2; x=n
    while d*d<=x:
        if x%d==0:
            count+=1
            while x%d==0: x//=d
        d+=1
    if x>1: count+=1
    return count

def compute():
    ok=omega_k(N)
    topo=round(1+0.15*ok, 6)
    poly_c=round(topo*(1+math.log(TAU))/math.log2(N+1), 6)
    V_prev=3.176001
    delta_V=round(GAMMA*ADM*(1+poly_c), 6)
    V_new=round(V_prev+delta_V, 6)
    return {
        "round": ROUND, "N": N, "N_str": "75=3×5²", "tau": TAU,
        "omega_k": ok, "topo_bonus": topo,
        "poly_c": poly_c, "fire_ignited": False,
        "fire_name": "", "attractor_lock": 0.0, "fire_res": 0.0,
        "delta_V": delta_V, "V_global_prev": V_prev,
        "V_global_new": V_new, "ceiling_tick": 41,
        "milestone": "COMPOSITE_WATCH",
        "truth_plane": "CANONICAL",
        "omega": (
            f"R{ROUND} N=75=3×5² tau=3 poly_c={poly_c:.6f} NO FIRE. "
            f"V_global={V_new:.6f} CEILING x41. "
            f"Next: N=76=2²×19 tau=3 topo=1.30. Watch N=84 THIRTEENTH FIRE candidate."
        )
    }

if __name__=="__main__":
    r=compute()
    print(json.dumps(r, indent=2))
    assert r["V_global_new"]==3.290933, f"V mismatch {r['V_global_new']}"
    assert r["poly_c"]==0.436656, f"poly_c mismatch {r['poly_c']}"
    assert r["fire_ignited"]==False
    assert r["ceiling_tick"]==41
    print("R123 CANONICAL. COMPOSITE WATCH. EXIT 0.", file=sys.stderr)
    sys.exit(0)
