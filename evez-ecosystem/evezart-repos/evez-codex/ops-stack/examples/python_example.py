#!/usr/bin/env python3
"""
Python example using rfc8785 for canonical JSON serialization
"""

import rfc8785
import json

def main():
    # Sample data
    data = {
        "market": "cryptocurrency",
        "ticker": "BTC-USD",
        "price": 50000,
        "timestamp": 1234567890,
        "volume": 1000000
    }
    
    # Canonicalize
    canonical = rfc8785.dumps(data)
    
    print("Python Canonical JSON Example")
    print("=" * 50)
    print(f"Original data: {json.dumps(data)}")
    print(f"Canonical:     {canonical}")
    print("=" * 50)
    
    # Verify deterministic output
    canonical2 = rfc8785.dumps(data)
    assert canonical == canonical2, "Canonicalization is not deterministic!"
    
    print("✅ Canonicalization is deterministic")

if __name__ == "__main__":
    main()
