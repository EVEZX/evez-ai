"""
EVEZ-OS Physics Dungeon — TDSE Navigation Engine
Maps web resources as quantum potentials. Navigation = wavefunction evolution.
Only stable or tunneling states become suggested paths.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

class PotentialType(Enum):
    WELL = "well"         # Stable resource (docs, APIs)
    BARRIER = "barrier"    # Blocked/protected resource
    LATTICE = "lattice"   # Repeated structure (pagination, indices)
    FREE = "free"         # Unconstrained

@dataclass
class QuantumNode:
    """A resource in the physics dungeon"""
    id: str
    url: str
    depth: int = 0
    potential_type: PotentialType = PotentialType.FREE
    energy: float = 0.0         # Content richness
    barrier_height: float = 0.0  # Auth/paywall/etc
    connected: List[str] = field(default_factory=list)

@dataclass
class WavefunctionState:
    """Probability distribution over navigation candidates"""
    node_ids: List[str]
    amplitudes: np.ndarray      # Complex amplitudes
    phase: float = 0.0
    time: float = 0.0

class TDSEEngine:
    """
    Time-Dependent Schrödinger Equation simulator for navigation.
    
    The wavefunction ψ(x,t) evolves over the potential landscape V(x)
    formed by web resources. Navigation probability = |ψ|² at each node.
    
    Uses split-operator method (stable, unitary):
      ψ(t+dt) = exp(-iV·dt/2) · FFT⁻¹[exp(-ik²·dt) · FFT[exp(-iV·dt/2) · ψ]]
    """
    
    def __init__(self, dx: float = 0.1, dt: float = 0.01, n_points: int = 128):
        self.dx = dx
        self.dt = dt
        self.n_points = n_points
        self.nodes: Dict[str, QuantumNode] = {}
        self.wavefunction: Optional[WavefunctionState] = None
        self.potential: np.ndarray = np.zeros(n_points)
        self.potential_history: List[np.ndarray] = []
        
    def add_node(self, node: QuantumNode):
        """Add a resource to the physics dungeon"""
        self.nodes[node.id] = node
        
    def build_potential(self):
        """Construct V(x) from node landscape"""
        self.potential = np.zeros(self.n_points)
        n = len(self.nodes)
        if n == 0:
            return
            
        # Map nodes to spatial positions
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.energy)
        for i, node in enumerate(sorted_nodes):
            pos = int(i / max(n - 1, 1) * (self.n_points - 1))
            
            if node.potential_type == PotentialType.WELL:
                # Attractive potential (negative = well)
                self.potential[pos] = -abs(node.energy) * 2
            elif node.potential_type == PotentialType.BARRIER:
                # Repulsive potential (positive = barrier)
                self.potential[pos] = node.barrier_height * 5
            elif node.potential_type == PotentialType.LATTICE:
                # Periodic potential
                for offset in range(-2, 3):
                    idx = (pos + offset) % self.n_points
                    self.potential[idx] = -abs(node.energy) * np.cos(offset * np.pi)
            # FREE = zero potential (default)
            
        # Smooth potential
        kernel = np.ones(5) / 5
        self.potential = np.convolve(self.potential, kernel, mode='same')
        self.potential_history.append(self.potential.copy())
        
    def initialize_wavefunction(self, center_node_id: str):
        """Start wavefunction as Gaussian packet at a node"""
        if center_node_id not in self.nodes:
            center_node_id = list(self.nodes.keys())[0]
        
        # Find position of center node
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.energy)
        center_idx = next(i for i, n in enumerate(sorted_nodes) if n.id == center_node_id)
        x0 = center_idx / max(len(sorted_nodes) - 1, 1) * (self.n_points - 1)
        
        x = np.arange(self.n_points) * self.dx
        sigma = 5.0  # Width of initial packet
        k0 = 2.0    # Initial momentum
        
        # Gaussian wave packet
        psi_real = np.exp(-((x - x0 * self.dx) ** 2) / (2 * sigma ** 2)) * np.cos(k0 * x)
        psi_imag = np.exp(-((x - x0 * self.dx) ** 2) / (2 * sigma ** 2)) * np.sin(k0 * x)
        
        self.psi = psi_real + 1j * psi_imag
        self.psi /= np.sqrt(np.sum(np.abs(self.psi) ** 2) * self.dx)  # Normalize
        
        self.wavefunction = WavefunctionState(
            node_ids=[n.id for n in sorted_nodes],
            amplitudes=self.psi,
            phase=0.0,
            time=0.0
        )
        
    def evolve(self, steps: int = 10) -> Dict[str, float]:
        """
        Evolve wavefunction using split-operator method.
        Returns navigation probabilities for each node.
        """
        if self.wavefunction is None:
            return {}
            
        psi = self.psi.copy()
        x = np.arange(self.n_points) * self.dx
        k = np.fft.fftfreq(self.n_points, self.dx) * 2 * np.pi
        
        V = self.potential
        kinetic = np.exp(-0.5j * k ** 2 * self.dt)
        
        for _ in range(steps):
            # Half-step potential
            psi *= np.exp(-0.5j * V * self.dt)
            # Full-step kinetic (in k-space)
            psi_k = np.fft.fft(psi)
            psi_k *= kinetic
            psi = np.fft.ifft(psi_k)
            # Half-step potential
            psi *= np.exp(-0.5j * V * self.dt)
            
            self.wavefunction.time += self.dt
        
        self.psi = psi
        self.wavefunction.amplitudes = psi
        
        # Compute probabilities at each node position
        probs = np.abs(psi) ** 2
        probs /= (probs.sum() + 1e-10)
        
        # Map back to nodes
        node_probs = {}
        n = len(self.wavefunction.node_ids)
        for i, node_id in enumerate(self.wavefunction.node_ids):
            pos = int(i / max(n - 1, 1) * (self.n_points - 1))
            node_probs[node_id] = float(probs[pos])
            
        return node_probs
        
    def get_tunneling_candidates(self, threshold: float = 0.01) -> List[Tuple[str, float]]:
        """
        Find nodes the wavefunction can tunnel into despite barriers.
        These are the 'hidden' navigation paths.
        """
        probs = self.evolve(steps=50)
        if not probs:
            return []
            
        # Nodes with non-zero probability behind barriers
        tunneling = []
        for node_id, prob in probs.items():
            node = self.nodes.get(node_id)
            if node and node.potential_type == PotentialType.BARRIER and prob > threshold:
                tunneling.append((node_id, prob))
                
        return sorted(tunneling, key=lambda x: -x[1])
        
    def get_stable_attractors(self) -> List[Tuple[str, float]]:
        """
        Find wells the wavefunction has concentrated in.
        These are the 'recommended' navigation destinations.
        """
        probs = self.evolve(steps=20)
        if not probs:
            return []
            
        attractors = []
        for node_id, prob in probs.items():
            node = self.nodes.get(node_id)
            if node and node.potential_type == PotentialType.WELL and prob > 0.05:
                attractors.append((node_id, prob))
                
        return sorted(attractors, key=lambda x: -x[1])
