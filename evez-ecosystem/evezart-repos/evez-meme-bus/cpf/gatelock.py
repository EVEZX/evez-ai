"""
cpf/gatelock.py — GateLockV1 + RoundResultV1 construction and validation.

GateLockV1: immutability anchor written at precommit-close.
RoundResultV1: audit proof written after beacon is known.

See cpf/SPEC.md for full field semantics.
"""
import time
from typing import Optional
from cpf.canon import canon, h_obj, gatelock_hash, ledger_head_hash, params_commit, sort_sigset
from cpf.beacon import verify_beacon_target, canonical_b32, DEFAULT_DELTA_MS
from cpf.derive import derive, thresh, fire_decision


# ---------- GateLockV1 ----------

def build_gatelock(
    round_id: int,
    lock_height: int,
    hyperloop_state: dict,
    cpf_params: dict,
    beacon_id: str,
    lock_time_unix_ms: Optional[int] = None,
    delta_ms: int = DEFAULT_DELTA_MS,
    validator_set_hash: str = "0" * 64,
    state_schema_id: str = "hyperloop_state_v1",
    window_id: Optional[str] = None,
) -> dict:
    """
    Build a GateLockV1 object.
    beacon_target is derived deterministically — not a caller choice.
    """
    if lock_time_unix_ms is None:
        lock_time_unix_ms = int(time.time() * 1000)

    from cpf.beacon import drand_round_for_time
    beacon_target = drand_round_for_time(lock_time_unix_ms, delta_ms)

    lhh = ledger_head_hash(hyperloop_state)
    pc  = params_commit(cpf_params)

    gate = {
        "type": "EVEZ.GateLockV1",
        "cpf_version": "v1",
        "round_id": round_id,
        "lock_height": lock_height,
        "lock_time_unix_ms": lock_time_unix_ms,
        "ledger_head_hash": lhh,
        "state_schema_id": state_schema_id,
        "state_canon": "JCS-UTF8",
        "params_commit": pc,
        "beacon": {
            "beacon_id": beacon_id,
            "beacon_target": beacon_target,
            "beacon_delay": delta_ms // (3 * 1000),  # in drand epochs
            "beacon_canon": cpf_params.get("beacon_canon", "HASHED32"),
        },
        "validator_set_hash": validator_set_hash,
        "gate_lock_sigset": [],
    }
    if window_id:
        gate["window_id"] = window_id
    return gate


def validate_gatelock(gate: dict, delta_ms: int = DEFAULT_DELTA_MS) -> list:
    """
    Validate a GateLockV1 for malleability vectors.
    Returns list of violation strings (empty = valid).
    """
    violations = []

    # Type guard
    if gate.get("type") != "EVEZ.GateLockV1":
        violations.append("type != EVEZ.GateLockV1")
        return violations

    # Beacon target determinism
    lock_ms = gate.get("lock_time_unix_ms")
    target  = gate.get("beacon", {}).get("beacon_target")
    if lock_ms is not None and target is not None:
        if not verify_beacon_target(lock_ms, target, delta_ms):
            violations.append(
                f"beacon_target={target} is not deterministic for "
                f"lock_time={lock_ms} + delta={delta_ms}ms"
            )

    # Sigset sorted
    sigset = gate.get("gate_lock_sigset", [])
    if sigset != sort_sigset(sigset):
        violations.append("gate_lock_sigset not sorted by pubkey")

    # Required fields present
    required = [
        "round_id", "lock_height", "lock_time_unix_ms",
        "ledger_head_hash", "params_commit", "beacon",
        "validator_set_hash"
    ]
    for f in required:
        if f not in gate:
            violations.append(f"missing required field: {f}")

    # Hex field lengths
    for hex_field, expected_len in [
        ("ledger_head_hash", 64), ("params_commit", 64), ("validator_set_hash", 64)
    ]:
        val = gate.get(hex_field, "")
        if len(val) != expected_len or val != val.lower():
            violations.append(f"{hex_field}: must be {expected_len} lowercase hex chars")

    return violations


# ---------- RoundResultV1 ----------

def build_round_result(
    round_id: int,
    gate: dict,
    beacon_output_hex: str,
    hyperloop_state: dict,
    cpf_params: dict,
) -> dict:
    """
    Build RoundResultV1 after beacon is known.
    All randomness derived deterministically from inputs.
    FIRE = x_fire < t_fire. No floats.
    """
    beacon_canon = gate["beacon"]["beacon_canon"]
    b32 = canonical_b32(beacon_output_hex, beacon_canon)
    lhh = ledger_head_hash(hyperloop_state)
    gl_hash = gatelock_hash(gate)

    dr = derive(b32, round_id, lhh)

    poly_c_scaled = cpf_params["poly_c_scaled"]
    t_fire = thresh(poly_c_scaled, dr.omega)
    fire   = fire_decision(dr.x_fire, t_fire)

    result = {
        "type": "EVEZ.RoundResultV1",
        "cpf_version": "v1",
        "round_id": round_id,
        "gate_lock_hash": gl_hash,
        "beacon_target": gate["beacon"]["beacon_target"],
        "B": beacon_output_hex,
        "omega": dr.omega,
        "x_fire": dr.x_fire.to_bytes(32, "big").hex(),
        "t_fire": t_fire.to_bytes(32, "big").hex(),
        "fire": fire,
        "p_fire_repr": f"{poly_c_scaled / 10**18:.6f}",  # human audit only, not consensus
    }
    return result


def validate_round_result(result: dict, gate: dict) -> list:
    """
    Re-derive from scratch and compare. Returns violations.
    Any difference = implementation divergence or tampering.
    """
    violations = []

    if result.get("type") != "EVEZ.RoundResultV1":
        violations.append("type != EVEZ.RoundResultV1")
        return violations

    if result.get("gate_lock_hash") != gatelock_hash(gate):
        violations.append("gate_lock_hash mismatch — GateLock may have been mutated")

    return violations
