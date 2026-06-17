"""Eigenforensics spectral decomposition engine for FOIA document gap analysis.

Built by Steven Crawford-Maggard (EVEZ666) — https://github.com/EvezArt

Core concept: Documents form a reference graph. Structural holes (missing records,
redactions, deliberate omissions) appear as NEGATIVE EIGENVALUES in the graph's
spectral decomposition. We map those eigenvalues to probable gap locations.
"""

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import json

# Universal incompleteness constant (η*) — recurs across EVEZ research
ETA_STAR = 0.03


@dataclass
class GapReport:
    doc_name: str
    total_nodes: int
    negative_eigenvalues: List[float]
    gap_score: float  # 0.0 (complete) to 1.0 (maximally incomplete)
    gap_locations: List[str]  # probable missing sections
    meme_trigger: bool  # True if gap_score exceeds meme threshold
    raw_eigenvalues: List[float] = field(default_factory=list)

    def to_dict(self):
        return {
            "doc_name": self.doc_name,
            "total_nodes": self.total_nodes,
            "negative_eigenvalues": self.negative_eigenvalues,
            "gap_score": round(self.gap_score, 4),
            "gap_locations": self.gap_locations,
            "meme_trigger": self.meme_trigger,
        }


def build_reference_graph(sections: List[str], references: List[Tuple[int, int]]) -> np.ndarray:
    """Build adjacency matrix from document sections and their cross-references."""
    n = len(sections)
    adj = np.zeros((n, n))
    for i, j in references:
        adj[i][j] = 1
        adj[j][i] = 1  # symmetric
    return adj


def compute_laplacian(adj: np.ndarray) -> np.ndarray:
    """Compute the graph Laplacian: L = D - A"""
    degree = np.diag(adj.sum(axis=1))
    return degree - adj


def detect_gaps(laplacian: np.ndarray, doc_name: str, sections: List[str]) -> GapReport:
    """Run spectral decomposition and extract gap signature."""
    n = laplacian.shape[0]
    # Compute all eigenvalues
    eigenvalues = np.linalg.eigvalsh(laplacian)
    
    # Negative eigenvalues = structural incompleteness
    negative_eigs = sorted([float(e) for e in eigenvalues if e < -1e-10])
    
    # Gap score: proportion of negative eigenvalues, weighted by magnitude
    if len(negative_eigs) == 0:
        gap_score = 0.0
    else:
        gap_score = min(1.0, abs(sum(negative_eigs)) / (n * ETA_STAR + 1e-10))
    
    # Heuristic: map extreme negative eigenvalue positions to sections
    gap_locations = []
    if negative_eigs:
        # Sections with lowest row-sum in Laplacian are likely gap boundary nodes
        row_sums = laplacian.sum(axis=1)
        gap_indices = np.argsort(row_sums)[:len(negative_eigs)]
        gap_locations = [sections[i] for i in gap_indices if i < len(sections)]
    
    return GapReport(
        doc_name=doc_name,
        total_nodes=n,
        negative_eigenvalues=negative_eigs,
        gap_score=gap_score,
        gap_locations=gap_locations,
        meme_trigger=gap_score > 0.15,  # 15% threshold triggers meme factory
        raw_eigenvalues=[float(e) for e in eigenvalues],
    )


def analyze_document(doc_path: str) -> GapReport:
    """Main entry: load processed doc JSON and run gap detection."""
    with open(doc_path) as f:
        doc = json.load(f)
    
    sections = doc.get("sections", [])
    references = [tuple(r) for r in doc.get("references", [])]
    
    if not sections:
        raise ValueError(f"No sections found in {doc_path}")
    
    adj = build_reference_graph(sections, references)
    laplacian = compute_laplacian(adj)
    return detect_gaps(laplacian, doc.get("name", doc_path), sections)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        report = analyze_document(sys.argv[1])
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print("Usage: python spectral.py <doc.json>")
        print("\nExample doc format:")
        example = {
            "name": "AARO_2024_Q1_Release",
            "sections": ["Executive Summary", "Case Files", "Appendix A", "Witness Reports"],
            "references": [[0, 1], [1, 2], [0, 3]]  # cross-reference pairs
        }
        print(json.dumps(example, indent=2))
