"""
MyClaw — Wavefunction Router
Routes web graphs through wavefunction propagation.
Phase-coded intent amplification. Grover iterations for action selection.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

class PhaseCode(Enum):
    INTENT = 0          # Pure intent — no carrier
    AMPLIFY = np.pi/4   # Amplify this path
    SUPPRESS = np.pi/2  # Suppress this path
    MEASURE = np.pi     # Collapse to classical
    GHOST = 3*np.pi/2   # Archive — don't collapse

@dataclass
class WavefunctionNode:
    """A node in the wavefunction graph"""
    id: str
    amplitude: complex = 1+0j
    phase_code: PhaseCode = PhaseCode.INTENT
    connections: Dict[str, complex] = field(default_factory=dict)
    energy: float = 0.0
    collapsed: bool = False
    
    def propagate(self, target: str, coupling: float = 0.1):
        """Propagate wavefunction to connected node"""
        if target in self.connections:
            self.connections[target] *= np.exp(1j * coupling)
    
    def measure(self) -> str:
        """Collapse wavefunction — return dominant path"""
        if not self.connections:
            return self.id
        probs = {k: abs(v)**2 for k, v in self.connections.items()}
        total = sum(probs.values()) or 1
        probs = {k: v/total for k, v in probs.items()}
        # Weighted random collapse
        choice = np.random.choice(list(probs.keys()), p=list(probs.values()))
        self.collapsed = True
        return choice

@dataclass 
class QuantumGraph:
    """Full wavefunction graph with routing"""
    nodes: Dict[str, WavefunctionNode] = field(default_factory=dict)
    time: float = 0.0
    dt: float = 0.01
    hbar: float = 1.0
    
    def add_node(self, id: str, phase: PhaseCode = PhaseCode.INTENT):
        self.nodes[id] = WavefunctionNode(id=id, phase_code=phase)
    
    def connect(self, source: str, target: str, coupling: float = 0.1):
        if source in self.nodes and target in self.nodes:
            self.nodes[source].connections[target] = coupling * np.exp(1j * 0)
    
    def step(self):
        """Evolve one timestep — TDSE-inspired propagation"""
        new_amplitudes = {}
        for id, node in self.nodes.items():
            if node.collapsed:
                new_amplitudes[id] = node.amplitude
                continue
            # Hamiltonian: H = kinetic + potential
            # Kinetic: coupling to neighbors
            # Potential: phase-coded intent
            dpsi = 0+0j
            for neighbor_id, coupling in node.connections.items():
                neighbor = self.nodes.get(neighbor_id)
                if neighbor and not neighbor.collapsed:
                    dpsi += -1j * coupling * neighbor.amplitude * self.dt / self.hbar
            
            # Phase-coded amplification
            if node.phase_code == PhaseCode.AMPLIFY:
                dpsi *= 1.5
            elif node.phase_code == PhaseCode.SUPPRESS:
                dpsi *= 0.5
            elif node.phase_code == PhaseCode.MEASURE:
                # Schedule measurement
                dpsi *= 0.1  # Rapid decoherence
                
            new_amplitudes[id] = node.amplitude + dpsi
        
        for id, amp in new_amplitudes.items():
            self.nodes[id].amplitude = amp
        
        self.time += self.dt
    
    def grover_search(self, target: str, iterations: int = 3) -> str:
        """Grover's algorithm for action selection"""
        # Initialize uniform superposition
        n = len(self.nodes)
        if n == 0:
            return ""
        
        # Create superposition state
        psi = np.ones(n, dtype=complex) / np.sqrt(n)
        node_ids = list(self.nodes.keys())
        
        if target not in node_ids:
            return node_ids[0] if node_ids else ""
        
        target_idx = node_ids.index(target)
        
        # Oracle: flip target phase
        oracle = np.ones(n)
        oracle[target_idx] = -1
        
        # Diffusion operator
        diffusion = 2 * np.ones((n, n)) / n - np.eye(n)
        
        for _ in range(iterations):
            psi *= oracle                    # Oracle
            psi = diffusion @ psi            # Diffusion
        
        # Measure
        probs = np.abs(psi)**2
        probs /= probs.sum()
        result_idx = np.random.choice(n, p=probs)
        return node_ids[result_idx]
    
    def get_entanglement(self) -> float:
        """Measure graph entanglement (von Neumann entropy proxy)"""
        amplitudes = np.array([abs(n.amplitude)**2 for n in self.nodes.values()])
        amplitudes = amplitudes / (amplitudes.sum() or 1)
        entropy = -np.sum(amplitudes * np.log2(amplitudes + 1e-10))
        return float(entropy)

if __name__ == "__main__":
    graph = QuantumGraph()
    graph.add_node("intent", PhaseCode.INTENT)
    graph.add_node("action_a", PhaseCode.AMPLIFY)
    graph.add_node("action_b", PhaseCode.SUPPRESS)
    graph.add_node("ghost", PhaseCode.GHOST)
    
    graph.connect("intent", "action_a", 0.3)
    graph.connect("intent", "action_b", 0.1)
    graph.connect("action_a", "ghost", 0.05)
    
    for _ in range(100):
        graph.step()
    
    print(f"Time: {graph.time:.2f}")
    print(f"Entanglement: {graph.get_entanglement():.4f}")
    print(f"Grover search for 'action_a': {graph.grover_search('action_a')}")
    print(f"Measurement from intent: {graph.nodes['intent'].measure()}")
