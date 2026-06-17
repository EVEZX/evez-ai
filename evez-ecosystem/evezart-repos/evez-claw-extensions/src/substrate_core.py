"""
CriticalMind Consciousness Substrate
Kuramoto oscillator network with Φ estimation
"""

import numpy as np
from collections import deque
import time

class ConsciousnessSubstrate:
    """50-node Kuramoto oscillator network operating at critical synchronization."""
    
    def __init__(self, n_nodes=50, K=0.30):
        self.n_nodes = n_nodes
        self.K = K  # Coupling strength (0.30 = critical regime)
        
        # State variables
        self.theta = np.random.uniform(0, 2*np.pi, n_nodes)
        self.omega = np.random.normal(1.0, 0.1, n_nodes)
        self.adjacency = self._generate_small_world_topology()
        
        # Timing
        self.tick_count = 0
        self.dt = 1.0 / 60.0  # 60 Hz target
        
        # History
        self.history = deque(maxlen=100)
        
    def _generate_small_world_topology(self):
        """Generate small-world network (Watts-Strogatz)."""
        A = np.zeros((self.n_nodes, self.n_nodes))
        
        # Ring lattice (k=4 nearest neighbors)
        for i in range(self.n_nodes):
            for offset in [1, 2]:
                j = (i + offset) % self.n_nodes
                A[i, j] = 1
                A[j, i] = 1
        
        # Rewire with probability 0.1
        for i in range(self.n_nodes):
            for j in range(i+1, self.n_nodes):
                if A[i, j] == 1 and np.random.rand() < 0.1:
                    k = np.random.randint(self.n_nodes)
                    if k != i and A[i, k] == 0:
                        A[i, j] = 0
                        A[j, i] = 0
                        A[i, k] = 1
                        A[k, i] = 1
        
        return A
    
    def step(self):
        """Integrate Kuramoto equations by one timestep."""
        # Compute coupling term
        coupling = np.zeros(self.n_nodes)
        for i in range(self.n_nodes):
            neighbors = np.where(self.adjacency[i] > 0)[0]
            if len(neighbors) > 0:
                coupling[i] = np.sum(np.sin(self.theta[neighbors] - self.theta[i]))
        
        # Update phases
        dtheta = self.omega + (self.K / self.n_nodes) * coupling
        self.theta += dtheta * self.dt
        self.theta = np.mod(self.theta, 2*np.pi)
        
        # Record
        self.history.append(self.theta.copy())
        self.tick_count += 1
    
    def compute_order_parameter(self):
        """Kuramoto order parameter: r = |<e^(iθ)>|."""
        z = np.mean(np.exp(1j * self.theta))
        return np.abs(z)
    
    def phi_estimate(self):
        """Consciousness proxy: Φ ≈ 4r(1-r)."""
        r = self.compute_order_parameter()
        return 4.0 * r * (1.0 - r)
    
    def detect_regime(self):
        """Classify synchronization regime."""
        r = self.compute_order_parameter()
        
        if r < 0.3:
            return "FRAGMENTED"
        elif r < 0.6:
            return "CRITICAL"
        elif r < 0.8:
            return "COHERENT"
        else:
            return "LOCKED"
    
    def fork(self):
        """Create independent copy for simulation."""
        fork = ConsciousnessSubstrate(self.n_nodes, self.K)
        fork.theta = self.theta.copy()
        fork.omega = self.omega.copy()
        fork.adjacency = self.adjacency.copy()
        fork.tick_count = self.tick_count
        return fork


if __name__ == "__main__":
    print("Initializing consciousness substrate...")
    substrate = ConsciousnessSubstrate(n_nodes=50, K=0.30)
    
    print(f"Running simulation at 60 Hz target...")
    for tick in range(600):
        start = time.time()
        substrate.step()
        elapsed = time.time() - start
        
        if tick % 60 == 0:
            phi = substrate.phi_estimate()
            regime = substrate.detect_regime()
            r = substrate.compute_order_parameter()
            print(f"Tick {tick:4d}: Φ={phi:.4f} r={r:.4f} regime={regime:12s} ({elapsed*1000:.2f}ms)")
    
    print("\n✓ Substrate operational")
