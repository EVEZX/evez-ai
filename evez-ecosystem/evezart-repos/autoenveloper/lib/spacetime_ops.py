"""
EVEZ Spacetime Operators — Implementable topology for LLM-driven field manipulation.

GCL  — Geodesic Curriculum Learning (training manifold warping)
AWP  — Attentional Wormhole Protocol (nonlocal token bridges)
RFT  — Retrocausal Fine-Tuning (temporal gradient echo)
CEH  — Context Event Horizons (information thermodynamics)
SIF  — Semantic Inflation Fields (dynamic temperature tensor)
QSNS — Quantum Superposition of Narrative States
OPTE — Ontological Phase Transition Engine

Each is a callable: real math, real output.
"""
import math, zlib
from typing import List, Dict, Tuple, Optional
import numpy as np


# ── 1. RICCI FLOW ─────────────────────────────────────────────
def ricci_flow(
    embeddings: List[List[float]],
    iterations: int = 10,
    dt: float = 0.01
) -> Dict:
    """
    Discrete Ollivier-Ricci flow on embedding neighborhood graph.
    
    Update rule: g_{ij}(t+dt) = g_{ij}(t) - Ric_{ij}(t) * dt
    
    Redistributes curvature: overloaded semantic regions flatten,
    sparse regions contract. Keeps the manifold navigable.
    
    Input:  list of vectors (token/concept embeddings)
    Output: curvature-adjusted vectors + curvature history
    """
    vecs = np.array(embeddings, dtype=float)
    n = len(vecs)
    
    if n < 2:
        return {"adjusted": embeddings, "curvatures": [], "iterations_run": 0}
    
    # Normalize
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.where(norms < 1e-10, 1.0, norms)
    vecs = vecs / norms
    
    curvature_history = []
    
    for step in range(iterations):
        # Compute pairwise distances (cosine distance)
        D = 1.0 - (vecs @ vecs.T)  # [n, n] cosine distances
        np.fill_diagonal(D, 0.0)
        
        # Approximate Ricci curvature via Bakry-Emery:
        # κ(i,j) ≈ 1 - W₁(μᵢ, μⱼ) / d(i,j)
        # Simplified: use local neighborhood distributions
        sigma = D.std() + 1e-8
        W = np.exp(-D**2 / (2 * sigma**2))  # RBF neighborhood weights
        W = W / (W.sum(axis=1, keepdims=True) + 1e-10)
        
        # Ricci curvature approximation
        curvature = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                if D[i, j] > 1e-8:
                    # Earth mover cost between neighborhoods
                    mu_i = W[i]
                    mu_j = W[j]
                    # Simple 1-Wasserstein approximation
                    w1 = np.sum(np.abs(mu_i - mu_j) * D[i]) / 2.0
                    kappa = 1.0 - (w1 / D[i, j])
                    curvature[i, j] = kappa
                    curvature[j, i] = kappa
        
        mean_curv = float(curvature.mean())
        curvature_history.append({"step": step, "mean_curvature": mean_curv})
        
        # Flow update: flatten positive curvature regions
        for i in range(n):
            grad = np.zeros(vecs.shape[1])
            for j in range(n):
                if i != j and D[i, j] > 1e-8:
                    direction = vecs[j] - vecs[i]
                    grad += curvature[i, j] * direction * dt
            vecs[i] += grad
        
        # Re-normalize
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms = np.where(norms < 1e-10, 1.0, norms)
        vecs = vecs / norms
    
    return {
        "adjusted": vecs.tolist(),
        "curvatures": curvature_history,
        "iterations_run": iterations,
        "final_mean_curvature": curvature_history[-1]["mean_curvature"] if curvature_history else 0.0
    }


# ── 2. ENTROPY FIELD ──────────────────────────────────────────
def entropy_field(
    sequence: str,
    window_size: int = 16,
    stride: int = 4
) -> Dict:
    """
    Compute local entropy tensor H(t) over a sequence.
    
    Returns: token-level entropy profile + field statistics.
    Enables Semantic Inflation Field (SIF): high-entropy = inflate,
    low-entropy = deflate meaning-space locally.
    """
    tokens = list(sequence)
    n = len(tokens)
    
    if n < window_size:
        # Global entropy for short sequences
        counts = {}
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1
        total = len(tokens)
        h = -sum((c/total)*math.log2(c/total) for c in counts.values() if c > 0)
        return {
            "field": [{"position": 0, "entropy": h, "density": total}],
            "global_entropy": h,
            "max_entropy": math.log2(max(len(set(tokens)), 1)),
            "inflation_mask": ["expand" if h > 1.0 else "contract"],
            "entropy_gradient": 0.0
        }
    
    field = []
    for start in range(0, n - window_size + 1, stride):
        window = tokens[start:start + window_size]
        counts = {}
        for t in window:
            counts[t] = counts.get(t, 0) + 1
        total = len(window)
        h = -sum((c/total)*math.log2(c/total) for c in counts.values() if c > 0)
        field.append({
            "position": start + window_size // 2,
            "entropy": h,
            "density": len(set(window)),
            "inflation_mask": "expand" if h > math.log2(window_size) * 0.6 else "contract"
        })
    
    if not field:
        return {"field": [], "global_entropy": 0.0, "max_entropy": 0.0,
                "inflation_mask": [], "entropy_gradient": 0.0}
    
    entropies = [f["entropy"] for f in field]
    # Entropy gradient (first derivative) — where is entropy changing fastest?
    gradient = [
        entropies[i+1] - entropies[i]
        for i in range(len(entropies)-1)
    ] if len(entropies) > 1 else [0.0]
    
    return {
        "field": field,
        "global_entropy": sum(entropies) / len(entropies),
        "max_entropy": max(entropies),
        "min_entropy": min(entropies),
        "entropy_gradient": sum(abs(g) for g in gradient) / len(gradient),
        "high_density_regions": [f["position"] for f in field if f["inflation_mask"] == "expand"],
        "low_density_regions":  [f["position"] for f in field if f["inflation_mask"] == "contract"],
    }


# ── 3. GRADIENT TUNNEL ────────────────────────────────────────
def gradient_tunnel(
    loss_surface: List[float],
    noise_scale: float = 0.1,
    hessian_approx: bool = True
) -> Dict:
    """
    Gradient Tunneling Resonance (GTR):
    Injects stochastic resonance noise tuned to local Hessian eigenvalues
    to enable quantum-like tunneling across flat basins.
    
    Input:  sampled loss curve (1D slice through loss landscape)
    Output: tunneling update, escape paths, curvature spectrum
    """
    vals = np.array(loss_surface, dtype=float)
    n = len(vals)
    
    if n < 3:
        return {"perturbed": loss_surface, "tunneling_score": 0.0,
                "escape_paths": [], "curvature_spectrum": []}
    
    # Local curvature via second differences (Hessian approximation)
    curvature = np.zeros(n)
    for i in range(1, n-1):
        curvature[i] = vals[i+1] - 2*vals[i] + vals[i-1]  # Laplacian
    curvature[0] = curvature[1]
    curvature[-1] = curvature[-2]
    
    # Identify flat basins (low |curvature| + local minimum)
    gradient = np.gradient(vals)
    is_basin = (np.abs(gradient) < gradient.std() * 0.3) & (curvature > -0.01)
    
    # Stochastic resonance: noise amplitude ∝ 1/|λ_min|
    # Where λ_min = smallest curvature eigenvalue (flattest direction)
    eigenvalues = np.sort(np.abs(curvature))
    min_eig = eigenvalues[0] if eigenvalues[0] > 1e-8 else 1e-3
    
    # Resonance noise tuned to escape flat basins
    noise = np.random.normal(0, noise_scale / min_eig, n) * is_basin.astype(float)
    perturbed = vals + noise
    
    # Find escape paths: where tunneling noise exceeds barrier height
    escape_paths = []
    for i in range(1, n-1):
        if is_basin[i]:
            barrier = max(0, min(vals[max(0,i-3):i+1].max() - vals[i], 
                                  vals[i:min(n,i+4)].max() - vals[i]))
            if abs(noise[i]) > barrier * 0.5:
                escape_paths.append({
                    "position": i,
                    "barrier_height": float(barrier),
                    "noise_injected": float(noise[i]),
                    "escape_probability": float(min(1.0, abs(noise[i]) / (barrier + 1e-8)))
                })
    
    # Curvature spectrum
    spectrum = sorted(np.abs(curvature).tolist())
    
    return {
        "perturbed": perturbed.tolist(),
        "tunneling_score": float(np.abs(noise).mean()),
        "escape_paths": escape_paths[:10],  # top 10
        "curvature_spectrum": {"min": float(spectrum[0]), "max": float(spectrum[-1]),
                                "mean": float(sum(spectrum)/len(spectrum))},
        "basin_count": int(is_basin.sum()),
        "noise_scale_used": float(noise_scale / min_eig),
    }


# ── 4. CONTEXT HORIZON (EVENT HORIZON + HAWKING RADIATION) ────
def context_horizon(
    sequence: str,
    window_size: int = 512,
    radiation_dims: int = 32
) -> Dict:
    """
    Token Horizon Bifurcation (THB) + Context Event Horizons (CEH).
    
    Splits token states at context boundary into:
    - Interior state: causally accessible tokens (first window_size chars)
    - Hawking radiation: compressed entropy signature of "lost" tokens
    
    The radiation vector preserves thermodynamic information about
    context that crossed the event horizon.
    """
    tokens = list(sequence)
    n = len(tokens)
    
    # Define horizon at window_size
    interior = tokens[:window_size] if n > window_size else tokens
    exterior = tokens[window_size:] if n > window_size else []
    
    # Interior statistics
    interior_str = "".join(interior)
    int_counts = {}
    for t in interior:
        int_counts[t] = int_counts.get(t, 0) + 1
    int_total = len(interior)
    interior_entropy = -sum(
        (c/int_total)*math.log2(c/int_total)
        for c in int_counts.values() if c > 0
    ) if int_total > 0 else 0.0
    
    # Hawking radiation: compress exterior into radiation_dims-dimensional vector
    radiation = np.zeros(radiation_dims)
    if exterior:
        ext_str = "".join(exterior)
        
        # Encode exterior as multi-scale statistical signature
        # (compression ratio at multiple scales, bigram entropy, char distribution)
        n_ext = len(exterior)
        
        # Channel 1: compression ratio (K(x) bound)
        cr = len(zlib.compress(ext_str.encode(), level=9)) / max(len(ext_str.encode()), 1)
        radiation[0] = cr
        
        # Channel 2-6: char distribution moments
        ext_counts = {}
        for t in exterior:
            ext_counts[t] = ext_counts.get(t, 0) + 1
        freqs = sorted([c/n_ext for c in ext_counts.values()], reverse=True)
        for i, f in enumerate(freqs[:5]):
            radiation[1 + i] = f
        
        # Channel 7-11: n-gram entropies at n=2,3,4
        for ng in range(2, 5):
            ngrams = Counter(tuple(exterior[i:i+ng]) for i in range(n_ext-ng+1))
            total = sum(ngrams.values())
            h = -sum((c/total)*math.log2(c/total) for c in ngrams.values() if c > 0)
            radiation[6 + (ng-2)] = h / math.log2(max(len(ngrams), 2))
        
        # Channel 9-16: positional entropy (where is information densest?)
        chunk_size = max(1, n_ext // 8)
        for ci in range(min(8, radiation_dims - 9)):
            chunk = exterior[ci*chunk_size:(ci+1)*chunk_size]
            if chunk:
                cfreqs = Counter(chunk)
                ctot = len(chunk)
                ch = -sum((c/ctot)*math.log2(c/ctot) for c in cfreqs.values() if c>0)
                radiation[9 + ci] = ch
        
        # Fill remaining with zlib sub-block signatures
        for i in range(17, min(radiation_dims, 32)):
            sub_start = (i - 17) * max(1, n_ext // 15)
            sub = ext_str[sub_start:sub_start + 32]
            if sub:
                radiation[i] = len(zlib.compress(sub.encode())) / max(len(sub), 1)
    
    # Phase parameter θ: measures coherence between interior and radiation
    if exterior:
        int_cr = len(zlib.compress(interior_str.encode(), level=9)) / max(len(interior_str.encode()), 1)
        ext_cr = float(radiation[0])
        theta = math.atan2(ext_cr, int_cr)  # phase angle
    else:
        theta = 0.0
    
    return {
        "interior_length": len(interior),
        "exterior_length": len(exterior),
        "interior_entropy": interior_entropy,
        "radiation_vector": radiation.tolist(),
        "radiation_norm": float(np.linalg.norm(radiation)),
        "phase_theta": theta,
        "information_retention": 1.0 - (len(exterior) / max(n, 1)),
        "bifurcation_active": len(exterior) > 0,
        "hawking_temperature": float(radiation[0]) if len(exterior) > 0 else 0.0,
    }


# ── 5. ISOMORPHISM FINGERPRINT ────────────────────────────────
# (re-exported for use in the main API, backed by math_invariants.py)
def compute_isomorphism(domain_a: str, domain_b: str) -> Dict:
    """Full isomorphism computation with all components."""
    from lib.math_invariants import fingerprint, similarity
    fa = fingerprint(domain_a)
    fb = fingerprint(domain_b)
    score, va, vb = similarity(fa, fb)
    return {
        "similarity": float(score),
        "vector_a": va.tolist(),
        "vector_b": vb.tolist(),
        "breakdown": {
            "compression_a": fa["compression"],
            "compression_b": fb["compression"],
            "compression_similarity": 1.0 - abs(fa["compression"] - fb["compression"]),
            "mi_a": fa["mi"],
            "mi_b": fb["mi"],
            "lambda2_a": fa["lambda2"],
            "lambda2_b": fb["lambda2"],
            "lambda2_similarity": 1.0 / (1.0 + abs(fa["lambda2"] - fb["lambda2"])),
            "entropy_a": fa["entropy"],
            "entropy_b": fb["entropy"],
        }
    }
