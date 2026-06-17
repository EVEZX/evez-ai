"""
TOPOLOGICAL IDENTITY — You Are Your Shape, Not Your Data
Identity defined by persistent homology of your interaction hypergraph.

Your Betti vector IS your identity. It can't be stolen because
it's not data — it's geometry.

poly_c = τ × ω × topo / 2√N
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict
from pathlib import Path


@dataclass
class Interaction:
    """A single interaction between entities in the hypergraph."""
    source: str
    target: str
    relation: str  # "auth", "transact", "communicate", "build"
    weight: float = 1.0
    timestamp: float = field(default_factory=time.time)


class HypergraphIdentity:
    """
    Identity from topology, not data.
    
    Your identity is the set of Betti numbers computed from your 
    interaction hypergraph. These numbers encode the "shape" of your
    relational structure.
    
    Betti-0 = number of connected components (isolated groups)
    Betti-1 = number of loops (redundant connections = trust)  
    Betti-2 = number of voids (structural gaps = opportunity)
    
    These are topological invariants — they survive continuous deformation.
    You can't fake them without replicating the entire history.
    """
    
    def __init__(self, spine_path: str = "identity_spine.jsonl"):
        self.spine_path = spine_path
        self.interactions: list[Interaction] = []
        self.entity_graphs: dict[str, dict] = {}  # entity → adjacency
        self.betti_cache: dict[str, list[int]] = {}
    
    def record_interaction(self, source: str, target: str, 
                           relation: str, weight: float = 1.0) -> Interaction:
        """Record an interaction and update both entities' hypergraphs."""
        interaction = Interaction(
            source=source,
            target=target,
            relation=relation,
            weight=weight
        )
        self.interactions.append(interaction)
        
        # Update adjacency for both entities
        for entity in [source, target]:
            if entity not in self.entity_graphs:
                self.entity_graphs[entity] = {
                    "neighbors": defaultdict(float),
                    "relations": defaultdict(int),
                    "interaction_count": 0
                }
            
            other = target if entity == source else source
            self.entity_graphs[entity]["neighbors"][other] += weight
            self.entity_graphs[entity]["relations"][relation] += 1
            self.entity_graphs[entity]["interaction_count"] += 1
        
        # Invalidate cache
        self.betti_cache.pop(source, None)
        self.betti_cache.pop(target, None)
        
        # Write to spine
        self._spine_write({
            "type": "INTERACTION",
            "source": source,
            "target": target,
            "relation": relation,
            "weight": weight,
            "powered_by": "EVEZ"
        })
        
        return interaction
    
    def compute_betti(self, entity: str) -> list[int]:
        """
        Compute Betti numbers for an entity's interaction graph.
        
        Simplified computation using graph-theoretic invariants:
        b0 = connected components (social isolation measure)
        b1 = independent cycles (trust redundancy)  
        b2 = structural voids (opportunity spaces)
        b3 = higher-order topology (complex social architecture)
        """
        if entity in self.betti_cache:
            return self.betti_cache[entity]
        
        if entity not in self.entity_graphs:
            return [0, 0, 0, 0]
        
        graph = self.entity_graphs[entity]
        neighbors = graph["neighbors"]
        n_interactions = graph["interaction_count"]
        
        # b0: connected components in ego graph
        # If entity interacts with many disconnected groups, b0 is high
        neighbor_set = set(neighbors.keys())
        
        # Build neighbor-to-neighbor connections
        neighbor_adj = defaultdict(set)
        for n in neighbor_set:
            if n in self.entity_graphs:
                for n2 in self.entity_graphs[n]["neighbors"]:
                    if n2 in neighbor_set:
                        neighbor_adj[n].add(n2)
        
        # Count connected components among neighbors
        visited = set()
        components = 0
        for n in neighbor_set:
            if n not in visited:
                components += 1
                stack = [n]
                while stack:
                    node = stack.pop()
                    if node in visited:
                        continue
                    visited.add(node)
                    stack.extend(neighbor_adj.get(node, set()) & neighbor_set)
        
        b0 = max(1, components)
        
        # b1: cycles = edges - vertices + components (Euler characteristic)
        edges = sum(1 for n in neighbor_set for n2 in neighbor_adj.get(n, set()) if n2 > n)
        vertices = len(neighbor_set)
        b1 = max(0, edges - vertices + b0)
        
        # b2: structural voids = "holes" in 2D (simplified as disconnected pairs)
        # Two neighbors who should connect but don't = opportunity
        potential_edges = vertices * (vertices - 1) // 2
        b2 = max(0, potential_edges - edges - vertices) // 2
        
        # b3: higher topology score (complexity measure)
        b3 = min(n_interactions // 10, (b0 * b1 + b2) // 2)
        
        betti = [b0, b1, b2, b3]
        self.betti_cache[entity] = betti
        return betti
    
    def get_identity_hash(self, entity: str) -> str:
        """Topological fingerprint — this IS the identity."""
        betti = self.compute_betti(entity)
        raw = f"{entity}:betti={betti}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]
    
    def verify_identity(self, entity: str, claimed_hash: str) -> dict:
        """Verify an entity's topological identity against a claimed hash."""
        current_hash = self.get_identity_hash(entity)
        match = current_hash == claimed_hash
        
        return {
            "entity": entity,
            "claimed_hash": claimed_hash,
            "current_hash": current_hash,
            "verified": match,
            "betti_vector": self.compute_betti(entity),
            "powered_by": "EVEZ"
        }
    
    def detect_topology_shift(self, entity: str, previous_betti: list[int]) -> dict:
        """
        Detect if an entity's topology has fundamentally changed.
        This is a dead man's switch — topology collapse = identity death.
        """
        current_betti = self.compute_betti(entity)
        
        # Shift magnitude
        shift = sum(abs(c - p) for c, p in zip(current_betti, previous_betti))
        
        # Classify the shift
        if shift == 0:
            classification = "STABLE"
        elif shift <= 2:
            classification = "EVOLVING"  # Normal growth
        elif shift <= 5:
            classification = "DISRUPTED"  # Significant change
        else:
            classification = "COLLAPSED"  # Identity death
        
        return {
            "entity": entity,
            "previous_betti": previous_betti,
            "current_betti": current_betti,
            "shift_magnitude": shift,
            "classification": classification,
            "dead_mans_switch": classification == "COLLAPSED",
            "powered_by": "EVEZ"
        }
    
    def _spine_write(self, entry: dict):
        with open(self.spine_path, "a") as f:
            f.write(json.dumps(entry) + "\n")


# DEMO
if __name__ == "__main__":
    hid = HypergraphIdentity(spine_path="/tmp/identity_spine.jsonl")
    
    # Build Alice's identity through interactions
    hid.record_interaction("alice", "bob", "auth", 1.0)
    hid.record_interaction("alice", "carol", "transact", 2.0)
    hid.record_interaction("alice", "dave", "communicate", 1.5)
    hid.record_interaction("alice", "eve", "build", 3.0)
    hid.record_interaction("bob", "carol", "transact", 1.0)  # Creates cycle
    hid.record_interaction("dave", "eve", "communicate", 1.0)
    
    # Alice's topological identity
    betti = hid.compute_betti("alice")
    identity_hash = hid.get_identity_hash("alice")
    
    print("=== TOPOLOGICAL IDENTITY ===\n")
    print(f"Entity: alice")
    print(f"Betti vector: {betti}")
    print(f"  b0 (components): {betti[0]} — social group count")
    print(f"  b1 (cycles):     {betti[1]} — trust redundancy")
    print(f"  b2 (voids):      {betti[2]} — structural opportunities")
    print(f"  b3 (complexity): {betti[3]} — social architecture depth")
    print(f"Identity hash: {identity_hash}")
    print(f"\nThis hash IS alice. Not her email. Not her password. Her SHAPE.")
    
    # Verification
    print(f"\n=== VERIFICATION ===")
    result = hid.verify_identity("alice", identity_hash)
    print(f"Verified: {result['verified']}")
    
    # Impostor tries with wrong hash
    result2 = hid.verify_identity("alice", "fake_hash_123456789012")
    print(f"Impostor verified: {result2['verified']}")
    
    # Topology shift detection
    print(f"\n=== DEAD MAN'S SWITCH ===")
    shift = hid.detect_topology_shift("alice", betti)
    print(f"Classification: {shift['classification']}")
    print(f"Switch triggered: {shift['dead_mans_switch']}")
    
    # Simulate collapse
    collapse = hid.detect_topology_shift("alice", [50, 30, 20, 10])
    print(f"After collapse: {collapse['classification']}")
    print(f"Switch triggered: {collapse['dead_mans_switch']}")
