"""
cpf/canon.py — Canonical JSON serialization for EVEZ CPF v1.

CANON(obj) contract:
  1. UTF-8 text
  2. Keys sorted lexicographically at every object level
  3. No insignificant whitespace
  4. Numbers: non-negative integers only; base-10, no leading zeros
     (except the literal "0"); range [0, 2^64-1]
  5. Byte strings: lowercase hex of fixed length, no 0x prefix
  6. Arrays: order defined by per-field rules (see canon_gatelock / canon_result)
  7. Strings: ASCII for IDs; unicode normalized to NFC before canon
Hashing:
  H_OBJ(domain, obj) = SHA-256(domain_bytes || 0x00 || CANON(obj))
"""
import json
import hashlib
import unicodedata
from typing import Any

# ---------- low-level canon helpers ----------

def _canon_value(v: Any) -> Any:
    """Recursively normalize a value for canonical serialization."""
    if isinstance(v, dict):
        return {k: _canon_value(val) for k, val in sorted(v.items())}
    if isinstance(v, list):
        return [_canon_value(i) for i in v]
    if isinstance(v, str):
        return unicodedata.normalize("NFC", v)
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        if v < 0 or v > (2**64 - 1):
            raise ValueError(f"Integer out of range [0, 2^64-1]: {v}")
        return v
    if isinstance(v, float):
        raise TypeError(f"Floats are forbidden in consensus objects. Got: {v}")
    return v


def canon(obj: dict) -> bytes:
    """
    Return canonical JSON bytes for obj.
    Keys sorted, no whitespace, NFC strings, no floats.
    """
    normalized = _canon_value(obj)
    return json.dumps(normalized, separators=(",", ":"), sort_keys=True,
                      ensure_ascii=False).encode("utf-8")


def h_obj(domain: str, obj: dict) -> str:
    """
    H_OBJ(domain, obj) = SHA-256(domain_bytes || 0x00 || CANON(obj))
    Returns lowercase hex string (64 chars).
    """
    domain_bytes = domain.encode("ascii")
    payload = domain_bytes + b"\x00" + canon(obj)
    return hashlib.sha256(payload).hexdigest()


# ---------- array sort rules (malleability kill) ----------

def sort_sigset(sigset: list) -> list:
    """gate_lock_sigset MUST be sorted by pubkey lexicographically."""
    return sorted(sigset, key=lambda s: s.get("pubkey", ""))


# ---------- state hash ----------

def ledger_head_hash(hyperloop_state: dict) -> str:
    """
    ledger_head_hash = H_OBJ("EVEZ:CPF:StateV1", hyperloop_state)
    All fields that influence p_fire must be present here.
    Writers MUST include every field explicitly; no implicit defaults.
    """
    required = {"N", "tau", "omega", "poly_c", "round_id", "fires", "V"}
    missing = required - set(hyperloop_state.keys())
    if missing:
        raise ValueError(f"hyperloop_state missing required fields: {missing}")
    return h_obj("EVEZ:CPF:StateV1", hyperloop_state)


# ---------- params commit ----------

def params_commit(params: dict) -> str:
    """
    Commit to poly_c coefficients + f() definition + clamp rules + constants.
    params keys: poly_c_coefficients, fire_function, clamp_min, clamp_max,
                 omega_modulus, schema_version.
    """
    return h_obj("EVEZ:CPF:ParamsV1", params)


# ---------- GateLock hash ----------

def gatelock_hash(gatelock: dict) -> str:
    """
    Hash of the canonical GateLock object.
    Sorts sigset before hashing.
    """
    g = dict(gatelock)
    g["gate_lock_sigset"] = sort_sigset(g.get("gate_lock_sigset", []))
    return h_obj("EVEZ:CPF:GateLockV1", g)
