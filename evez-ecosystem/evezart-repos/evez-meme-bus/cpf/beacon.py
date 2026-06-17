"""
cpf/beacon.py — Beacon selection and canonical beacon value derivation.

beacon_target must be deterministic given GateLock time/height.
No human choice in timing.

Rule (time-based, drand-mainnet period = 3 seconds):
  T_lock = lock_time_unix_ms
  DELTA_MS = protocol constant (default 240_000 = 4 min = ~80 drand rounds)
  beacon_target = first_beacon_round_at_or_after(T_lock + DELTA_MS)

For drand-mainnet (genesis_time=1595431050, period=3s):
  beacon_round = ceil((T_target_unix_s - genesis_time) / period)
"""
import math
import hashlib
from typing import Literal

# Protocol constants — in params_commit
DEFAULT_DELTA_MS: int = 240_000          # +4 minutes after lock
DRAND_GENESIS_UNIX_S: int = 1595431050   # drand-mainnet genesis
DRAND_PERIOD_S: int = 3                   # drand-mainnet round period

BeaconCanon = Literal["RAW", "HASHED32"]


def drand_round_for_time(unix_ms: int, delta_ms: int = DEFAULT_DELTA_MS) -> int:
    """
    Deterministic beacon round selection.
    beacon_target = first drand round at or after (unix_ms + delta_ms).
    """
    target_unix_s = (unix_ms + delta_ms) / 1000.0
    # ceil((target - genesis) / period)
    elapsed = target_unix_s - DRAND_GENESIS_UNIX_S
    if elapsed < 0:
        raise ValueError("Target time is before drand genesis")
    return math.ceil(elapsed / DRAND_PERIOD_S)


def verify_beacon_target(lock_time_unix_ms: int, beacon_target: int,
                         delta_ms: int = DEFAULT_DELTA_MS) -> bool:
    """
    Verify that beacon_target == expected deterministic target for lock_time.
    Used by auditors to reject GateLocks with hand-picked beacon rounds.
    """
    expected = drand_round_for_time(lock_time_unix_ms, delta_ms)
    return beacon_target == expected


def canonical_b32(beacon_output_hex: str, beacon_canon: BeaconCanon) -> bytes:
    """
    B32 = the canonical 32-byte beacon value used in IKM.

    If beacon_canon == "HASHED32":
        B32 = SHA-256("EVEZ:CPF:beacon" || 0x00 || B_raw)
    If beacon_canon == "RAW":
        B32 = B_raw  (beacon already outputs 32 bytes, passed as hex)
    """
    raw = bytes.fromhex(beacon_output_hex)
    if beacon_canon == "HASHED32":
        domain = b"EVEZ:CPF:beacon"
        return hashlib.sha256(domain + b"\x00" + raw).digest()
    elif beacon_canon == "RAW":
        if len(raw) != 32:
            raise ValueError(f"RAW beacon must be 32 bytes, got {len(raw)}")
        return raw
    else:
        raise ValueError(f"Unknown beacon_canon: {beacon_canon}")
