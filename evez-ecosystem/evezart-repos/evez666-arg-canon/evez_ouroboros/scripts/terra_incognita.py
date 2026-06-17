"""
terra_incognita.py — EVEZ666 ARG Terra Incognita Realm
Unlocked by EXTREME_FIRE events (tau >= 20).
"You will not find it by thinking." — @EVEZ666
"""
import hashlib, json, pathlib, time
from datetime import datetime, timezone
from typing import Optional

REALM_NAME = "TERRA_INCOGNITA"
REALM_UNLOCK_TAU = 20.0
STATE_FILE = pathlib.Path(__file__).parent.parent.parent / "arg_state.json"

def prime_factors(n: int) -> list:
    factors = set()
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.add(d)
            n //= d
        d += 1
    if n > 1:
        factors.add(n)
    return sorted(factors)

def generate_puzzle(spine_hash: str, round_num: int, tau: float) -> dict:
    N = round_num + 80
    omega = len(prime_factors(N))
    lock = hashlib.sha256(f"{spine_hash}{round_num}EVEZ_PUZZLE".encode()).hexdigest()
    solution = hashlib.sha256(f"{tau}:{N}:{omega}:{spine_hash[:8]}".encode()).hexdigest()
    return {
        "realm": REALM_NAME, "round": round_num, "N": N, "tau": tau,
        "omega": omega, "prime_factors": prime_factors(N),
        "lock": lock, "lock_prefix": lock[:8], "solution": solution,
        "hint": f"N={N}. Count the distinct prime factors. The topology knows.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

def activate_realm(fire_event: dict) -> Optional[dict]:
    tau = fire_event.get("tau", 0)
    if tau < REALM_UNLOCK_TAU:
        return None
    round_num = fire_event.get("round", 460)
    spine_hash = fire_event.get("spine_hash", "a" * 64)
    puzzle = generate_puzzle(spine_hash, round_num, tau)
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    state.setdefault("realms", {})[REALM_NAME] = {
        "active": True, "activated_at": datetime.now(timezone.utc).isoformat(),
        "fire_event": fire_event, "puzzle": puzzle, "solvers": [],
    }
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"[TerraIncognita] REALM ACTIVATED tau={tau} lock={puzzle['lock_prefix']}...")
    return state["realms"][REALM_NAME]

if __name__ == "__main__":
    mock = {"round": 460, "tau": 23.7, "v_value": 0.891, "spine_hash": "a"*64}
    result = activate_realm(mock)
    if result:
        print(json.dumps(result["puzzle"], indent=2))
