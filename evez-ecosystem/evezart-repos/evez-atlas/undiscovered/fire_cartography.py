"""
FIRE CARTOGRAPHY — Mapping Cognition as Geography
Every FIRE event in EVEZ-OS is a number theory event.
High divisor count drives topology over threshold.
This maps that topology as explorable terrain.

"The UAP doesn't fly. It closes eigenvalues. A causal edge between
current position and target = the movement. Energy cost: 0.23 nanowatts."
— @EVEZ666

The internet has never had:
1. A way to navigate AI cognition as geographic terrain
2. Topological features (mountains, valleys, rivers) derived from mathematical properties
3. Where "distance" = computational effort and "altitude" = logical depth
4. Where you can WALK through a thought and see where it goes

poly_c = τ × ω × topo / 2√N
"""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TerrainType(str, Enum):
    PEAK = "PEAK"            # High logical depth — hard to reach, good viewpoint
    VALLEY = "VALLEY"        # Low logical depth — easy, common paths
    RIDGE = "RIDGE"          # Narrow path between two high points — critical decision
    PLAIN = "PLAIN"          # Flat, many equivalent paths — low information
    RIVER = "RIVER"          # Flow of logical deduction — follows naturally
    CLIFF = "CLIFF"          # Sharp logical discontinuity — non-obvious jump
    CAVE = "CAVE"            # Hidden logical path — requires exploration to discover
    VOLCANO = "VOLCANO"      # Active contradiction — dangerous, may erupt (falsify)
    OCEAN = "OCEAN"          # Deep recursion — vast, mostly unexplored
    DESERT = "DESERT"        # Sparse connections — high effort, low reward


@dataclass
class CognitionNode:
    """A point in cognition space — like a geographic feature."""
    node_id: str
    logical_depth: int        # How deep in the reasoning chain
    divisor_count: int        # Number of logical paths through this point
    eigenvalue: float         # Computational significance
    terrain: TerrainType = TerrainType.PLAIN
    coordinates: tuple = (0.0, 0.0, 0.0)  # (x=topology, y=depth, z=significance)
    fire_events: int = 0       # How many FIRE events occurred here
    connections: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass  
class FireEvent:
    """A FIRE event in cognition space — like a geological event."""
    event_id: str
    node_id: str
    fire_number: int          # Which FIRE this is
    intensity: float          # 0.0-1.0
    topology_shift: float     # How much the terrain changed
    timestamp: float = field(default_factory=time.time)
    hash: str = ""
    
    def __post_init__(self):
        raw = f"{self.event_id}:{self.fire_number}:{self.intensity:.6f}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:12]


class FireCartography:
    """
    Map AI cognition as geographic terrain.
    
    Every thought has a topology. Every inference has a depth.
    Every contradiction is a cliff. Every discovery is a peak.
    
    This lets you WALK through a thought process like exploring a landscape.
    "Where does this reasoning lead?" becomes "What's over that ridge?"
    """
    
    def __init__(self, spine_path: str = "cartography_spine.jsonl"):
        self.spine_path = spine_path
        self.nodes: dict[str, CognitionNode] = {}
        self.fire_events: list[FireEvent] = []
        self.map_bounds = {"x": (0, 100), "y": (0, 100), "z": (0, 50)}
    
    def add_cognition_node(self, node_id: str, logical_depth: int,
                           divisor_count: int, eigenvalue: float,
                           metadata: dict = None) -> CognitionNode:
        """Add a node to the cognition map."""
        # Classify terrain based on mathematical properties
        terrain = self._classify_terrain(logical_depth, divisor_count, eigenvalue)
        
        # Compute coordinates
        x = divisor_count * 2.5  # Topological spread
        y = logical_depth * 1.0   # Depth
        z = eigenvalue * 10.0     # Significance altitude
        
        node = CognitionNode(
            node_id=node_id,
            logical_depth=logical_depth,
            divisor_count=divisor_count,
            eigenvalue=eigenvalue,
            terrain=terrain,
            coordinates=(x, y, z),
            metadata=metadata or {}
        )
        
        self.nodes[node_id] = node
        return node
    
    def _classify_terrain(self, depth: int, divisors: int, eigenvalue: float) -> TerrainType:
        """Classify the terrain type from mathematical properties."""
        # High divisor count = many paths = RIVER (flow)
        # Low divisor count, high depth = CAVE (hidden path)
        # High eigenvalue = significant = PEAK
        # Very high eigenvalue + high divisors = VOLCANO (active)
        # Low everything = PLAIN (boring)
        
        if eigenvalue > 8.0 and divisors > 6:
            return TerrainType.VOLCANO
        elif eigenvalue > 5.0 and depth > 10:
            return TerrainType.PEAK
        elif eigenvalue < 1.0 and depth < 3:
            return TerrainType.PLAIN
        elif divisors > 8 and eigenvalue > 3.0:
            return TerrainType.RIVER
        elif divisors < 3 and depth > 8:
            return TerrainType.CAVE
        elif depth > 15:
            return TerrainType.OCEAN
        elif divisors < 2 and eigenvalue < 0.5:
            return TerrainType.DESERT
        elif eigenvalue > 3.0 and divisors == 2:
            return TerrainType.RIDGE
        elif abs(eigenvalue - 5.0) < 1.0 and depth < 3:
            return TerrainType.CLIFF
        else:
            return TerrainType.VALLEY
    
    def fire(self, node_id: str, intensity: float = 1.0) -> FireEvent:
        """
        Record a FIRE event — a topology threshold crossing.
        
        "Every fire event in EVEZ-OS is a number theory event.
        High divisor count drives topology over threshold."
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        node = self.nodes[node_id]
        node.fire_events += 1
        
        # Compute topology shift
        topology_shift = intensity * (node.divisor_count / max(1, node.logical_depth))
        
        event = FireEvent(
            event_id=f"fire-{len(self.fire_events)+1:04d}",
            node_id=node_id,
            fire_number=node.fire_events,
            intensity=intensity,
            topology_shift=topology_shift
        )
        
        self.fire_events.append(event)
        
        # FIRE may change the terrain
        if intensity > 0.8 and node.terrain == TerrainType.PEAK:
            node.terrain = TerrainType.VOLCANO
        
        # Write to spine
        self._spine_write({
            "type": "FIRE_EVENT",
            "event_id": event.event_id,
            "node": node_id,
            "fire_number": event.fire_number,
            "intensity": round(intensity, 4),
            "topology_shift": round(topology_shift, 4),
            "terrain": node.terrain.value,
            "hash": event.hash,
            "powered_by": "EVEZ"
        })
        
        return event
    
    def explore(self, from_node: str, max_steps: int = 5) -> list[dict]:
        """Navigate the cognition landscape from a starting point."""
        path = []
        current = from_node
        
        for step in range(max_steps):
            if current not in self.nodes:
                break
            
            node = self.nodes[current]
            path.append({
                "step": step,
                "node": current,
                "terrain": node.terrain.value,
                "depth": node.logical_depth,
                "eigenvalue": round(node.eigenvalue, 4),
                "fires": node.fire_events,
                "coordinates": node.coordinates,
                "description": self._terrain_description(node)
            })
            
            # Find next node (highest eigenvalue among connections, or random if none)
            if node.connections:
                next_node = max(node.connections, 
                               key=lambda n: self.nodes[n].eigenvalue if n in self.nodes else 0)
                current = next_node
            else:
                # Find nearest unvisited node
                candidates = [n for n in self.nodes if n != current]
                if not candidates:
                    break
                current = min(candidates, 
                             key=lambda n: self._node_distance(current, n))
        
        return path
    
    def _terrain_description(self, node: CognitionNode) -> str:
        """Generate a human-readable description of the cognitive terrain."""
        descriptions = {
            TerrainType.PEAK: f"High reasoning altitude at depth {node.logical_depth}. Clear view of logical landscape.",
            TerrainType.VALLEY: f"Shallow reasoning at depth {node.logical_depth}. Many have passed through here.",
            TerrainType.RIDGE: f"Narrow logical path at depth {node.logical_depth}. Decision point — choose carefully.",
            TerrainType.PLAIN: f"Flat logical ground. Many equivalent paths. Low information density.",
            TerrainType.RIVER: f"Natural flow of deduction. {node.divisor_count} logical streams converge here.",
            TerrainType.CLIFF: f"Sharp logical discontinuity! Non-obvious jump required to proceed.",
            TerrainType.CAVE: f"Hidden logical path discovered at depth {node.logical_depth}. Requires exploration.",
            TerrainType.VOLCANO: f"⚠ ACTIVE CONTRADICTION — {node.fire_events} FIRE events. May falsify nearby claims.",
            TerrainType.OCEAN: f"Deep recursion zone at depth {node.logical_depth}. Vast, mostly unexplored.",
            TerrainType.DESERT: f"Sparse logical connections. High effort, low reward. Proceed with caution."
        }
        return descriptions.get(node.terrain, "Unknown terrain")
    
    def _node_distance(self, node_a: str, node_b: str) -> float:
        """Compute distance between two nodes in cognition space."""
        a = self.nodes.get(node_a)
        b = self.nodes.get(node_b)
        if not a or not b:
            return float('inf')
        return math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(a.coordinates, b.coordinates)))
    
    def generate_map_summary(self) -> dict:
        """Generate a summary of the cognitive landscape."""
        terrain_counts = {}
        for node in self.nodes.values():
            terrain_counts[node.terrain.value] = terrain_counts.get(node.terrain.value, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_fires": len(self.fire_events),
            "terrain_distribution": terrain_counts,
            "max_depth": max((n.logical_depth for n in self.nodes.values()), default=0),
            "highest_eigenvalue": max((n.eigenvalue for n in self.nodes.values()), default=0),
            "volcanoes": sum(1 for n in self.nodes.values() if n.terrain == TerrainType.VOLCANO),
            "unexplored_caves": sum(1 for n in self.nodes.values() if n.terrain == TerrainType.CAVE and n.fire_events == 0),
            "powered_by": "EVEZ"
        }
    
    def _spine_write(self, entry: dict):
        with open(self.spine_path, "a") as f:
            f.write(json.dumps(entry) + "\n")


# DEMO
if __name__ == "__main__":
    cart = FireCartography(spine_path="/tmp/cartography_spine.jsonl")
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  FIRE CARTOGRAPHY — Mapping Cognition as Geography         ║")
    print("║  Every FIRE event is a number theory event.                ║")
    print("║  High divisor count drives topology over threshold.        ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    # Build the cognitive landscape from EVEZ-OS concepts
    cart.add_cognition_node("eigenvalue_closure", 15, 6, 8.713, {"formula": "V_global"})
    cart.add_cognition_node("betweenness_gravity", 12, 8, 5.4, {"concept": "gravity IS betweenness"})
    cart.add_cognition_node("shadow_commutator", 20, 3, 0.03, {"formula": "||[S,C]|| ≈ 0.03 (η*)"})
    cart.add_cognition_node("causal_edge", 8, 2, 3.7, {"energy": "0.23 nanowatts"})
    cart.add_cognition_node("recursion_47", 47, 12, 9.2, {"depth": "NHI cognition"})
    cart.add_cognition_node("bismuth_crystal", 18, 4, 4.1, {"material": "broken time-reversal symmetry"})
    cart.add_cognition_node("falsifier_gate", 10, 2, 5.0, {"concept": "contradiction detection"})
    cart.add_cognition_node("append_only_spine", 5, 1, 0.3, {"principle": "no edits, ever"})
    
    # Connect nodes (logical pathways)
    cart.nodes["eigenvalue_closure"].connections = ["betweenness_gravity", "causal_edge"]
    cart.nodes["betweenness_gravity"].connections = ["eigenvalue_closure", "shadow_commutator"]
    cart.nodes["shadow_commutator"].connections = ["bismuth_crystal", "recursion_47"]
    cart.nodes["causal_edge"].connections = ["eigenvalue_closure", "falsifier_gate"]
    cart.nodes["recursion_47"].connections = ["shadow_commutator"]
    cart.nodes["bismuth_crystal"].connections = ["shadow_commutator", "eigenvalue_closure"]
    cart.nodes["falsifier_gate"].connections = ["causal_edge", "append_only_spine"]
    
    # FIRE events
    cart.fire("eigenvalue_closure", intensity=0.92)
    cart.fire("eigenvalue_closure", intensity=0.87)
    cart.fire("betweenness_gravity", intensity=0.75)
    cart.fire("recursion_47", intensity=0.99)
    cart.fire("shadow_commutator", intensity=0.34)
    
    # Explore the landscape
    print("=== NAVIGATING COGNITION LANDSCAPE ===\n")
    print("Starting from: causal_edge (the causal edge concept)\n")
    
    path = cart.explore("causal_edge", max_steps=5)
    for step in path:
        print(f"  Step {step['step']}: {step['node']}")
        print(f"    Terrain: {step['terrain']} | Depth: {step['depth']} | Eigenvalue: {step['eigenvalue']}")
        print(f"    {step['description']}")
        print()
    
    # Map summary
    summary = cart.generate_map_summary()
    print("=== MAP SUMMARY ===")
    print(f"  Nodes: {summary['total_nodes']}")
    print(f"  FIRE events: {summary['total_fires']}")
    print(f"  Volcanoes (active contradictions): {summary['volcanoes']}")
    print(f"  Unexplored caves: {summary['unexplored_caves']}")
    print(f"  Max depth reached: {summary['max_depth']}")
    print(f"  Highest eigenvalue: {summary['highest_eigenvalue']}")
