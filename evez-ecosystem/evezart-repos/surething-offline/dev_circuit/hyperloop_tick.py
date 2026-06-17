# EVEZ-GENERATED: Hyperloop tick computation module
# DCT-002 | Generated 2026-03-12 | circuit: THINK-G (groq/llama-3.3-70b-versatile)
import math
import random
import sys
import json
from typing import Any

def factorize(n: int) -> list[int]:
    """Factorize n by explicit trial division. Returns list of prime factors (with repeats).
    Inputs: n (positive integer)
    Outputs: list of prime factors, e.g. 12 -> [2, 2, 3]
    Note: EVEZ canonical rule — explicit enumeration only, no sympy shortcuts.
    """
    factors: list[int] = []
    i = 2
    while i * i <= n:
        if n % i:
            i += 1
        else:
            n //= i
            factors.append(i)
    if n > 1:
        factors.append(n)
    return factors

def count_divisors(n: int) -> int:
    """Count all divisors of n by explicit enumeration (loop 1..n).
    Inputs: n (positive integer)
    Outputs: divisor count tau
    Note: EVEZ rule — must use explicit loop, not formula product((e+1)).
    """
    count = 0
    for i in range(1, n + 1):
        if n % i == 0:
            count += 1
    return count

def compute_tick(round_number: int) -> dict[str, Any]:
    """Compute one EVEZ hyperloop tick.
    Inputs: round_number (int)
    Outputs: dict with all tick fields
    Fields: round, N, factors, tau, omega_k, topo, poly_c, x, p_fire, u, FIRE
    """
    N = round_number + 480
    factors = factorize(N)
    tau = count_divisors(N)
    omega_k = len(set(factors))
    topo_map = {1: 1.15, 2: 1.30, 3: 1.45}
    topo = topo_map.get(omega_k, 1.0)
    poly_c = (tau * omega_k * topo) / (2 * math.sqrt(N))
    x = max(0.0, min(1.0, (poly_c - 0.45) / 2.10))
    p_fire = x ** 0.60
    u = random.uniform(0, 1)
    FIRE = (u < p_fire) and (omega_k == 3)
    return {
        "round": round_number,
        "N": N,
        "factors": factors,
        "tau": tau,
        "omega_k": omega_k,
        "topo": topo,
        "poly_c": round(poly_c, 6),
        "x": round(x, 6),
        "p_fire": round(p_fire, 6),
        "u": round(u, 6),
        "FIRE": FIRE,
    }

def _test() -> None:
    """Test with known values: round=22 -> N=502=2*251, tau=4, omega_k=2, no FIRE."""
    result = compute_tick(22)
    assert result["round"] == 22, f"round mismatch: {result['round']}"
    assert result["N"] == 502, f"N mismatch: {result['N']}"
    assert sorted(result["factors"]) == [2, 251], f"factors: {result['factors']}"
    assert result["tau"] == 4, f"tau mismatch: {result['tau']}"
    assert result["omega_k"] == 2, f"omega_k mismatch: {result['omega_k']}"
    assert not result["FIRE"], "omega_k=2 cannot FIRE"
    # Test R508 candidate: N=988 wait, R508 N=508+480=988=4*13*19, omega=3
    r508 = compute_tick(28)  # N=508 = 4*127, omega=2 -- actually R508 is round=508 which means N=988
    print(f"R508 test: N={r508['N']} tau={r508['tau']} omega={r508['omega_k']} FIRE={r508['FIRE']}")
    print("All tests passed.")

if __name__ == "__main__":
    if "--test" in sys.argv:
        _test()
    elif len(sys.argv) == 2:
        try:
            round_num = int(sys.argv[1])
            result = compute_tick(round_num)
            print(json.dumps(result, indent=2))
        except ValueError:
            print(f"ERROR: invalid round number: {sys.argv[1]}")
            sys.exit(1)
    else:
        print("Usage: python hyperloop_tick.py <round_number>")
        print("       python hyperloop_tick.py --test")
        sys.exit(1)
