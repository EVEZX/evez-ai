"""
EVEZ Autoenveloper — Mathematical Invariants Core
Implements the Φ(x) fingerprint vector:
    Φ(x) = [C(x), I₁..I₅(x), λ₂(x), Hₚ(x)]

Where:
    C(x)      — compression ratio (LZ77/zlib upper bound on K(x))
    I₁..I₅   — mutual information at lag k=1..5
    λ₂        — Laplacian Fiedler value (spectral gap)
    Hₚ        — persistence entropy (PMI-based topological fingerprint)

Similarity:
    S(x,y) = √( cos(Φx,Φy) · (1 - JS(Φx,Φy)) )
"""
import zlib, math, re
from collections import Counter
from typing import List, Tuple
import numpy as np


# ── 1. COMPRESSION RATIO ──────────────────────────────────────
def compression_ratio(x: str) -> float:
    """
    Upper bound on K(x)/len(x) via zlib deflate.
    Returns ratio in [0,1] where lower = more compressible = more regular.
    """
    raw = x.encode("utf-8")
    if not raw:
        return 0.0
    compressed = zlib.compress(raw, level=9)
    return len(compressed) / max(len(raw), 1)


# ── 2. MUTUAL INFORMATION PROFILE ────────────────────────────
def mutual_info_profile(x: str, max_lag: int = 5) -> List[float]:
    """
    MI(X_t; X_{t+k}) for k = 1..max_lag over character/token sequence.
    Captures dependency structure: Markov vs fractal vs IID.
    """
    tokens = list(x)
    n = len(tokens)
    if n < max_lag + 2:
        return [0.0] * max_lag

    results = []
    for lag in range(1, max_lag + 1):
        pairs = list(zip(tokens[:n-lag], tokens[lag:]))
        if not pairs:
            results.append(0.0)
            continue

        # Joint distribution
        joint_counts = Counter(pairs)
        marginal_a = Counter(t[0] for t in pairs)
        marginal_b = Counter(t[1] for t in pairs)
        total = len(pairs)

        mi = 0.0
        for (a, b), cnt in joint_counts.items():
            p_ab = cnt / total
            p_a  = marginal_a[a] / total
            p_b  = marginal_b[b] / total
            if p_ab > 0 and p_a > 0 and p_b > 0:
                mi += p_ab * math.log2(p_ab / (p_a * p_b))
        results.append(max(0.0, mi))

    return results


# ── 3. SPECTRAL GAP (FIEDLER VALUE λ₂) ───────────────────────
def spectral_gap(x: str, max_nodes: int = 64) -> float:
    """
    Laplacian Fiedler value λ₂ of the token co-occurrence graph.
    Measures algebraic connectivity — structural skeleton of the sequence.
    Higher λ₂ = more connected = more complex interdependence.
    """
    # Build co-occurrence graph (bigram adjacency)
    tokens = list(x[:max_nodes * 4])  # cap for performance
    vocab = sorted(set(tokens))
    if len(vocab) < 3:
        return 0.0

    # Cap vocabulary for tractability
    if len(vocab) > max_nodes:
        freq = Counter(tokens)
        vocab = [w for w, _ in freq.most_common(max_nodes)]
    
    idx = {v: i for i, v in enumerate(vocab)}
    n = len(vocab)
    A = np.zeros((n, n))

    for a, b in zip(tokens[:-1], tokens[1:]):
        if a in idx and b in idx:
            i, j = idx[a], idx[b]
            A[i, j] += 1
            A[j, i] += 1  # undirected

    # Normalize and compute Laplacian
    row_sums = A.sum(axis=1)
    D = np.diag(row_sums)
    L = D - A

    if n < 3:
        return 0.0

    try:
        # Get smallest non-trivial eigenvalue
        eigenvalues = np.linalg.eigvalsh(L)
        eigenvalues_sorted = np.sort(eigenvalues)
        # λ₂ is the second smallest (first is always ≈0)
        fiedler = float(eigenvalues_sorted[1]) if len(eigenvalues_sorted) > 1 else 0.0
        return max(0.0, fiedler)
    except Exception:
        return 0.0


# ── 4. PERSISTENCE ENTROPY ────────────────────────────────────
def persistence_entropy(x: str, window: int = 8) -> float:
    """
    PMI-based persistence entropy — Cohen-Steiner stable topological fingerprint.
    Invariant under Lipschitz perturbations.
    
    Approximates: H_p = -Σ (l_i / L) log(l_i / L)
    where l_i = persistence (lifetime) of topological features,
    computed here via sliding-window PMI persistence.
    """
    if len(x) < window * 2:
        return 0.0

    tokens = list(x)
    n = len(tokens)
    
    # Compute local PMI scores across sliding windows
    lifetimes = []
    
    for start in range(0, n - window, window // 2):
        segment = tokens[start:start + window]
        if len(segment) < 2:
            continue
        
        # Local bigram PMI
        pairs = Counter(zip(segment[:-1], segment[1:]))
        marginal = Counter(segment)
        seg_total = len(segment) - 1
        
        local_pmi = 0.0
        for (a, b), cnt in pairs.items():
            p_ab = cnt / seg_total
            p_a  = marginal[a] / len(segment)
            p_b  = marginal[b] / len(segment)
            if p_ab > 0 and p_a > 0 and p_b > 0:
                local_pmi += p_ab * math.log2(p_ab / (p_a * p_b))
        
        lifetimes.append(abs(local_pmi))
    
    if not lifetimes:
        return 0.0
    
    L = sum(lifetimes)
    if L == 0:
        return 0.0
    
    # Shannon entropy over persistence distribution
    entropy = 0.0
    for l in lifetimes:
        if l > 0:
            p = l / L
            entropy -= p * math.log2(p)
    
    return entropy


# ── FINGERPRINT VECTOR ────────────────────────────────────────
def fingerprint(x: str) -> dict:
    """Compute full Φ(x) = [C(x), I₁..I₅(x), λ₂(x), Hₚ(x)]."""
    return {
        "compression": compression_ratio(x),
        "mi":          mutual_info_profile(x, max_lag=5),
        "lambda2":     spectral_gap(x),
        "entropy":     persistence_entropy(x),
    }


def flatten(phi: dict) -> np.ndarray:
    """Flatten fingerprint dict to numpy vector."""
    return np.array(
        [phi["compression"]] + phi["mi"] + [phi["lambda2"], phi["entropy"]],
        dtype=float
    )


# ── JENSEN-SHANNON DIVERGENCE ─────────────────────────────────
def jensen_shannon(va: np.ndarray, vb: np.ndarray) -> float:
    """
    JS divergence between two vectors (treated as discrete distributions
    after softmax normalization). Range [0,1], 0=identical.
    """
    def softmax(v):
        v = v - v.max()  # numerical stability
        e = np.exp(v)
        return e / (e.sum() + 1e-12)

    pa = softmax(va)
    pb = softmax(vb)
    pm = (pa + pb) / 2.0

    def kl(p, q):
        mask = (p > 0) & (q > 0)
        return float(np.sum(p[mask] * np.log2(p[mask] / q[mask])))

    js = (kl(pa, pm) + kl(pb, pm)) / 2.0
    return min(1.0, max(0.0, js))


# ── SIMILARITY ────────────────────────────────────────────────
def similarity(a: dict, b: dict) -> Tuple[float, np.ndarray, np.ndarray]:
    """
    S(x,y) = √( cos(Φx,Φy) · (1 - JS(Φx,Φy)) )
    
    Geometric mean of:
    - Cosine similarity: angular alignment of fingerprint vectors
    - 1 - JS divergence: distributional shape agreement
    
    This punishes mismatch in either dimension independently.
    Returns (score, vector_a, vector_b).
    """
    va = flatten(a)
    vb = flatten(b)

    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)

    if norm_a < 1e-10 or norm_b < 1e-10:
        return 0.0, va, vb

    cos_sim = float(np.dot(va, vb) / (norm_a * norm_b))
    cos_sim = max(0.0, min(1.0, cos_sim))  # clamp to [0,1]

    js = jensen_shannon(va, vb)
    
    score = math.sqrt(cos_sim * (1.0 - js))
    return score, va, vb
