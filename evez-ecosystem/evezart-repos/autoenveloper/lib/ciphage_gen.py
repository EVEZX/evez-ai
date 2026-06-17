"""
CIPHAGE GEN — Cipher Pattern Generator
The "least expected, most valued" module:
Cross-domain structural isomorphism detector + cipher pattern engine.

Two modes:
1. Generate: produce novel encoding patterns from a seed structure
2. Detect: find structural equivalences across domains (code, finance, bio, language)
"""

import hashlib
import json
import math
import re
from typing import Any

# ── CIPHER GENERATION ENGINE ──────────────────────────────────────────────────

def generate_substitution_cipher(seed: str, alphabet: str = None) -> dict:
    """Generate a deterministic substitution cipher from a seed string."""
    if alphabet is None:
        alphabet = "abcdefghijklmnopqrstuvwxyz"
    
    # Deterministic shuffle via seed hash
    h = hashlib.sha256(seed.encode()).digest()
    shuffled = list(alphabet)
    for i in range(len(shuffled) - 1, 0, -1):
        j = h[i % len(h)] % (i + 1)
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    
    return {
        "encrypt": dict(zip(alphabet, shuffled)),
        "decrypt": dict(zip(shuffled, alphabet)),
        "seed":    seed,
        "type":    "substitution"
    }


def generate_polyalphabetic_cipher(seed: str, period: int = 5) -> dict:
    """Vigenère-style multi-alphabet cipher from seed."""
    alphabets = []
    for i in range(period):
        sub_seed = f"{seed}_{i}"
        alphabets.append(generate_substitution_cipher(sub_seed)["encrypt"])
    return {
        "alphabets": alphabets,
        "period":    period,
        "seed":      seed,
        "type":      "polyalphabetic"
    }


def generate_transposition_matrix(seed: str, size: int = 8) -> dict:
    """Generate a transposition grid cipher."""
    h = hashlib.sha256(seed.encode()).digest()
    indices = list(range(size))
    for i in range(len(indices) - 1, 0, -1):
        j = h[i % len(h)] % (i + 1)
        indices[i], indices[j] = indices[j], indices[i]
    return {
        "column_order": indices,
        "grid_size":    size,
        "seed":         seed,
        "type":         "transposition"
    }


# ── PATTERN GENERATION ────────────────────────────────────────────────────────

def generate_fractal_pattern(depth: int = 4, rule: str = "sierpinski") -> dict:
    """Generate L-system / fractal expansion pattern."""
    rules = {
        "sierpinski": {"A": "B-A-B", "B": "A+B+A", "axiom": "A", "angle": 60},
        "dragon":     {"X": "X+YF+", "Y": "-FX-Y", "axiom": "FX", "angle": 90},
        "koch":       {"F": "F+F--F+F", "axiom": "F", "angle": 60},
        "plant":      {"X": "F+[[X]-X]-F[-FX]+X", "F": "FF", "axiom": "X", "angle": 25},
    }
    cfg = rules.get(rule, rules["sierpinski"])
    sequence = cfg["axiom"]
    for _ in range(depth):
        sequence = "".join(cfg.get(c, c) for c in sequence)
    return {
        "rule":     rule,
        "depth":    depth,
        "length":   len(sequence),
        "sequence": sequence[:500] + ("..." if len(sequence) > 500 else ""),
        "angle":    cfg["angle"]
    }


def generate_recursive_numeric_pattern(seed_int: int, steps: int = 20,
                                        mode: str = "collatz") -> dict:
    """Generate recursive numeric sequences."""
    def collatz(n):
        seq = [n]
        while n != 1 and len(seq) < 1000:
            n = n // 2 if n % 2 == 0 else 3 * n + 1
            seq.append(n)
        return seq

    def fibonacci_mod(n, mod=1000):
        a, b, seq = 0, 1, [0]
        for _ in range(n):
            a, b = b, (a + b) % mod
            seq.append(a)
        return seq

    def logistic_map(r=3.9, x0=0.5, n=50):
        x, seq = x0, [x0]
        for _ in range(n):
            x = r * x * (1 - x)
            seq.append(round(x, 6))
        return seq

    sequences = {
        "collatz":   lambda: collatz(seed_int),
        "fibonacci": lambda: fibonacci_mod(steps),
        "logistic":  lambda: logistic_map(n=steps),
    }
    seq = sequences.get(mode, sequences["collatz"])()
    return {"mode": mode, "seed": seed_int, "steps": steps, "sequence": seq}


# ── CROSS-DOMAIN ISOMORPHISM DETECTOR ────────────────────────────────────────

def extract_structural_fingerprint(data: Any, domain: str = "auto") -> dict:
    """
    Extract domain-agnostic structural fingerprint from any input.
    Works on: code strings, numeric sequences, text, JSON objects.
    Returns a vector of structural metrics for comparison.
    """
    text = json.dumps(data) if not isinstance(data, str) else data

    tokens = re.findall(r'\w+|[^\w\s]', text)
    if not tokens:
        return {"error": "empty input"}

    # Entropy
    freq = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    total = len(tokens)
    entropy = -sum((c/total) * math.log2(c/total) for c in freq.values() if c > 0)

    # Repetition ratio
    unique_ratio = len(freq) / total

    # Nesting depth (brackets)
    depth, max_depth, cur = 0, 0, 0
    for ch in text:
        if ch in "([{":
            cur += 1
            max_depth = max(max_depth, cur)
        elif ch in ")]}":
            cur -= 1

    # Transition entropy (bigram)
    bigrams = [tokens[i] + tokens[i+1] for i in range(len(tokens)-1)]
    bg_freq = {}
    for b in bigrams:
        bg_freq[b] = bg_freq.get(b, 0) + 1
    bg_total = len(bigrams) or 1
    bigram_entropy = -sum((c/bg_total) * math.log2(c/bg_total) for c in bg_freq.values())

    return {
        "domain":         domain,
        "token_count":    total,
        "unique_ratio":   round(unique_ratio, 4),
        "entropy":        round(entropy, 4),
        "bigram_entropy": round(bigram_entropy, 4),
        "max_depth":      max_depth,
        "avg_token_len":  round(sum(len(t) for t in tokens) / total, 2),
        "length":         len(text)
    }


def compare_structures(a: Any, b: Any,
                        domain_a: str = "unknown", domain_b: str = "unknown") -> dict:
    """
    Compare structural fingerprints of two inputs.
    Returns similarity score and dimension-wise diff.
    """
    fa = extract_structural_fingerprint(a, domain_a)
    fb = extract_structural_fingerprint(b, domain_b)

    dims = ["unique_ratio", "entropy", "bigram_entropy", "avg_token_len"]
    diffs = {}
    scores = []
    for d in dims:
        va, vb = fa.get(d, 0), fb.get(d, 0)
        mx = max(abs(va), abs(vb), 1e-9)
        diff = abs(va - vb) / mx
        diffs[d] = round(diff, 4)
        scores.append(1 - min(diff, 1))

    similarity = round(sum(scores) / len(scores), 4)
    return {
        "similarity":    similarity,
        "isomorphic":    similarity > 0.85,
        "fingerprint_a": fa,
        "fingerprint_b": fb,
        "dimension_diffs": diffs,
        "interpretation": (
            "High structural isomorphism — these patterns share the same underlying grammar."
            if similarity > 0.85 else
            "Moderate structural similarity — partial pattern overlap."
            if similarity > 0.6 else
            "Low structural similarity — distinct pattern classes."
        )
    }


# ── TOOL WRAPPERS ─────────────────────────────────────────────────────────────

def get_tools():
    from tools.registry import Tool

    return [
        Tool(
            name="ciphage_generate_cipher",
            description="Generate a deterministic cipher from a seed. Types: substitution, polyalphabetic, transposition.",
            parameters={
                "type": "object",
                "properties": {
                    "seed":       {"type": "string", "description": "Seed string for deterministic generation"},
                    "cipher_type":{"type": "string", "enum": ["substitution", "polyalphabetic", "transposition"]},
                    "period":     {"type": "integer", "description": "Period for polyalphabetic cipher", "default": 5},
                    "size":       {"type": "integer", "description": "Grid size for transposition", "default": 8}
                },
                "required": ["seed", "cipher_type"]
            },
            fn=lambda seed, cipher_type, period=5, size=8: (
                generate_substitution_cipher(seed) if cipher_type == "substitution" else
                generate_polyalphabetic_cipher(seed, period) if cipher_type == "polyalphabetic" else
                generate_transposition_matrix(seed, size)
            )
        ),
        Tool(
            name="ciphage_fractal_pattern",
            description="Generate fractal/L-system patterns. Rules: sierpinski, dragon, koch, plant.",
            parameters={
                "type": "object",
                "properties": {
                    "rule":  {"type": "string", "enum": ["sierpinski", "dragon", "koch", "plant"]},
                    "depth": {"type": "integer", "description": "Expansion depth (1-6 recommended)"}
                },
                "required": ["rule"]
            },
            fn=lambda rule, depth=4: generate_fractal_pattern(depth, rule)
        ),
        Tool(
            name="ciphage_numeric_pattern",
            description="Generate recursive numeric sequences. Modes: collatz, fibonacci, logistic.",
            parameters={
                "type": "object",
                "properties": {
                    "seed":  {"type": "integer", "description": "Starting integer"},
                    "mode":  {"type": "string", "enum": ["collatz", "fibonacci", "logistic"]},
                    "steps": {"type": "integer", "default": 20}
                },
                "required": ["seed", "mode"]
            },
            fn=lambda seed, mode, steps=20: generate_recursive_numeric_pattern(seed, steps, mode)
        ),
        Tool(
            name="ciphage_compare_structures",
            description="Cross-domain structural isomorphism detector. Compare any two inputs (code, text, data) for structural equivalence.",
            parameters={
                "type": "object",
                "properties": {
                    "input_a":   {"type": "string", "description": "First input (any domain)"},
                    "input_b":   {"type": "string", "description": "Second input (any domain)"},
                    "domain_a":  {"type": "string", "description": "Domain label for input A (e.g. 'code', 'financial', 'linguistic')"},
                    "domain_b":  {"type": "string", "description": "Domain label for input B"}
                },
                "required": ["input_a", "input_b"]
            },
            fn=lambda input_a, input_b, domain_a="unknown", domain_b="unknown": (
                compare_structures(input_a, input_b, domain_a, domain_b)
            )
        )
    ]
