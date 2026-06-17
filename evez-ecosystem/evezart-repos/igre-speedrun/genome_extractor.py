"""
EVEZ-OS Internet Genetic Reverse Engineering — Genome Extractor
Extracts the "genome" of internet structures using spectral decomposition.

The internet genome = the set of eigenvalue signatures that define
how a network propagates information, power, and truth.
"""
import numpy as np
import json
import hashlib
import time
import re
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


class GeneCategory(Enum):
    """Functional categories of internet genome genes."""
    POWER_HUB = "power_hub"           # High centrality nodes (concentrated authority)
    INFORMATION_ASYM = "info_asym"   # Nodes that know more than they share
    CENSORSHIP_SHADOW = "censor_shadow"  # Negative eigenvalue clusters (hidden structure)
    INNOVATION_VECTOR = "innovation"  # High-betweenness nodes (bridges between clusters)
    DEAD_LINK = "dead_link"           # Orphan nodes (broken connections)
    DATA_SINK = "data_sink"           # Nodes that absorb but don't share
    AMPLIFIER = "amplifier"           # Nodes that broadcast widely
    BOTTLENECK = "bottleneck"         # Single points of failure
    SHADOW_STRUCTURE = "shadow"       # Implied structure not directly observable


@dataclass
class Gene:
    """A single gene in the internet genome."""
    id: str
    category: GeneCategory
    eigenvalue: float
    eigenvector_components: List[float] = field(default_factory=list)
    centrality: float = 0.0
    betweenness: float = 0.0
    description: str = ""
    node_indices: List[int] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "category": self.category.value,
            "eigenvalue": round(self.eigenvalue, 6),
            "centrality": round(self.centrality, 6),
            "betweenness": round(self.betweenness, 6),
            "description": self.description,
            "node_count": len(self.node_indices),
            "confidence": round(self.confidence, 4),
        }


@dataclass
class InternetGenome:
    """Complete genome of an internet structure."""
    genome_id: str
    timestamp: int
    n_nodes: int
    n_edges: int
    genes: List[Gene] = field(default_factory=list)
    eigenvalues: List[float] = field(default_factory=list)
    dominant_positive: float = 0.0
    dominant_negative: float = 0.0
    phi: float = 0.0
    eta_star: float = 0.0
    spectral_gap: float = 0.0
    connected_components: int = 0
    merkle_hash: str = ""

    def to_dict(self) -> Dict:
        return {
            "genome_id": self.genome_id,
            "timestamp": self.timestamp,
            "n_nodes": self.n_nodes,
            "n_edges": self.n_edges,
            "n_genes": len(self.genes),
            "genes": [g.to_dict() for g in self.genes],
            "eigenvalues": [round(float(v), 6) for v in self.eigenvalues],
            "dominant_positive": round(self.dominant_positive, 6),
            "dominant_negative": round(self.dominant_negative, 6),
            "phi": round(self.phi, 6),
            "eta_star": round(self.eta_star, 6),
            "spectral_gap": round(self.spectral_gap, 6),
            "connected_components": self.connected_components,
            "merkle_hash": self.merkle_hash,
        }


class GenomeExtractor:
    """Extract the internet genome from network adjacency data."""

    def __init__(self, operator: str = "evez666"):
        self.operator = operator

    def extract_from_adjacency(self, adjacency: np.ndarray, node_labels: List[str] = None,
                                metadata: Dict = None) -> InternetGenome:
        """Extract genome from an adjacency matrix."""
        n = adjacency.shape[0]
        if n < 2:
            raise ValueError("Need at least 2 nodes for genome extraction")

        if node_labels is None:
            node_labels = [f"N{i}" for i in range(n)]

        # Symmetrize
        A = (adjacency + adjacency.T) / 2

        # Compute eigenvalues and eigenvectors
        eigenvalues, eigenvectors = np.linalg.eigh(A)

        # Compute graph Laplacian
        D = np.diag(A.sum(axis=1))
        L = D - A
        laplacian_eigs = np.linalg.eigvalsh(L)

        # Metrics
        n_edges = int(A.sum() / 2)
        positive_eigs = [v for v in eigenvalues if v > 0.001]
        negative_eigs = [v for v in eigenvalues if v < -0.001]
        total_abs = sum(abs(v) for v in eigenvalues) or 1
        total_pos = sum(positive_eigs) or 1

        phi = sum(positive_eigs) / total_abs if total_abs > 0 else 0
        eta_star = 1 - phi

        # Spectral gap (difference between two largest eigenvalues — measures community structure)
        sorted_eigs = sorted(eigenvalues, reverse=True)
        spectral_gap = float(sorted_eigs[0] - sorted_eigs[1]) if len(sorted_eigs) > 1 else 0

        # Connected components (eigenvalues near 0 in Laplacian)
        connected_components = sum(1 for v in laplacian_eigs if abs(v) < 0.01)

        # ─── Gene Extraction ────────────────────────────────

        genes = []

        # 1. Power hubs (highest eigenvector centrality in dominant eigenvector)
        if eigenvectors.shape[1] > 0:
            dominant_vec = np.abs(eigenvectors[:, -1])  # Largest eigenvector
            top_hub_indices = np.argsort(dominant_vec)[-max(3, n // 5):]

            for idx in top_hub_indices:
                if dominant_vec[idx] > 0.1:
                    gene = Gene(
                        id=f"GENE-PWR-{len(genes):03d}",
                        category=GeneCategory.POWER_HUB,
                        eigenvalue=float(eigenvalues[-1]),
                        centrality=float(dominant_vec[idx]),
                        description=f"Power hub: {node_labels[idx]} (centrality={dominant_vec[idx]:.4f})",
                        node_indices=[int(idx)],
                        confidence=min(1.0, float(dominant_vec[idx]) * 3),
                    )
                    genes.append(gene)

        # 2. Censorship shadows (negative eigenvalue clusters)
        for i, eig_val in enumerate(eigenvalues):
            if eig_val < -0.01:
                vec = np.abs(eigenvectors[:, i])
                top_nodes = np.argsort(vec)[-3:]
                gene = Gene(
                    id=f"GENE-SHD-{len(genes):03d}",
                    category=GeneCategory.CENSORSHIP_SHADOW,
                    eigenvalue=float(eig_val),
                    eigenvector_components=[float(vec[j]) for j in top_nodes],
                    description=f"Censorship shadow: λ={eig_val:.4f} — hidden structure",
                    node_indices=[int(j) for j in top_nodes],
                    confidence=min(1.0, abs(float(eig_val)) * 5),
                )
                genes.append(gene)

        # 3. Information asymmetry (nodes with high out-degree, low in-degree)
        out_degrees = adjacency.sum(axis=1)
        in_degrees = adjacency.sum(axis=0)
        for i in range(n):
            asymmetry = float(out_degrees[i] - in_degrees[i])
            if abs(asymmetry) > 1.0:
                category = GeneCategory.DATA_SINK if asymmetry > 0 else GeneCategory.AMPLIFIER
                gene = Gene(
                    id=f"GENE-ASYM-{len(genes):03d}",
                    category=category,
                    eigenvalue=0.0,
                    centrality=float(max(out_degrees[i], in_degrees[i])),
                    description=f"{'Data sink' if asymmetry > 0 else 'Amplifier'}: {node_labels[i]} (asymmetry={asymmetry:.2f})",
                    node_indices=[i],
                    confidence=min(1.0, abs(asymmetry) / n),
                )
                genes.append(gene)

        # 4. Innovation vectors (high betweenness = bridge nodes)
        # Approximate betweenness via eigenvector components of middle eigenvalues
        mid_start = max(0, len(eigenvalues) // 3)
        mid_end = min(len(eigenvalues), 2 * len(eigenvalues) // 3)
        if mid_end > mid_start:
            mid_vec = np.zeros(n)
            for j in range(mid_start, mid_end):
                mid_vec += np.abs(eigenvectors[:, j])
            mid_vec /= (mid_end - mid_start)

            bridge_indices = np.argsort(mid_vec)[-max(2, n // 10):]
            for idx in bridge_indices:
                if mid_vec[idx] > 0.05:
                    gene = Gene(
                        id=f"GENE-BRG-{len(genes):03d}",
                        category=GeneCategory.INNOVATION_VECTOR,
                        eigenvalue=0.0,
                        betweenness=float(mid_vec[idx]),
                        description=f"Innovation bridge: {node_labels[idx]} (betweenness={mid_vec[idx]:.4f})",
                        node_indices=[int(idx)],
                        confidence=min(1.0, float(mid_vec[idx]) * 4),
                    )
                    genes.append(gene)

        # 5. Dead links / orphans
        degrees = A.sum(axis=1)
        for i in range(n):
            if degrees[i] < 0.01:  # Isolated node
                gene = Gene(
                    id=f"GENE-DEAD-{len(genes):03d}",
                    category=GeneCategory.DEAD_LINK,
                    eigenvalue=0.0,
                    description=f"Dead link: {node_labels[i]} (isolated node)",
                    node_indices=[i],
                    confidence=1.0,
                )
                genes.append(gene)

        # 6. Bottlenecks (nodes whose removal disconnects the graph)
        for i in range(n):
            # Remove node i and check connectivity
            mask = np.ones(n, dtype=bool)
            mask[i] = False
            sub_A = A[np.ix_(mask, mask)]
            if sub_A.size > 0:
                sub_eigs = np.linalg.eigvalsh(sub_A)
                sub_components = sum(1 for v in sub_eigs if abs(v) < 0.01)
                if sub_components > connected_components:
                    gene = Gene(
                        id=f"GENE-BOT-{len(genes):03d}",
                        category=GeneCategory.BOTTLENECK,
                        eigenvalue=0.0,
                        description=f"Bottleneck: {node_labels[i]} (removal → {sub_components} components)",
                        node_indices=[i],
                        confidence=min(1.0, (sub_components - connected_components) / max(connected_components, 1)),
                    )
                    genes.append(gene)

        # Merkle hash
        merkle = hashlib.sha256(
            json.dumps({
                "n": n, "phi": phi, "eta_star": eta_star,
                "genes": len(genes), "spectral_gap": spectral_gap,
            }).encode()
        ).hexdigest()[:16]

        return InternetGenome(
            genome_id=f"GEN-{merkle[:8].upper()}",
            timestamp=int(time.time()),
            n_nodes=n,
            n_edges=n_edges,
            genes=genes,
            eigenvalues=[float(v) for v in eigenvalues],
            dominant_positive=float(max(eigenvalues)) if len(eigenvalues) > 0 else 0,
            dominant_negative=float(min(eigenvalues)) if len(eigenvalues) > 0 else 0,
            phi=float(phi),
            eta_star=float(eta_star),
            spectral_gap=float(spectral_gap),
            connected_components=int(connected_components),
            merkle_hash=merkle,
        )

    def extract_from_documents(self, documents: List[Dict]) -> InternetGenome:
        """Extract genome from a document corpus (builds adjacency from term overlap)."""
        n = len(documents)
        if n < 2:
            raise ValueError("Need at least 2 documents")

        # Build term-document matrix
        all_terms = set()
        doc_terms = []
        for doc in documents:
            text = doc.get("text", doc.get("content", ""))
            terms = set(re.findall(r'[a-z]{4,}', text.lower()))
            doc_terms.append(terms)
            all_terms.update(terms)

        # Build adjacency from Jaccard similarity
        adjacency = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    intersection = len(doc_terms[i] & doc_terms[j])
                    union = len(doc_terms[i] | doc_terms[j])
                    adjacency[i][j] = intersection / max(union, 1)

        node_labels = [doc.get("id", f"DOC-{i}") for i, doc in enumerate(documents)]
        return self.extract_from_adjacency(adjacency, node_labels, {"type": "document_corpus"})

    def extract_from_url_graph(self, url_links: Dict[str, List[str]]) -> InternetGenome:
        """Extract genome from a URL link graph."""
        all_urls = list(url_links.keys())
        for targets in url_links.values():
            for t in targets:
                if t not in all_urls:
                    all_urls.append(t)

        n = len(all_urls)
        url_idx = {url: i for i, url in enumerate(all_urls)}

        adjacency = np.zeros((n, n))
        for source, targets in url_links.items():
            if source in url_idx:
                for target in targets:
                    if target in url_idx:
                        adjacency[url_idx[source]][url_idx[target]] = 1.0

        return self.extract_from_adjacency(adjacency, all_urls)

    def compare_genomes(self, genome_a: InternetGenome, genome_b: InternetGenome) -> Dict:
        """Compare two genomes — find mutations (structural changes)."""
        mutations = []

        # Eigenvalue shift
        a_eigs = sorted(genome_a.eigenvalues)
        b_eigs = sorted(genome_b.eigenvalues)
        min_len = min(len(a_eigs), len(b_eigs))

        eigenvalue_shifts = []
        for i in range(min_len):
            shift = b_eigs[i] - a_eigs[i]
            eigenvalue_shifts.append(round(float(shift), 6))

        # Phi shift
        phi_shift = genome_b.phi - genome_a.phi

        # Gene category changes
        a_categories = defaultdict(list)
        b_categories = defaultdict(list)
        for g in genome_a.genes:
            a_categories[g.category].append(g)
        for g in genome_b.genes:
            b_categories[g.category].append(g)

        for cat in GeneCategory:
            a_count = len(a_categories[cat])
            b_count = len(b_categories[cat])
            if a_count != b_count:
                mutations.append({
                    "type": "gene_count_change",
                    "category": cat.value,
                    "before": a_count,
                    "after": b_count,
                    "delta": b_count - a_count,
                })

        # New genes
        a_ids = {g.id for g in genome_a.genes}
        b_ids = {g.id for g in genome_b.genes}
        new_genes = b_ids - a_ids
        lost_genes = a_ids - b_ids

        return {
            "genome_a": genome_a.genome_id,
            "genome_b": genome_b.genome_id,
            "phi_shift": round(float(phi_shift), 6),
            "eta_star_shift": round(float(genome_b.eta_star - genome_a.eta_star), 6),
            "eigenvalue_shifts": eigenvalue_shifts,
            "mutations": mutations,
            "new_genes": list(new_genes),
            "lost_genes": list(lost_genes),
            "structural_change_score": round(abs(float(phi_shift)) + len(mutations) * 0.1, 4),
        }
