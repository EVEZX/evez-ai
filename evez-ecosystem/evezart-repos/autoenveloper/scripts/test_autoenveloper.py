"""
Autoenveloper CLI — Quick Test Runner
Tests all new modules without requiring OpenAI API key.
"""
import sys
import json

sys.path.insert(0, "/home/user/surething/cells/203f2e09-85e4-4638-ba08-cffd9c6e0b02/workspace/src/autoenveloper")

from tools.ciphage_gen import (
    generate_substitution_cipher,
    generate_fractal_pattern,
    generate_recursive_numeric_pattern,
    compare_structures
)
from tools.geometric import spectral_analysis, detect_symmetry
from tools.linguistic import style_fingerprint, detect_patterns, anonymize_text

def run_tests():
    results = {}

    # 1. Ciphage - cipher generation
    cipher = generate_substitution_cipher("evezart666")
    results["cipher"] = {
        "seed": cipher["seed"],
        "sample_map": dict(list(cipher["encrypt"].items())[:5]),
        "type": cipher["type"]
    }

    # 2. Fractal pattern
    fractal = generate_fractal_pattern(depth=3, rule="sierpinski")
    results["fractal"] = {
        "rule": fractal["rule"],
        "depth": fractal["depth"],
        "length": fractal["length"],
        "preview": fractal["sequence"][:80]
    }

    # 3. Cross-domain isomorphism
    code_sample = "for i in range(n): result += compute(i, cache[i % len(cache)])"
    finance_sample = "for tick in data: value += transform(tick, memory[tick % len(memory)])"
    iso = compare_structures(code_sample, finance_sample, "code", "finance")
    results["isomorphism"] = {
        "similarity": iso["similarity"],
        "isomorphic": iso["isomorphic"],
        "interpretation": iso["interpretation"]
    }

    # 4. Spectral analysis of logistic map
    from tools.ciphage_gen import generate_recursive_numeric_pattern
    seq = generate_recursive_numeric_pattern(42, steps=64, mode="logistic")["sequence"]
    spectral = spectral_analysis(seq)
    results["spectral"] = spectral

    # 5. Symmetry detection - regular hexagon
    import math
    hex_pts = [[math.cos(i * math.pi / 3), math.sin(i * math.pi / 3)] for i in range(6)]
    sym = detect_symmetry(hex_pts, tolerance=0.05)
    results["symmetry"] = sym

    # 6. Style fingerprint
    fp = style_fingerprint(
        "Build the system. Deploy the pattern. The recursive architecture "
        "reveals its own structure. Measure complexity. Feed it back. Repeat."
    )
    results["style_fingerprint"] = fp

    # 7. Anonymization
    anon = anonymize_text(
        "Contact me at evezart@gmail.com or 555-123-4567. My IP is 192.168.1.1. "
        "Hash: a7f3c2e9d1b844e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
        strategy="pseudonymize"
    )
    results["anonymization"] = {
        "original_length": anon["original_length"],
        "anonymized_text": anon["anonymized_text"],
        "strategy": anon["strategy"]
    }

    return results


if __name__ == "__main__":
    results = run_tests()
    print(json.dumps(results, indent=2))
