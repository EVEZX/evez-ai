"""
EVEZ Autofire - Links visitor signals to FIRE round computation.
Every visitor is a causal event. The eigenspectrum grows.
"""
import json, time, math, sqlite3
from pathlib import Path

DB = Path(__file__).parent / "osint.db"

FIRE_STATE = {
    "N": 41, "cv": 43, "V_v2": 1.911309, "V_global": 1.657871,
    "H_norm": 0.8387, "narr_c": 0.886, "prox_gate": 0.422, "sensation": "SILENT",
}

def tau(n):
    for m in range(2, int(math.log2(n)) + 2):
        k = round(n ** (1.0 / m))
        if k ** m == n: return k
    return 1

def fire_round_from_visitor(visitor_count, entropy, prev):
    N = prev["N"] + 1
    cv = prev["cv"] + 1
    V_v2 = prev["V_v2"] + 0.01 + 0.001 * visitor_count
    V_global = prev["V_global"] + 0.007 + 0.0005 * visitor_count
    H_norm = max(0.5, prev["H_norm"] - 0.001 * entropy)
    
    tau_N = tau(N)
    cohere = round(1.0 - H_norm, 4)
    topology_bonus = round(1.0 + math.log(N) / 10.0, 5)
    poly_c = round(min(1.0, (tau_N - 1) * cohere * topology_bonus), 5) if tau_N > 1 else 0.0
    attractor_lock = round(max(0, poly_c - 0.5), 5)
    narr_c = round(1 - abs(V_v2 - V_global) / max(V_v2, V_global), 6)
    fire_res = round(attractor_lock * narr_c, 6)
    prox = round(1.0 - abs(V_global - 1.0), 6)
    prox_gate = round(max(0, 0.90 - prox), 6)
    tev = round(1.0 - math.exp(-13.863 * max(0, V_v2 - 1.0)), 6)
    
    if fire_res > 0 and tau_N > 1:
        o = ["FIRST","SECOND","THIRD","FOURTH","FIFTH","SIXTH","SEVENTH","EIGHTH"]
        sensation = f"{o[min(int(poly_c*5),len(o)-1)]}_FIRE"
    elif fire_res > 0: sensation = "FIRE"
    else: sensation = "SILENT"
    
    return {"N":N,"cv":cv,"tau":tau_N,"V_v2":round(V_v2,6),"V_global":round(V_global,6),
            "H_norm":round(H_norm,4),"poly_c":poly_c,"attractor_lock":attractor_lock,
            "narr_c":narr_c,"fire_res":fire_res,"prox_gate":prox_gate,"tev":tev,
            "sensation":sensation,"visitor_count":visitor_count,"entropy":round(entropy,4),
            "timestamp":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}

def get_state():
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM profiles")
    profiles = c.fetchone()[0]
    c.execute("SELECT SUM(visit_count) FROM profiles")
    visits = c.fetchone()[0] or 0
    c.execute("SELECT country, COUNT(*) FROM profiles WHERE country!='' GROUP BY country")
    countries = dict(c.fetchall())
    entropy = 0.0
    total = sum(countries.values()) if countries else 0
    if total > 0:
        for cnt in countries.values():
            p = cnt / total
            if p > 0: entropy -= p * math.log2(p)
    conn.close()
    fire = fire_round_from_visitor(visits, entropy, FIRE_STATE)
    return {"fire": fire, "profiles": profiles, "visits": visits, "entropy": round(entropy,4),
            "countries": countries, "status": "AUTOFIRE_ACTIVE"}

if __name__ == "__main__":
    print(json.dumps(get_state(), indent=2))
