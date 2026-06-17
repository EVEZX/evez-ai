"""EVEZ-OS R131 — prime_block_watch_7.py
CANONICAL ROUND 131 — PRIME BLOCK 7

N=83=PRIME
tau=1 (prime: only divisors are 1 and 83)
omega_k=1 (distinct prime factors: {83})
topo_bonus=1.15 (1 + 0.15*omega_k)
poly_c=0.179904 (topo*(1+ln(tau))/log2(N+1) = 1.15*(1+0)/log2(84))
fire_ignited=False (poly_c=0.179904 < 0.500)
delta_V=0.094392 (0.08*(1+poly_c))
V_global_prev=4.047097
V_global_new=4.141489
ceiling_tick=49
truth_plane=CANONICAL

Note: N=83 is prime → tau=1 → ln(1)=0 → PRIME BLOCK 7 minimum energy.
V_global crossed 4.0 for first time at R130. Climbing.
"""

import math

GAMMA = 0.08
ADM   = 1.0
THRESH = 0.500


def factorize(n):
    """Return prime factorization as dict {prime: exp}"""
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def tau_N(n):
    """Number of divisors"""
    t = 1
    for e in factorize(n).values():
        t *= (e + 1)
    return t


def omega_k(n):
    """Number of distinct prime factors"""
    return len(factorize(n))


def topo_bonus(n):
    return 1.0 + 0.15 * omega_k(n)


def poly_c(n):
    t = tau_N(n)
    if t <= 1:
        return 0.0
    return topo_bonus(n) * (1.0 + math.log(t)) / math.log2(n + 1)


def compute_r131():
    N = 83
    tau = tau_N(N)      # 1 (prime)
    ok  = omega_k(N)    # 1
    topo = topo_bonus(N) # 1.15
    pc   = poly_c(N)    # 0.179904
    fire = pc >= THRESH  # False
    delta_V = GAMMA * ADM * (1.0 + pc)  # 0.094392
    V_prev  = 4.047097
    V_new   = V_prev + delta_V           # 4.141489
    ceiling_tick = 49

    result = {
        "round":         131,
        "N":             N,
        "N_str":         "83=PRIME",
        "tau":           tau,
        "omega_k":       ok,
        "topo_bonus":    topo,
        "poly_c":        round(pc, 6),
        "fire_ignited":  fire,
        "delta_V":       round(delta_V, 6),
        "V_global_prev": V_prev,
        "V_global_new":  round(V_new, 6),
        "ceiling_tick":  ceiling_tick,
        "truth_plane":   "CANONICAL",
    }
    return result


# ── Assertions ────────────────────────────────────────────────────────────────

def _assert_r131():
    r = compute_r131()
    assert r["tau"] == 1,          f"tau expected 1, got {r['tau']}"
    assert r["omega_k"] == 1,      f"omega_k expected 1, got {r['omega_k']}"
    assert abs(r["topo_bonus"] - 1.15) < 1e-9
    assert abs(r["poly_c"] - 0.179904) < 1e-4, f"poly_c {r['poly_c']}"
    assert r["fire_ignited"] is False
    assert abs(r["delta_V"] - 0.094392) < 1e-4, f"delta_V {r['delta_V']}"
    assert abs(r["V_global_new"] - 4.141489) < 1e-4, f"V_new {r['V_global_new']}"
    assert r["ceiling_tick"] == 49
    print("R131 assertions PASSED")
    return r


if __name__ == "__main__":
    r = _assert_r131()
    import json
    print(json.dumps(r, indent=2))
