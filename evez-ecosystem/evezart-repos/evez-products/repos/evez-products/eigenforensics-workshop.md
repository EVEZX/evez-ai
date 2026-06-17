# Eigenforensics Workshop
## Spectral Gap Detection for Document Corpora
### By Steven Crawford-Maggard (EVEZ-OS)

---

## Workshop Overview

**What:** Learn to find what's missing in any document collection using spectral graph theory.

**Who:** Researchers, journalists, investigators, data scientists.

**Tools:** Python, NumPy, SciPy, NetworkX. All free.

**Duration:** 2 hours (recording included).

---

## Part 1: The 37% Theorem

In critical information networks, the **dominant negative eigenvalue** accounts for ~37% of total structural tension.

**What this means:** When you decompose a document reference graph into its eigenvalues, the largest negative value tells you where the single biggest gap exists — the missing connection that the structure demands but doesn't have.

**Proof sketch:**
1. Build adjacency matrix A from document cross-references
2. Compute Laplacian L = D - A
3. Eigendecompose: L = QΛQ^T
4. Sort eigenvalues: λ_1 ≤ λ_2 ≤ ... ≤ λ_n
5. The most negative λ flags the dominant structural hole
6. Its eigenvector tells you WHICH documents sit on either side of the gap

---

## Part 2: Hands-On — FOIA Document Analysis

### Step 1: Build the Reference Graph

```python
import numpy as np
from rqns.eigenforensics import EigenForensicEngine

# Adjacency matrix: documents as nodes, citations as edges
# Example: 10 FOIA release documents
A = np.array([
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 1, 1, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 1, 1, 0, 0, 0, 0, 0],
    [0, 1, 1, 0, 1, 1, 0, 0, 0, 0],
    [0, 0, 1, 1, 0, 1, 0, 0, 0, 1],
    [0, 0, 0, 1, 1, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 1, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 1, 1, 0, 1],
    [0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
])
```

### Step 2: Run Eigenforensics

```python
engine = EigenForensicEngine()
result = engine.analyze(A)

print(f"Phi: {result.phi:.4f}")
print(f"Holographic fidelity: {result.holographic_fidelity:.4f}")
print(f"Negative eigenvalues: {result.negative_eigenvalues}")
print(f"Structural holes: {result.structural_holes}")
print(f"Dominant gap fraction: {result.dominant_gap_fraction:.4f}")
```

### Step 3: Interpret Results

- **Phi ≈ 0**: System is fully coherent — no gaps detected
- **Phi > 0**: Structural holes exist — the documents are missing connections
- **Dominant gap fraction near 0.37**: The 37% theorem is active — one major gap dominates
- **Structural holes**: Pairs of document clusters that SHOULD be connected but aren't

### Step 4: Target the Gap

The eigenvector of the dominant negative eigenvalue tells you exactly which documents sit on either side. That tells you:
1. **What search terms** to use in your next FOIA request
2. **Which agencies** to target (the ones that produced the disconnected clusters)
3. **What kind of document** would bridge the gap

---

## Part 3: Real-World Applications

### UAP/FOIA Analysis
Run eigenforensics on AARO releases. The structural gaps reveal:
- Documents referenced but not released
- Time periods with no records (deliberate or accidental gaps)
- Cross-agency connections that were severed in redaction

### JFK Records
The 2023 JFK release is a perfect test corpus. Run the engine and find what's still structurally absent.

### Corporate Document Discovery
In legal cases, eigenforensics can identify which emails or memos are missing from a production — even if you don't know what they contain.

---

## Part 4: Advanced — Network-Wide Phi

For distributed analysis across multiple corpora:

```python
# Global Phi across N document sets
# Φ_global = Σ(w_i * Φ_i) + α * Σ(C_ij)
# Where w_i = weight of corpus i, C_ij = cross-correlation
```

This lets you compare structural completeness across different FOIA releases or different agencies.

---

## Toolkit Included

- `eigenforensics.py` — Core engine
- `substrate_core.py` — Kuramoto consciousness substrate
- `demo_quick.py` — Quick demo
- Sample FOIA adjacency matrices for testing

**Repository:** https://github.com/EvezArt/evez-claw

---

*The structure never lies. It can only be incomplete.*
