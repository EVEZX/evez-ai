"""
EVEZ-OS Speedrun Outcome Projecteer
Finds highest-leverage interventions in internet genome structures.
Simulates cascading outcomes from targeted actions.

Speedrun = find the minimum intervention that produces maximum eigenvalue shift.
"""

import numpy as np
import json
import hashlib
import time
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class InterventionType(Enum):
    ADD_NODE = "add_node"           # Add new node to network
    REMOVE_NODE = "remove_node"     # Remove node from network
    ADD_EDGE = "add_edge"           # Add connection
    REMOVE_EDGE = "remove_edge"     # Remove connection
    WEIGHT_SHIFT = "weight_shift"   # Change edge weight
    INJECT_INFO = "inject_info"     # Inject information into node
    CENSOR = "censor"               # Remove information from node
    BRIDGE = "bridge"               # Connect two disconnected clusters
    AMPLIFY = "amplify"             # Boost node centrality


class OutcomeMetric(Enum):
    PHI_SHIFT = "phi_shift"                    # Change in fidelity
    ETA_STAR_REDUCTION = "eta_star_reduction"  # Reduction in incompleteness
    CONNECTIVITY_GAIN = "connectivity_gain"    # Increased connectivity
    INFORMATION_FLOW = "info_flow"              # Increased information flow
    POWER_REDISTRIBUTION = "power_redist"       # More even power distribution
    GAP_CLOSURE = "gap_closure"                 # Fewer structural gaps


@dataclass
class Intervention:
    """A single intervention on the network."""
    id: str
    type: InterventionType
    target_nodes: List[int]
    description: str
    cost: float = 1.0  # Relative cost of intervention

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "target_nodes": self.target_nodes,
            "description": self.description,
            "cost": self.cost,
        }


@dataclass
class OutcomePrediction:
    """Predicted outcome of an intervention."""
    intervention_id: str
    metric: OutcomeMetric
    predicted_value: float
    confidence: float
    cascade_depth: int = 0  # How many steps the cascade propagates
    side_effects: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "intervention_id": self.intervention_id,
            "metric": self.metric.value,
            "predicted_value": round(self.predicted_value, 6),
            "confidence": round(self.confidence, 4),
            "cascade_depth": self.cascade_depth,
            "side_effects": self.side_effects,
        }


@dataclass
class SpeedrunResult:
    """Complete speedrun result — optimal intervention sequence."""
    run_id: str
    timestamp: int
    n_simulations: int
    best_sequence: List[Intervention] = field(default_factory=list)
    best_outcome: Dict = field(default_factory=dict)
    all_interventions: List[Dict] = field(default_factory=list)
    outcome_per_cost: float = 0.0
    merkle_hash: str = ""

    def to_dict(self) -> Dict:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "n_simulations": self.n_simulations,
            "best_sequence": [i.to_dict() for i in self.best_sequence],
            "best_outcome": self.best_outcome,
            "all_interventions": self.all_interventions[:20],  # Top 20
            "outcome_per_cost": round(self.outcome_per_cost, 6),
            "merkle_hash": self.merkle_hash,
        }


class OutcomeProjecteer:
    """Simulate interventions and find optimal speedrun sequences."""

    def __init__(self, operator: str = "evez666"):
        self.operator = operator

    def _apply_intervention(self, adjacency: np.ndarray, intervention: Intervention) -> np.ndarray:
        """Apply an intervention to an adjacency matrix, return modified matrix."""
        A = adjacency.copy()
        n = A.shape[0]

        if intervention.type == InterventionType.ADD_EDGE:
            for i, j in zip(intervention.target_nodes[:-1], intervention.target_nodes[1:]):
                if i < n and j < n:
                    A[i][j] = 1.0
                    A[j][i] = 1.0

        elif intervention.type == InterventionType.REMOVE_EDGE:
            for i, j in zip(intervention.target_nodes[:-1], intervention.target_nodes[1:]):
                if i < n and j < n:
                    A[i][j] = 0.0
                    A[j][i] = 0.0

        elif intervention.type == InterventionType.REMOVE_NODE:
            # Zero out all connections to this node
            for i in intervention.target_nodes:
                if i < n:
                    A[i, :] = 0
                    A[:, i] = 0

        elif intervention.type == InterventionType.WEIGHT_SHIFT:
            for i, j in zip(intervention.target_nodes[:-1], intervention.target_nodes[1:]):
                if i < n and j < n:
                    A[i][j] = min(A[i][j] + 0.5, 1.0)
                    A[j][i] = min(A[j][i] + 0.5, 1.0)

        elif intervention.type == InterventionType.BRIDGE:
            # Connect two disconnected clusters
            if len(intervention.target_nodes) >= 2:
                i, j = intervention.target_nodes[0], intervention.target_nodes[1]
                if i < n and j < n:
                    A[i][j] = 0.5
                    A[j][i] = 0.5

        elif intervention.type == InterventionType.AMPLIFY:
            # Boost node's centrality
            for i in intervention.target_nodes:
                if i < n:
                    for j in range(n):
                        if i != j:
                            A[i][j] = min(A[i][j] + 0.3, 1.0)
                            A[j][i] = min(A[j][i] + 0.3, 1.0)

        return A

    def _compute_metrics(self, adjacency: np.ndarray) -> Dict[str, float]:
        """Compute all outcome metrics for an adjacency matrix."""
        n = adjacency.shape[0]
        if n < 2:
            return {"phi": 1.0, "eta_star": 0.0, "connectivity": 0.0,
                    "info_flow": 0.0, "power_distribution": 1.0, "gaps": 0}

        A = (adjacency + adjacency.T) / 2
        eigenvalues = np.linalg.eigvalsh(A)

        pos_eigs = [v for v in eigenvalues if v > 0.001]
        neg_eigs = [v for v in eigenvalues if v < -0.001]
        total_abs = sum(abs(v) for v in eigenvalues) or 1

        phi = sum(pos_eigs) / total_abs if total_abs > 0 else 0
        eta_star = 1 - phi

        # Connectivity = ratio of connected edges to max possible
        max_edges = n * (n - 1) / 2
        actual_edges = A.sum() / 2
        connectivity = actual_edges / max_edges if max_edges > 0 else 0

        # Information flow = sum of edge weights (total throughput)
        info_flow = float(A.sum()) / (n * n) if n > 0 else 0

        # Power distribution = entropy of degree distribution
        degrees = A.sum(axis=1)
        if degrees.sum() > 0:
            probs = degrees / degrees.sum()
            probs = probs[probs > 0]
            entropy = -sum(p * np.log(p) for p in probs)
            max_entropy = np.log(n) if n > 1 else 1
            power_dist = entropy / max_entropy if max_entropy > 0 else 0
        else:
            power_dist = 0

        gaps = len(neg_eigs)

        return {
            "phi": float(phi),
            "eta_star": float(eta_star),
            "connectivity": float(connectivity),
            "info_flow": float(info_flow),
            "power_distribution": float(power_dist),
            "gaps": gaps,
        }

    def generate_interventions(self, adjacency: np.ndarray, 
                                 node_labels: List[str] = None) -> List[Intervention]:
        """Generate candidate interventions based on network structure."""
        n = adjacency.shape[0]
        if node_labels is None:
            node_labels = [f"N{i}" for i in range(n)]

        interventions = []
        A = (adjacency + adjacency.T) / 2
        degrees = A.sum(axis=1)

        # 1. Bridge disconnected components
        # Find nodes in different clusters and propose bridges
        eigenvalues, eigenvectors = np.linalg.eigh(A)
        if eigenvectors.shape[1] >= 2:
            # Use second eigenvector (Fiedler vector) to find clusters
            fiedler = eigenvectors[:, 1] if eigenvectors.shape[1] > 1 else eigenvectors[:, 0]
            cluster_a = [i for i in range(n) if fiedler[i] >= 0]
            cluster_b = [i for i in range(n) if fiedler[i] < 0]

            if cluster_a and cluster_b:
                # Find closest nodes across clusters
                best_pair = None
                best_dist = float('inf')
                for a in cluster_a[:5]:
                    for b in cluster_b[:5]:
                        dist = abs(fiedler[a] - fiedler[b])
                        if dist < best_dist:
                            best_dist = dist
                            best_pair = (a, b)

                if best_pair:
                    interventions.append(Intervention(
                        id=f"INT-BRG-{len(interventions):03d}",
                        type=InterventionType.BRIDGE,
                        target_nodes=list(best_pair),
                        description=f"Bridge {node_labels[best_pair[0]]} ↔ {node_labels[best_pair[1]]} (cross-cluster)",
                        cost=2.0,
                    ))

        # 2. Amplify weak nodes (boost centrality of low-degree nodes)
        sorted_by_degree = sorted(range(n), key=lambda i: degrees[i])
        for i in sorted_by_degree[:3]:
            if degrees[i] < 1.0:
                interventions.append(Intervention(
                    id=f"INT-AMP-{len(interventions):03d}",
                    type=InterventionType.AMPLIFY,
                    target_nodes=[i],
                    description=f"Amplify {node_labels[i]} (current degree={degrees[i]:.2f})",
                    cost=1.5,
                ))

        # 3. Remove bottleneck (if removing a node increases connectivity)
        for i in range(n):
            if degrees[i] > 2.0:
                interventions.append(Intervention(
                    id=f"INT-REM-{len(interventions):03d}",
                    type=InterventionType.REMOVE_NODE,
                    target_nodes=[i],
                    description=f"Remove bottleneck {node_labels[i]} (degree={degrees[i]:.2f})",
                    cost=3.0,
                ))
                if len(interventions) > 20:
                    break

        # 4. Add edges between unconnected high-degree nodes
        for i in range(min(n, 5)):
            for j in range(i + 1, min(n, 5)):
                if A[i][j] < 0.1 and degrees[i] > 0.5 and degrees[j] > 0.5:
                    interventions.append(Intervention(
                        id=f"INT-ADD-{len(interventions):03d}",
                        type=InterventionType.ADD_EDGE,
                        target_nodes=[i, j],
                        description=f"Connect {node_labels[i]} → {node_labels[j]}",
                        cost=1.0,
                    ))

        # 5. Weight shifts on strong connections
        for i in range(min(n, 5)):
            for j in range(i + 1, min(n, 5)):
                if 0.1 < A[i][j] < 0.9:
                    interventions.append(Intervention(
                        id=f"INT-WGT-{len(interventions):03d}",
                        type=InterventionType.WEIGHT_SHIFT,
                        target_nodes=[i, j],
                        description=f"Strengthen {node_labels[i]} ↔ {node_labels[j]} ({A[i][j]:.2f}→1.0)",
                        cost=0.5,
                    ))

        return interventions[:50]  # Cap at 50 candidates

    def simulate_intervention(self, adjacency: np.ndarray, intervention: Intervention,
                                original_metrics: Dict[str, float] = None) -> Dict:
        """Simulate an intervention and predict outcomes."""
        if original_metrics is None:
            original_metrics = self._compute_metrics(adjacency)

        modified = self._apply_intervention(adjacency, intervention)
        new_metrics = self._compute_metrics(modified)

        # Compute deltas
        deltas = {}
        for key in original_metrics:
            if key in new_metrics:
                deltas[key] = new_metrics[key] - original_metrics[key]

        # Cascade depth: estimate how far the effect propagates
        # Heuristic: eigenvalue shift magnitude correlates with cascade depth
        eig_shift = abs(deltas.get("eta_star", 0))
        cascade_depth = min(5, int(eig_shift * 20))

        # Side effects
        side_effects = []
        if deltas.get("connectivity", 0) < -0.1:
            side_effects.append("Reduced connectivity risk")
        if deltas.get("power_distribution", 0) < -0.05:
            side_effects.append("Power concentration increased")
        if deltas.get("gaps", 0) > 0:
            side_effects.append(f"New structural gaps: {int(deltas['gaps'])}")

        # Outcome/cost ratio
        eta_improvement = -deltas.get("eta_star", 0)  # Lower eta_star is better
        connectivity_gain = deltas.get("connectivity", 0)
        info_flow_gain = deltas.get("info_flow", 0)
        power_dist_gain = deltas.get("power_distribution", 0)
        gap_reduction = -deltas.get("gaps", 0)  # Fewer gaps is better

        # Composite outcome: weighted combination of all improvements
        composite_improvement = (
            eta_improvement * 3.0 +        # η* reduction most important
            connectivity_gain * 2.0 +        # Connectivity second
            info_flow_gain * 1.0 +          # Info flow third
            power_dist_gain * 0.5 +        # Power distribution fourth
            gap_reduction * 2.0             # Gap closure also important
        )
        outcome_per_cost = composite_improvement / max(intervention.cost, 0.1)

        return {
            "intervention": intervention.to_dict(),
            "deltas": deltas,
            "new_metrics": new_metrics,
            "cascade_depth": cascade_depth,
            "side_effects": side_effects,
            "outcome_per_cost": round(outcome_per_cost, 6),
            "eta_star_change": deltas.get("eta_star", 0),
            "phi_change": deltas.get("phi", 0),
        }

    def speedrun(self, adjacency: np.ndarray, node_labels: List[str] = None,
                 n_simulations: int = 100, target_metric: OutcomeMetric = OutcomeMetric.ETA_STAR_REDUCTION
                 ) -> SpeedrunResult:
        """Run a full speedrun: find optimal intervention sequence."""
        original_metrics = self._compute_metrics(adjacency)
        interventions = self.generate_interventions(adjacency, node_labels)

        # Simulate all interventions
        results = []
        for intervention in interventions:
            sim = self.simulate_intervention(adjacency, intervention, original_metrics)
            results.append(sim)

        # Sort by outcome/cost ratio
        results.sort(key=lambda r: r["outcome_per_cost"], reverse=True)

        # Pick best sequence (top 3 non-conflicting interventions)
        used_nodes = set()
        best_sequence = []
        best_outcome = {}

        for sim in results:
            intervention = sim["intervention"]
            target_set = set(intervention["target_nodes"])

            # Skip if conflicts with already-chosen intervention
            if target_set & used_nodes:
                continue

            # Only include interventions that improve the target metric
            if sim["outcome_per_cost"] > 0:
                int_obj = Intervention(
                    id=intervention["id"],
                    type=InterventionType(intervention["type"]),
                    target_nodes=intervention["target_nodes"],
                    description=intervention["description"],
                    cost=intervention["cost"],
                )
                best_sequence.append(int_obj)
                used_nodes.update(target_set)

                if len(best_sequence) >= 3:
                    break

        # Compute cumulative outcome
        if best_sequence:
            cumulative_adj = adjacency.copy()
            total_cost = 0
            for intervention in best_sequence:
                cumulative_adj = self._apply_intervention(cumulative_adj, intervention)
                total_cost += intervention.cost

            final_metrics = self._compute_metrics(cumulative_adj)
            best_outcome = {
                "original_metrics": original_metrics,
                "final_metrics": final_metrics,
                "total_cost": total_cost,
                "phi_gain": final_metrics["phi"] - original_metrics["phi"],
                "eta_star_reduction": original_metrics["eta_star"] - final_metrics["eta_star"],
                "connectivity_gain": final_metrics["connectivity"] - original_metrics["connectivity"],
            }
        else:
            best_outcome = {"message": "No improving interventions found"}

        # All intervention results for ranking
        all_interventions = [
            {
                "rank": i + 1,
                "outcome_per_cost": r["outcome_per_cost"],
                "intervention": r["intervention"]["description"],
                "eta_star_change": r["eta_star_change"],
                "phi_change": r["phi_change"],
                "cascade_depth": r["cascade_depth"],
            }
            for i, r in enumerate(results[:20])
        ]

        merkle = hashlib.sha256(
            json.dumps({
                "n_sims": n_simulations,
                "best_cost": sum(i.cost for i in best_sequence),
                "eta_reduction": best_outcome.get("eta_star_reduction", 0),
            }).encode()
        ).hexdigest()[:16]

        return SpeedrunResult(
            run_id=f"SPD-{merkle[:8].upper()}",
            timestamp=int(time.time()),
            n_simulations=n_simulations,
            best_sequence=best_sequence,
            best_outcome=best_outcome,
            all_interventions=all_interventions,
            outcome_per_cost=best_outcome.get("eta_star_reduction", 0) / max(sum(i.cost for i in best_sequence), 0.1) if best_sequence else 0,
            merkle_hash=merkle,
        )
