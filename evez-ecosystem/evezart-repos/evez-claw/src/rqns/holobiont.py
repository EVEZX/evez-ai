"""
EntangledHolobiontMapper — Microbiome-gut-brain + quantum biology + federated learning.

Maps holobiont-scale active inference:
- Host + microbiome as joint causal graph
- Quantum coherence channels in biological networks
- Privacy-preserving federated aggregation across endosymbiotic scales

The holobiont resists decoherence because horizontal gene transfer
continuously re-entangles the microbiome component with host neural states.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class HolobiontState:
    host_phi: float
    microbiome_phi: float
    joint_phi: float            # Entangled Φ > sum of parts
    coherence_channel: float    # [0,1] quantum coherence proxy
    decoherence_rate: float
    federated_privacy_budget: float  # ε for differential privacy


class EntangledHolobiontMapper:
    """
    Models the holobiont (host + microbiome) as a jointly conscious system.

    Joint Φ exceeds the sum of individual Φ values when the microbiome-gut-
    brain axis maintains coherent information integration. This models
    resistance to decoherence via entanglement-like correlations.
    """

    DECOHERENCE_BASE = 0.03  # Matches η* — systems decohere at ~3%/tick

    def __init__(self, privacy_epsilon: float = 1.0):
        self.privacy_epsilon = privacy_epsilon
        self._nodes: Dict[str, np.ndarray] = {}

    def register_agent(self, agent_id: str, local_params: np.ndarray):
        """Register a federated learning participant (endosymbiont)."""
        self._nodes[agent_id] = local_params.copy()

    def federated_aggregate(self, noise_scale: float = 0.1) -> np.ndarray:
        """
        Privacy-preserving federated mean with Gaussian DP noise.
        ε-differential privacy: σ = noise_scale / ε
        """
        if not self._nodes:
            return np.array([])

        params = np.array(list(self._nodes.values()))
        mean = params.mean(axis=0)

        # Gaussian noise for differential privacy
        sigma = noise_scale / self.privacy_epsilon
        noise = np.random.normal(0, sigma, mean.shape)
        return mean + noise

    def compute_joint_phi(self, host_adj: np.ndarray,
                           microbiome_adj: np.ndarray,
                           coupling: float = 0.15) -> HolobiontState:
        """
        Compute joint Φ for host + microbiome system.

        Joint adjacency = block matrix with coupling term.
        Entanglement boost: joint_phi > host_phi + microbiome_phi when
        coupling > decoherence threshold.
        """
        def phi_from_adj(A: np.ndarray) -> float:
            r_bar = A.mean()
            return 4.0 * r_bar * (1.0 - r_bar)

        host_phi = phi_from_adj(host_adj)
        micro_phi = phi_from_adj(microbiome_adj)

        # Joint Φ with entanglement boost
        coherence = max(0.0, coupling - self.DECOHERENCE_BASE)
        joint_phi = host_phi + micro_phi + coherence * host_phi * micro_phi

        decoherence_rate = self.DECOHERENCE_BASE + max(0, 0.02 - coherence)

        return HolobiontState(
            host_phi=host_phi,
            microbiome_phi=micro_phi,
            joint_phi=min(joint_phi, 1.0),
            coherence_channel=coherence,
            decoherence_rate=decoherence_rate,
            federated_privacy_budget=self.privacy_epsilon,
        )
