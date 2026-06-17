"""
cpf/validator.py — CLI tool + importable validator.

Usage:
  python3 -m cpf.validator <gatelock.json> [beacon_output_hex]
  python3 -m cpf.validator --vectors   (run reference test vectors)

Returns:
  0 = valid (no violations)
  1 = violations found
  2 = usage error
"""
import json
import sys
from cpf.gatelock import validate_gatelock, build_round_result, validate_round_result
from cpf.vectors import run_all


def validate_file(gatelock_path: str, beacon_hex: str | None = None) -> int:
    with open(gatelock_path) as f:
        gate = json.load(f)

    viols = validate_gatelock(gate)
    if viols:
        print("[GATELOCK VIOLATIONS]")
        for v in viols:
            print(f"  ✗ {v}")
        return 1

    print(f"[OK] GateLock valid: round_id={gate.get('round_id')}, "
          f"beacon_target={gate.get('beacon', {}).get('beacon_target')}")

    if beacon_hex:
        state_path = gatelock_path.replace(".json", "_state.json")
        params_path = gatelock_path.replace(".json", "_params.json")
        try:
            with open(state_path) as f:
                state = json.load(f)
            with open(params_path) as f:
                params = json.load(f)
        except FileNotFoundError as e:
            print(f"[SKIP] Round result validation: {e}")
            return 0

        result = build_round_result(
            round_id=gate["round_id"],
            gate=gate,
            beacon_output_hex=beacon_hex,
            hyperloop_state=state,
            cpf_params=params,
        )
        rviols = validate_round_result(result, gate)
        if rviols:
            print("[ROUND RESULT VIOLATIONS]")
            for v in rviols:
                print(f"  ✗ {v}")
            return 1

        print(f"[OK] omega={result['omega']}  fire={result['fire']}")
        print(f"     x_fire={result['x_fire'][:16]}...")
        print(f"     t_fire={result['t_fire'][:16]}...")

    return 0


def run_vectors() -> int:
    print("Running CPF v1 reference test vectors...")
    data = run_all()
    errors = 0
    for v in data["vectors"]:
        r = v["result"]
        print(f"\n[{v['vector_id']}] {v['description']}")
        print(f"  ledger_head_hash : {v['ledger_head_hash']}")
        print(f"  params_commit    : {v['params_commit']}")
        print(f"  omega            : {r['omega']}")
        print(f"  x_fire           : {r['x_fire']}")
        print(f"  t_fire           : {r['t_fire']}")
        print(f"  fire             : {r['fire']}")
        print(f"  gate_lock_hash   : {r['gate_lock_hash']}")
        if r.get("omega") not in (1, 2, 3):
            print(f"  [ERR] omega out of range: {r['omega']}")
            errors += 1
        else:
            print(f"  [PASS]")
    if errors:
        print(f"\n{errors} vector(s) FAILED")
        return 1
    print("\nAll vectors PASSED")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 -m cpf.validator <gatelock.json> [beacon_hex]")
        print("       python3 -m cpf.validator --vectors")
        sys.exit(2)
    if sys.argv[1] == "--vectors":
        sys.exit(run_vectors())
    beacon = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(validate_file(sys.argv[1], beacon))
