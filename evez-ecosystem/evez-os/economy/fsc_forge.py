#!/usr/bin/env python3
"""
FSC_FORGE Credit Broker — EVEZ Credit Protocol v0.1.0
Converts verified probe results into EVEZ credits.
Zero infrastructure. Runs anywhere Python 3 runs.
"""
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
from typing import Any, Dict, List, Optional

GENESIS_HASH = hashlib.sha256(b"EVEZ-SPINE-GENESIS").hexdigest()

CREDIT_RATES = {
    "CANONICAL":       {"probe": 1, "falsifier": 2},
    "TESTED":          {"probe": 1, "falsifier": 0},
    "ALERT":           {"probe": 1, "threat_bounty": 5},
    "SPLIT_DETECTED":  {"probe": 1, "threat_bounty": 2},
    "CONTESTED":       {"falsifier": 1},
    "META_CANONICAL":  {"mission": 5},
    "PENDING":         {},
    "THEATRICAL":      {},
}

_ECB_CACHE: Dict[str, Any] = {}

def fetch_ecb_rate() -> Dict[str, float]:
    global _ECB_CACHE
    if _ECB_CACHE and (time.time() - _ECB_CACHE.get("ts", 0)) < 3600:
        return _ECB_CACHE["rates"]
    try:
        import urllib.request, re
        with urllib.request.urlopen(
            "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml",
            timeout=5
        ) as r:
            xml = r.read().decode()
        rates = {m.group(1): float(m.group(2)) for m in
                 re.finditer(r"currency='([A-Z]+)' rate='([0-9.]+)'", xml)}
        _ECB_CACHE = {"rates": rates, "ts": time.time()}
        return rates
    except Exception:
        return {"USD": 1.1753, "GBP": 0.8738}

def count_credits(spine_path: Path) -> Dict[str, Any]:
    credits = {"probe": 0, "falsifier": 0, "threat_bounty": 0, "mission": 0}
    with spine_path.open() as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                entry = json.loads(line)
                tp = entry.get("truth_plane", "")
                for credit_type, amount in CREDIT_RATES.get(tp, {}).items():
                    credits[credit_type] += amount
            except Exception:
                pass
    total = sum(credits.values())
    rates = fetch_ecb_rate()
    floor_eur = total * 0.01
    floor_usd = floor_eur * rates.get("USD", 1.1753)
    return {
        "credits": credits,
        "total": total,
        "floor_eur": round(floor_eur, 4),
        "floor_usd": round(floor_usd, 4),
        "ecb_usd": rates.get("USD"),
        "distribution": {
            "creator_40pct": round(floor_usd * 0.40, 6),
            "player_pool_40pct": round(floor_usd * 0.40, 6),
            "mission_fund_20pct": round(floor_usd * 0.20, 6),
        }
    }

def generate_identity_keypair() -> Dict[str, str]:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
        pub_hex = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
        priv_hex = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()).hex()
        return {"public_key": pub_hex, "private_key": priv_hex, "note": "Keep private_key on device. Never transmit."}
    except ImportError:
        seed = hashlib.sha256(f"{time.time_ns()}".encode()).hexdigest()
        return {"public_key": hashlib.sha256(seed.encode()).hexdigest(), "private_key": seed, "note": "Install cryptography for proper ed25519 keys."}

def sign_entry(entry_hash: str, private_key_hex: str) -> str:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        priv = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
        sig = priv.sign(bytes.fromhex(entry_hash))
        return sig.hex()
    except ImportError:
        return hashlib.sha256(f"{entry_hash}:{private_key_hex}".encode()).hexdigest()

if __name__ == "__main__":
    import sys
    spine_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("spine/spine.jsonl")
    if not spine_path.exists():
        print(f"Spine not found: {spine_path}")
        sys.exit(1)
    result = count_credits(spine_path)
    print(f"\nEVEZ Credit Broker — Session Report")
    print(f"{'='*40}")
    print(f"Probe credits:     {result['credits']['probe']}")
    print(f"Falsifier credits: {result['credits']['falsifier']}")
    print(f"Threat bounty:     {result['credits']['threat_bounty']}")
    print(f"Mission credits:   {result['credits']['mission']}")
    print(f"TOTAL:             {result['total']} credits")
    print(f"Floor value:       EUR{result['floor_eur']} / USD{result['floor_usd']}")
    print(f"ECB rate:          1 EUR = {result['ecb_usd']} USD")
    print(f"\nDistribution (per session):")
    print(f"  Creator (40%):      USD{result['distribution']['creator_40pct']}")
    print(f"  Player pool (40%):  USD{result['distribution']['player_pool_40pct']}")
    print(f"  Mission fund (20%): USD{result['distribution']['mission_fund_20pct']}")
    print(f"\nPowered by EVEZ | github.com/EvezArt/evez-os")
