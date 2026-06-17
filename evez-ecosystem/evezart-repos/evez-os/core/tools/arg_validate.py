#!/usr/bin/env python3
"""Minimal ARG map validator.

Checks that:
- required lobbies exist as nodes
- required edge ordering exists
- (optional) provenance_refs exist syntactically

This is intentionally lightweight. The full validation is done by comparing against spine events.
"""
import json, sys
from pathlib import Path

REQUIRED = ["DNS","BGP","TLS","CDN","BACKEND"]

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/arg_validate.py path/to/player_map.json")
        raise SystemExit(2)
    p = Path(sys.argv[1])
    data = json.loads(p.read_text(encoding="utf-8"))
    nodes = {n["id"] for n in data.get("nodes", [])}
    missing = [x for x in REQUIRED if x not in nodes]
    if missing:
        print("FAIL missing required nodes:", missing)
        raise SystemExit(1)

    edges = {(e["src"], e["dst"]) for e in data.get("edges", [])}
    required_edges = [("DNS","BGP"),("BGP","TLS"),("TLS","CDN"),("CDN","BACKEND")]
    missing_edges = [e for e in required_edges if e not in edges]
    if missing_edges:
        print("FAIL missing required edges:", missing_edges)
        raise SystemExit(1)

    print("PASS structural lobby chain present. Next: align provenance to spine for a real win.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
