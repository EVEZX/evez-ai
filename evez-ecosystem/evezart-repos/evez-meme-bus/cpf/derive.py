"""
cpf/derive.py — CPF split randomness: byte-exact HKDF derivation.

Given:
  B32  = canonical 32-byte beacon value (from cpf.beacon.canonical_b32)
  RID8 = round_id as 8-byte big-endian
  LHH  = ledger_head_hash as 32 raw bytes (from hex)

IKM = B32 || RID8 || LHH

HKDF (SHA-256):
  PRK      = HKDF-Extract(salt = b"EVEZ:CPF:v1", IKM)
  r_topo   = HKDF-Expand(PRK, info=b"TOPO", 32)
  r_fire   = HKDF-Expand(PRK, info=b"FIRE", 32)

Interpretation:
  t_topo   = int.from_bytes(r_topo, 'big')  in [0, 2^256)
  x_fire   = int.from_bytes(r_fire, 'big')  in [0, 2^256)
  omega    = 1 + (t_topo % OMEGA_MODULUS)   (default mod 3 => omega in {1,2,3})
  t_fire   = THRESH(poly_c, N, tau, omega)   uint256 threshold
  FIRE     = x_fire < t_fire

No floats in the consensus path. All comparisons are uint256.
"""
import hashlib
import hmac
from typing import NamedTuple

OMEGA_MODULUS: int = 3          # extend to 32 for DOE
INT256_MAX: int = 2**256 - 1
INT256_SIZE: int = 2**256


# ---------- HKDF-SHA256 (RFC 5869) ----------

def _hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    return hmac.new(salt, ikm, hashlib.sha256).digest()


def _hkdf_expand(prk: bytes, info: bytes, length: int) -> bytes:
    """HKDF-Expand per RFC 5869. Max output = 255 * hash_len."""
    hash_len = 32
    n = -(-length // hash_len)  # ceil
    t = b""
    okm = b""
    for i in range(1, n + 1):
        t = hmac.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
        okm += t
    return okm[:length]


# ---------- public API ----------

class DeriveResult(NamedTuple):
    r_topo: bytes           # 32 raw bytes
    r_fire: bytes           # 32 raw bytes
    t_topo: int             # uint256
    x_fire: int             # uint256
    omega: int              # 1..OMEGA_MODULUS
    prk: bytes              # 32 raw bytes (for auditing)


def derive(b32: bytes, round_id: int, ledger_head_hash_hex: str) -> DeriveResult:
    """
    Full CPF randomness derivation.
    All inputs are deterministic; no floating-point in this path.
    """
    if len(b32) != 32:
        raise ValueError(f"b32 must be 32 bytes, got {len(b32)}")
    if round_id < 0 or round_id >= 2**64:
        raise ValueError(f"round_id out of [0, 2^64-1]: {round_id}")

    rid8 = round_id.to_bytes(8, "big")
    lhh = bytes.fromhex(ledger_head_hash_hex)
    if len(lhh) != 32:
        raise ValueError("ledger_head_hash must be 64 hex chars (32 bytes)")

    ikm = b32 + rid8 + lhh
    prk = _hkdf_extract(b"EVEZ:CPF:v1", ikm)

    r_topo = _hkdf_expand(prk, b"TOPO", 32)
    r_fire = _hkdf_expand(prk, b"FIRE", 32)

    t_topo = int.from_bytes(r_topo, "big")
    x_fire = int.from_bytes(r_fire, "big")
    omega  = 1 + (t_topo % OMEGA_MODULUS)

    return DeriveResult(
        r_topo=r_topo,
        r_fire=r_fire,
        t_topo=t_topo,
        x_fire=x_fire,
        omega=omega,
        prk=prk
    )


# ---------- threshold (no floats) ----------

def thresh(poly_c: int, omega: int) -> int:
    """
    Convert poly_c probability (scaled integer: poly_c_scaled = floor(p * SCALE))
    to a uint256 threshold.

    t_fire = floor(poly_c_scaled * 2^256 / SCALE)

    SCALE = 10**18  (so poly_c=0.75 => poly_c_scaled=750_000_000_000_000_000)

    forced_no_fire:  poly_c_scaled=0          => t_fire=0
    always_fire:     poly_c_scaled=SCALE      => t_fire=INT256_MAX (capped)

    omega is passed for future multi-omega threshold tables;
    currently omega only controls r_topo routing, not the threshold directly.
    Threshold is solely a function of poly_c for the v1 spec.
    """
    SCALE = 10**18
    if poly_c < 0 or poly_c > SCALE:
        raise ValueError(f"poly_c_scaled must be in [0, SCALE]. Got {poly_c}")
    if poly_c == 0:
        return 0
    if poly_c == SCALE:
        return INT256_MAX
    t = (poly_c * INT256_SIZE) // SCALE
    return min(t, INT256_MAX)


def fire_decision(x_fire: int, t_fire: int) -> bool:
    """
    FIRE iff x_fire < t_fire.
    No floats, no rounding, pure uint256 comparison.
    """
    return x_fire < t_fire
