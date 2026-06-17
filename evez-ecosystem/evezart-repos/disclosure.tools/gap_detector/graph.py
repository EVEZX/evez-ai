"""
Reference graph builder for disclosure.tools
Constructs document-level and cross-document reference graphs
for spectral gap analysis.
"""
import numpy as np
import re
import hashlib
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ReferenceNode:
    """A node in the document reference graph."""
    id: str
    doc_id: str
    section_idx: int
    section_title: str
    text_snippet: str  # first 200 chars
    keywords: Set[str] = field(default_factory=set)
    references_out: List[str] = field(default_factory=list)  # node IDs this references
    references_in: List[str] = field(default_factory=list)   # node IDs referencing this


@dataclass
class ReferenceGraph:
    """Complete reference graph across documents."""
    nodes: Dict[str, ReferenceNode] = field(default_factory=dict)
    adjacency: Optional[np.ndarray] = None
    _index_map: Dict[str, int] = field(default_factory=dict)

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

    def add_node(self, node: ReferenceNode):
        self.nodes[node.id] = node

    def add_edge(self, from_id: str, to_id: str):
        if from_id in self.nodes and to_id in self.nodes:
            if to_id not in self.nodes[from_id].references_out:
                self.nodes[from_id].references_out.append(to_id)
            if from_id not in self.nodes[to_id].references_in:
                self.nodes[to_id].references_in.append(from_id)

    def build_adjacency(self) -> np.ndarray:
        """Build weighted adjacency matrix from reference graph."""
        n = len(self.nodes)
        if n == 0:
            return np.zeros((0, 0))

        self._index_map = {node_id: i for i, node_id in enumerate(self.nodes)}
        self.adjacency = np.zeros((n, n))

        for node_id, node in self.nodes.items():
            i = self._index_map[node_id]
            # Explicit references
            for ref_id in node.references_out:
                if ref_id in self._index_map:
                    j = self._index_map[ref_id]
                    self.adjacency[i][j] = 1.0
                    self.adjacency[j][i] = 1.0  # symmetric

            # Keyword overlap (implicit references)
            for other_id, other_node in self.nodes.items():
                if other_id == node_id:
                    continue
                overlap = len(node.keywords & other_node.keywords)
                if overlap > 0:
                    j = self._index_map[other_id]
                    weight = min(overlap / 10.0, 1.0)  # cap at 1.0
                    self.adjacency[i][j] = max(self.adjacency[i][j], weight * 0.5)

        return self.adjacency

    def compute_laplacian(self) -> np.ndarray:
        """Compute graph Laplacian: L = D - A"""
        if self.adjacency is None:
            self.build_adjacency()
        degree = np.diag(self.adjacency.sum(axis=1))
        return degree - self.adjacency

    def find_orphan_nodes(self) -> List[str]:
        """Find nodes with no references (potential gaps or isolated records)."""
        orphans = []
        for node_id, node in self.nodes.items():
            if not node.references_out and not node.references_in:
                orphans.append(node_id)
        return orphans

    def find_dangling_refs(self) -> List[Tuple[str, str]]:
        """Find references that point to non-existent nodes (structural gaps)."""
        danglers = []
        for node_id, node in self.nodes.items():
            for ref_id in node.references_out:
                if ref_id not in self.nodes:
                    danglers.append((node_id, ref_id))
        return danglers

    def to_dict(self) -> Dict:
        return {
            "n_nodes": self.n_nodes,
            "n_edges": sum(len(n.references_out) for n in self.nodes.values()),
            "orphan_nodes": self.find_orphan_nodes(),
            "dangling_references": self.find_dangling_refs(),
        }


def _extract_keywords(text: str, max_keywords: int = 20) -> Set[str]:
    """Extract meaningful keywords from text."""
    # Stop words for FOIA/government documents
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "shall", "can", "this", "that",
        "these", "those", "it", "its", "not", "no", "nor", "as", "if", "then",
        "than", "too", "very", "also", "just", "more", "most", "such", "only",
        "which", "what", "when", "where", "who", "whom", "how", "all", "each",
        "every", "both", "few", "some", "any", "other", "into", "over", "after",
        "before", "about", "between", "through", "during", "without", "upon",
        "per", "via", "etc", "however", "therefore", "thus", "hence",
    }

    # Tokenize and filter
    words = re.findall(r'[A-Za-z]{3,}', text.lower())
    keywords = set()
    freq = defaultdict(int)

    for w in words:
        if w not in stop_words and len(w) >= 4:
            freq[w] += 1

    # Take top keywords by frequency
    sorted_words = sorted(freq.items(), key=lambda x: -x[1])
    for word, count in sorted_words[:max_keywords]:
        if count >= 2:  # must appear at least twice
            keywords.add(word)

    return keywords


def build_document_graph(documents: List[Dict]) -> ReferenceGraph:
    """Build a reference graph from a list of ingested documents.

    Each document should have: id, sections (list of strings), references (optional)
    """
    graph = ReferenceGraph()
    all_nodes = []

    # Create nodes from document sections
    for doc in documents:
        doc_id = doc.get("id", "unknown")
        sections = doc.get("sections", [])
        text = doc.get("text", "")

        if not sections and text:
            # Split text into sections
            sections = [p.strip() for p in text.split("\n\n") if p.strip()]

        for idx, section in enumerate(sections):
            node_id = f"{doc_id}::S{idx}"
            snippet = section[:200]
            keywords = _extract_keywords(section)
            title = section.split("\n")[0][:80] if section else f"Section {idx}"

            node = ReferenceNode(
                id=node_id,
                doc_id=doc_id,
                section_idx=idx,
                section_title=title,
                text_snippet=snippet,
                keywords=keywords,
            )
            graph.add_node(node)
            all_nodes.append(node)

    # Build cross-references based on keyword overlap and explicit references
    node_list = list(graph.nodes.values())
    for i, node_a in enumerate(node_list):
        for j, node_b in enumerate(node_list):
            if i >= j:
                continue
            # Skip intra-document connections (handled separately)
            if node_a.doc_id == node_b.doc_id:
                if abs(node_a.section_idx - node_b.section_idx) == 1:
                    graph.add_edge(node_a.id, node_b.id)
                continue

            # Cross-document: keyword overlap
            overlap = len(node_a.keywords & node_b.keywords)
            if overlap >= 3:
                graph.add_edge(node_a.id, node_b.id)

    # Apply explicit references from documents
    for doc in documents:
        doc_id = doc.get("id", "unknown")
        refs = doc.get("references", [])
        for ref in refs:
            if isinstance(ref, (list, tuple)) and len(ref) >= 2:
                src_idx, tgt_idx = ref[0], ref[1]
                src_node = f"{doc_id}::S{src_idx}"
                # Find target — could be same doc or different
                tgt_node = f"{doc_id}::S{tgt_idx}"
                graph.add_edge(src_node, tgt_node)

    return graph


def build_corpus_graph(documents: List[Dict]) -> ReferenceGraph:
    """Build a document-level graph (one node per document, not per section)."""
    graph = ReferenceGraph()

    for doc in documents:
        doc_id = doc.get("id", "unknown")
        text = doc.get("text", "")
        keywords = _extract_keywords(text)

        node = ReferenceNode(
            id=doc_id,
            doc_id=doc_id,
            section_idx=0,
            section_title=doc.get("title", doc_id),
            text_snippet=text[:200],
            keywords=keywords,
        )
        graph.add_node(node)

    # Cross-reference by keyword overlap
    node_list = list(graph.nodes.values())
    for i, node_a in enumerate(node_list):
        for j, node_b in enumerate(node_list):
            if i >= j:
                continue
            overlap = len(node_a.keywords & node_b.keywords)
            if overlap >= 2:
                graph.add_edge(node_a.id, node_b.id)

    return graph
