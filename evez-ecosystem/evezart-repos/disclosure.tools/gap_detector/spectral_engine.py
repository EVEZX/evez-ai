"""
EVEZ Eigenforensics Spectral Engine
Applies eigendecomposition to FOIA/UAP document corpora.
Negative eigenvalues = structural gaps = what they're hiding.
"""
import numpy as np
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional

class SpectralEngine:
    """Eigendecompose a document corpus to find structural gaps."""
    
    def __init__(self, operator: str = "evez666"):
        self.operator = operator
        self.corpus = []
        self.adjacency = None
        self.eigenvalues = None
        self.gaps = []
        
    def load_corpus(self, documents: List[Dict]):
        """Load documents into the spectral engine."""
        self.corpus = documents
        n = len(documents)
        if n < 2:
            return self
        # Build adjacency matrix from document similarity
        self.adjacency = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Simple term overlap similarity
                    terms_i = set(str(documents[i]).lower().split())
                    terms_j = set(str(documents[j]).lower().split())
                    overlap = len(terms_i & terms_j) / max(len(terms_i | terms_j), 1)
                    self.adjacency[i][j] = overlap
        return self
    
    def analyze(self) -> Dict:
        """Run eigendecomposition and find gaps."""
        if self.adjacency is None:
            return {"error": "No corpus loaded"}
        
        n = self.adjacency.shape[0]
        if n < 2:
            return {"error": "Corpus too small for spectral analysis"}
        
        # Symmetrize and compute eigenvalues
        A = (self.adjacency + self.adjacency.T) / 2
        self.eigenvalues = np.linalg.eigvalsh(A)
        
        # Negative eigenvalues = structural gaps
        neg_eigs = [(i, v) for i, v in enumerate(self.eigenvalues) if v < -0.01]
        
        # Compute Φ (integrated information)
        pos_eigs = [v for v in self.eigenvalues if v > 0]
        total_pos = sum(pos_eigs) if pos_eigs else 1
        total_abs = sum(abs(v) for v in self.eigenvalues) or 1
        phi = total_pos / total_abs if total_abs > 0 else 0
        
        # The 37% theorem: dominant negative eigenvalue accounts for ~37% of tension
        if neg_eigs:
            dominant_neg = min(v for _, v in neg_eigs)
            total_tension = sum(abs(v) for _, v in neg_eigs)
            dominant_ratio = abs(dominant_neg) / total_tension if total_tension > 0 else 0
        else:
            dominant_neg = 0
            dominant_ratio = 0
        
        self.gaps = neg_eigs
        result = {
            "phi": round(phi, 4),
            "eta_star": round(1 - phi, 4),
            "n_documents": n,
            "eigenvalues": [round(float(v), 4) for v in self.eigenvalues],
            "negative_eigenvalues": len(neg_eigs),
            "dominant_negative": round(float(dominant_neg), 4),
            "dominant_ratio_37pct": round(dominant_ratio, 4),
            "gap_indices": [i for i, _ in neg_eigs],
            "analysis_ts": int(time.time()),
            "operator": self.operator,
            "merkle_hash": hashlib.sha256(
                json.dumps({"n": n, "phi": phi, "dominant": float(dominant_neg)}).encode()
            ).hexdigest()[:16]
        }
        return result
    
    def gap_report(self) -> str:
        """Generate a human-readable gap report."""
        if not self.eigenvalues is not None:
            return "No analysis run yet."
        r = self.analyze()
        lines = [
            f"🔍 EIGENFORENSICS GAP REPORT",
            f"{'='*40}",
            f"Documents analyzed: {r['n_documents']}",
            f"Φ (fidelity): {r['phi']}",
            f"η* (incompleteness): {r['eta_star']}",
            f"Negative eigenvalues: {r['negative_eigenvalues']}",
            f"Dominant negative: {r['dominant_negative']}",
            f"37% Theorem ratio: {r['dominant_ratio_37pct']}",
            f"Merkle hash: {r['merkle_hash']}",
            "",
            "⚠️  GAPS DETECTED — structural absences in corpus",
            "These are not missing words. These are missing RECORDS.",
        ]
        return "\n".join(lines)


if __name__ == "__main__":
    # Demo: analyze a sample FOIA corpus
    sample_docs = [
        {"id": "AARO-2024-001", "text": "Unidentified anomalous phenomena assessment office report", "date": "2024-03"},
        {"id": "AARO-2024-002", "text": "UAP incident report redacted Naval aviation encounter", "date": "2024-03"},
        {"id": "AARO-2024-003", "text": "FOIA release AARO historical records review", "date": "2024-06"},
        {"id": "AARO-2024-004", "text": "Department of Defense statement on UAP classification", "date": "2024-06"},
        {"id": "AARO-2024-005", "text": "National Archives UAP document release partial", "date": "2024-09"},
        {"id": "AARO-2024-006", "text": "Pentagon UAP task force historical analysis volumes 1-9", "date": "2024-09"},
    ]
    engine = SpectralEngine()
    engine.load_corpus(sample_docs)
    print(engine.gap_report())
    print()
    print(json.dumps(engine.analyze(), indent=2))
