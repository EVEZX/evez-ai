#!/usr/bin/env python3
"""
OS-EVEZ Bundle Verifier — No API key. No account. Math only.
Usage: python3 verify_bundle.py events.json bundle_manifest.json
"""
import json, hashlib, sys

def verify(events_path="events.json", manifest_path="bundle_manifest.json"):
    events = json.load(open(events_path))
    manifest = json.load(open(manifest_path))
    root = hashlib.sha256(json.dumps(events, sort_keys=True).encode()).hexdigest()
    expected = manifest["root_hash"]
    if root == expected:
        print(f"VALID ✓ ({len(events)} events)")
        print(f"Root: {root}")
        return True
    print(f"TAMPERED ✗")
    print(f"Got:      {root}")
    print(f"Expected: {expected}")
    return False

if __name__ == "__main__":
    args = sys.argv[1:]
    ok = verify(*args) if args else verify()
    sys.exit(0 if ok else 1)
