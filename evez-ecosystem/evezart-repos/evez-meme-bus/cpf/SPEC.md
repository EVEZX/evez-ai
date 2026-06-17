# EVEZ CPF GateLock v1 — Canonical Specification

## TL;DR: Malleability Kill List

For every round, the following must be true or you are back to Run 43:

1. `GateLock.ledger_head_hash` = `H_OBJ("EVEZ:CPF:StateV1", hyperloop_state)` — every field that influences `p_fire` is inside this hash
2. `GateLock.params_commit` = `H_OBJ("EVEZ:CPF:ParamsV1", cpf_params)` — all polynomial coefficients + function definition locked before reveal
3. `beacon_target` is computed deterministically: `first_drand_round_at_or_after(lock_time + DELTA)` — no human timing choice
4. All arrays inside hashed objects have fixed sort rules (sigset sorted by pubkey)
5. All "optional fields" normalized before hashing — missing field is not allowed; writers MUST include all fields with explicit values

---

## Object 1: GateLockV1

Written at **precommit-close**. Freezes all inputs that can affect `p_fire`.

```json
{
  "type": "EVEZ.GateLockV1",
  "cpf_version": "v1",
  "window_id": "run44:R356-R360",
  "round_id": 455,
  "lock_height": 115,
  "lock_time_unix_ms": 1772628000000,
  "ledger_head_hash": "<64 hex chars>",
  "state_schema_id": "hyperloop_state_v1",
  "state_canon": "JCS-UTF8",
  "params_commit": "<64 hex chars>",
  "beacon": {
    "beacon_id": "drand-mainnet",
    "beacon_target": 59087600,
    "beacon_delay": 80,
    "beacon_canon": "HASHED32"
  },
  "validator_set_hash": "<64 hex chars>",
  "gate_lock_sigset": [
    { "pubkey": "<id>", "sig": "<base64url>" }
  ]
}
```

**Hard rule**: Anything that influences `p_fire` must be derivable from `ledger_head_hash + params_commit + round_id`. No hidden "soft inputs."

---

## Object 2: RoundResultV1

Written **after beacon is known**. Audit proof of deterministic execution.

```json
{
  "type": "EVEZ.RoundResultV1",
  "cpf_version": "v1",
  "round_id": 455,
  "gate_lock_hash": "<64 hex chars>",
  "beacon_target": 59087600,
  "B": "<64 hex chars — beacon output>",
  "omega": 2,
  "x_fire": "<64 hex chars — 256-bit draw>",
  "t_fire": "<64 hex chars — 256-bit threshold>",
  "fire": false,
  "p_fire_repr": "0.224900"
}
```

**Consensus-critical**: only `fire = (x_fire < t_fire)`. `p_fire_repr` is human audit rendering only.

---

## Canonical Serialization (CANON)

```
CANON(obj) rules:
1. UTF-8 text
2. Keys sorted lexicographically at every object level
3. No insignificant whitespace
4. Numbers: non-negative integers only; base-10, no leading zeros
5. Byte strings: lowercase hex, no 0x prefix, fixed length
6. Arrays: order per field rules below
7. Strings: ASCII for IDs; unicode NFC-normalized

Array ordering:
  gate_lock_sigset: sorted by pubkey (lexicographic)
```

## Hashing (domain separation)

```
H_OBJ(domain, obj) = SHA-256(domain_bytes || 0x00 || CANON(obj))

Domains:
  "EVEZ:CPF:GateLockV1"    — for gatelock_hash
  "EVEZ:CPF:RoundResultV1" — for result hash
  "EVEZ:CPF:StateV1"       — for ledger_head_hash
  "EVEZ:CPF:ParamsV1"      — for params_commit
  "EVEZ:CPF:beacon"        — for beacon value canonicalization
```

## Beacon Selection (deterministic)

```
T_lock = lock_time_unix_ms
beacon_target = first_drand_round_at_or_after(T_lock + DELTA_MS)

For drand-mainnet:
  genesis_unix_s = 1595431050
  period_s       = 3
  beacon_target  = ceil((T_lock/1000 + DELTA_MS/1000 - genesis) / period)

DELTA_MS = 240_000 (4 minutes = ~80 drand rounds) [protocol constant]
```

## Randomness Derivation (HKDF, no floats)

```
B32  = canonical_b32(beacon_output, beacon_canon)
RID8 = round_id as 8-byte big-endian
LHH  = bytes.fromhex(ledger_head_hash)

IKM      = B32 || RID8 || LHH
PRK      = HKDF-Extract(salt=b"EVEZ:CPF:v1", IKM)
r_topo   = HKDF-Expand(PRK, info=b"TOPO", 32)
r_fire   = HKDF-Expand(PRK, info=b"FIRE", 32)

t_topo   = int_be(r_topo)
x_fire   = int_be(r_fire)
omega    = 1 + (t_topo mod 3)

t_fire   = floor(poly_c_scaled * 2^256 / 10^18)
           where poly_c_scaled in [0, 10^18]

FIRE     = x_fire < t_fire
```

## Running

```bash
# Run reference test vectors (must all PASS before deploying)
python3 -m cpf.validator --vectors

# Validate a GateLock file
python3 -m cpf.validator path/to/gatelock.json

# Validate + run round result
python3 -m cpf.validator path/to/gatelock.json <beacon_output_hex>
```
