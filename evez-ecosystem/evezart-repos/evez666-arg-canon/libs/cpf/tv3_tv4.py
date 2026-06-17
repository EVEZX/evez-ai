#!/usr/bin/env python3
"""
EVEZ CPF v1 — Test Vectors TV3 + TV4 (byte-exact)
Run: python -m libs.cpf.tv3_tv4
"""
import hashlib, hmac, json, unicodedata
from typing import Any

UINT64_MAX = (1 << 64) - 1

def _canon_value(v: Any) -> Any:
    if isinstance(v, bool): return v
    if isinstance(v, int):
        if v < 0 or v > UINT64_MAX: raise ValueError(f"Integer {v} out of [0, 2^64-1]")
        return v
    if isinstance(v, float): raise TypeError(f"Floats forbidden: {v!r}")
    if isinstance(v, str): return unicodedata.normalize("NFC", v)
    if isinstance(v, dict): return {k: _canon_value(val) for k, val in sorted(v.items())}
    if isinstance(v, list): return [_canon_value(i) for i in v]
    if v is None: return v
    raise TypeError(f"Unsupported type: {type(v)}")

def canon_bytes(obj): return json.dumps(_canon_value(obj), ensure_ascii=True, separators=(',',':'), sort_keys=True).encode('utf-8')
def h_obj_hex(domain, obj): return hashlib.sha256(domain + b'' + canon_bytes(obj)).digest().hex().lower()
def beacon_to_b32(b): return hashlib.sha256(b'EVEZ:CPF:beacon' + b'' + b).digest()
def hkdf_extract(salt, ikm): return hmac.new(salt, ikm, hashlib.sha256).digest()
def hkdf_expand(prk, info, n=32): return hmac.new(prk, info + b'\x01', hashlib.sha256).digest()[:n]
def derive(b32, rid, lhh):
    ikm = b32 + rid.to_bytes(8,'big') + lhh
    prk = hkdf_extract(b'EVEZ:CPF:v1', ikm)
    return prk, hkdf_expand(prk, b'TOPO', 32), hkdf_expand(prk, b'FIRE', 32)
def omega_from(r_topo, mod=3): return 1 + (int.from_bytes(r_topo,'big') % mod)
def is_sigset_sorted(gl): keys=[s['pubkey'] for s in gl.get('gate_lock_sigset',[])]; return keys==sorted(keys)

if __name__ == '__main__':
    # TV3 smoke check
    state = {'N':123456789,'poly_inputs':{'a':1,'b':2},'state_schema_id':'hyperloop_state:v7','tau':16,'window_id':'run44:R356-R360'}
    lhh = h_obj_hex(b'EVEZ:CPF:StateV1', state)
    assert lhh == 'e1d66a4f0b401989f4f92f7b05f02d9ebc3b27179b3d36c9f860248803110df3', f'TV3 lhh fail: {lhh}'
    print(f'TV3 ledger_head_hash OK: {lhh}')
    # TV4 smoke check
    def norm_v8(raw):
        pi = dict(raw.get('poly_inputs') or {})
        pi.setdefault('a',0); pi.setdefault('b',0); pi.setdefault('c',0)
        n = dict(raw); n['poly_inputs'] = pi; n.setdefault('abstain_mode',0); return n
    raw4 = {'N':42,'tau':4,'window_id':'run44:R356-R360','state_schema_id':'hyperloop_state:v8','poly_inputs':{'a':7}}
    lhh4 = h_obj_hex(b'EVEZ:CPF:StateV1', norm_v8(raw4))
    assert lhh4 == 'd85c2cb10dc81bf0b757af621a83ed59bcae5ad37e72e62dfb27fae680f51615', f'TV4 lhh fail: {lhh4}'
    print(f'TV4 ledger_head_hash OK: {lhh4}')
    print('ALL CPF TV3+TV4 PASSED')