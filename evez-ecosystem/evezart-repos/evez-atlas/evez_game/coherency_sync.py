"""Coherency Synchronizer and Entanglement System.

Implements quantum-inspired coherency maintenance and entanglement:
- Distributed state synchronization with conflict resolution
- Entanglement-based state correlation across nodes
- Coherency decay and revival mechanisms
- Measurement-induced collapse simulation
- Bell inequality violation detection for entanglement verification
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .quantum_rng import QuantumRNG, random_bytes, random_float


class CoherencyState(Enum):
    """States of quantum-like coherency."""
    COHERENT = auto()      # Fully synchronized
    DECOHERING = auto()    # Losing synchronization
    DECOHERENT = auto()    # Fully desynchronized
    COLLAPSED = auto()     # Measured, definite state
    ENTANGLED = auto()     # Correlated with another state


@dataclass
class QuantumState:
    """A quantum-like state with superposition and phase."""
    id: str
    amplitudes: Dict[str, complex] = field(default_factory=dict)
    phase: float = 0.0
    coherency: float = 1.0
    state: CoherencyState = CoherencyState.COHERENT
    last_sync: float = field(default_factory=time.time)
    entangled_with: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def probability(self, basis: str) -> float:
        """Get probability of measuring state in given basis."""
        if basis not in self.amplitudes:
            return 0.0
        return abs(self.amplitudes[basis]) ** 2
    
    def normalize(self) -> None:
        """Normalize amplitudes to sum of probabilities = 1."""
        total = sum(abs(a)**2 for a in self.amplitudes.values())
        if total > 0:
            factor = 1.0 / (total ** 0.5)
            for k in self.amplitudes:
                self.amplitudes[k] *= factor
    
    def measure(self, rng: Optional[QuantumRNG] = None) -> Tuple[str, float]:
        """Measure the state, collapsing superposition."""
        rng = rng or QuantumRNG()
        
        # Create superposition for RNG
        states = [(a, b) for b, a in self.amplitudes.items()]
        result = rng.quantum_superposition(states)
        
        # Collapse state
        prob = self.probability(result)
        self.amplitudes = {result: complex(1.0, 0)}
        self.state = CoherencyState.COLLAPSED
        self.coherency = 0.0
        
        return result, prob
    
    def apply_phase_shift(self, delta: float) -> None:
        """Apply phase shift to all amplitudes."""
        self.phase += delta
        for k in self.amplitudes:
            self.amplitudes[k] *= complex(
                math.cos(delta),
                math.sin(delta)
            )


import math


@dataclass
class EntanglementLink:
    """A link between entangled states."""
    state_a: str
    state_b: str
    correlation_type: str = "bell"  # bell, ghz, w
    strength: float = 1.0
    created_at: float = field(default_factory=time.time)
    last_verified: float = field(default_factory=time.time)
    bell_score: float = 0.0  # CHSH inequality violation score


class EntanglementManager:
    """Manage entanglement between quantum states."""
    
    def __init__(self, rng: Optional[QuantumRNG] = None):
        self.rng = rng or QuantumRNG()
        self.states: Dict[str, QuantumState] = {}
        self.links: Dict[str, EntanglementLink] = {}
        self._lock = threading.Lock()
    
    def create_state(self, state_id: str, bases: List[str] = None) -> QuantumState:
        """Create a new quantum state in superposition."""
        bases = bases or ["0", "1"]
        
        # Create equal superposition
        n = len(bases)
        amplitude = complex(1.0 / (n ** 0.5), 0)
        
        state = QuantumState(
            id=state_id,
            amplitudes={b: amplitude for b in bases},
            state=CoherencyState.COHERENT
        )
        
        with self._lock:
            self.states[state_id] = state
        
        return state
    
    def entangle(self, state_a: str, state_b: str, correlation_type: str = "bell") -> EntanglementLink:
        """Create entanglement between two states."""
        with self._lock:
            if state_a not in self.states:
                self.create_state(state_a)
            if state_b not in self.states:
                self.create_state(state_b)
            
            # Create Bell pair amplitudes
            if correlation_type == "bell":
                # |Φ+⟩ = (|00⟩ + |11⟩) / √2
                self.states[state_a].amplitudes = {"0": complex(1/2**0.5, 0), "1": complex(0, 0)}
                self.states[state_b].amplitudes = {"0": complex(1/2**0.5, 0), "1": complex(0, 0)}
            
            # Update state metadata
            self.states[state_a].entangled_with.add(state_b)
            self.states[state_b].entangled_with.add(state_a)
            self.states[state_a].state = CoherencyState.ENTANGLED
            self.states[state_b].state = CoherencyState.ENTANGLED
            
            # Create link
            link_id = f"{state_a}:{state_b}"
            link = EntanglementLink(
                state_a=state_a,
                state_b=state_b,
                correlation_type=correlation_type,
                strength=1.0
            )
            
            # Verify with Bell test
            link.bell_score = self._bell_test(state_a, state_b)
            
            self.links[link_id] = link
            
            return link
    
    def _bell_test(self, state_a: str, state_b: str, iterations: int = 1000) -> float:
        """Perform CHSH inequality test to verify entanglement.
        
        Returns violation score (S > 2 indicates entanglement).
        """
        # CHSH angles
        angles_a = [0, math.pi/4]
        angles_b = [math.pi/8, 3*math.pi/8]
        
        correlations = []
        
        for theta_a in angles_a:
            for theta_b in angles_b:
                # Simulate measurements
                matches = 0
                for _ in range(iterations):
                    # Measure both states at given angles
                    result_a = self._measure_at_angle(state_a, theta_a)
                    result_b = self._measure_at_angle(state_b, theta_b)
                    
                    # Check correlation
                    if result_a == result_b:
                        matches += 1
                
                correlation = (2 * matches - iterations) / iterations
                correlations.append(correlation)
        
        # Calculate S parameter
        S = abs(correlations[0] - correlations[1] + correlations[2] + correlations[3])
        
        return S
    
    def _measure_at_angle(self, state_id: str, angle: float) -> int:
        """Simulate measurement at specific angle."""
        # Simplified: rotate and measure
        prob_0 = math.cos(angle / 2) ** 2
        return 0 if self.rng.random_float() < prob_0 else 1
    
    def measure_entangled(self, state_id: str) -> Tuple[str, float]:
        """Measure an entangled state, affecting partner."""
        with self._lock:
            if state_id not in self.states:
                raise KeyError(f"Unknown state: {state_id}")
            
            state = self.states[state_id]
            
            # Measure
            result, prob = state.measure(self.rng)
            
            # Collapse entangled partners
            for partner_id in state.entangled_with:
                if partner_id in self.states:
                    partner = self.states[partner_id]
                    # Anti-correlate for Bell states
                    partner_result = "1" if result == "0" else "0"
                    partner.amplitudes = {partner_result: complex(1.0, 0)}
                    partner.state = CoherencyState.COLLAPSED
                    partner.coherency = 0.0
            
            return result, prob
    
    def get_state(self, state_id: str) -> Optional[QuantumState]:
        """Get a quantum state."""
        with self._lock:
            return self.states.get(state_id)
    
    def get_link(self, state_a: str, state_b: str) -> Optional[EntanglementLink]:
        """Get entanglement link between two states."""
        link_id = f"{state_a}:{state_b}"
        alt_id = f"{state_b}:{state_a}"
        
        with self._lock:
            return self.links.get(link_id) or self.links.get(alt_id)


class CoherencySynchronizer:
    """Synchronize distributed states with coherency maintenance."""
    
    def __init__(self, node_id: str, rng: Optional[QuantumRNG] = None):
        self.node_id = node_id
        self.rng = rng or QuantumRNG()
        self.local_states: Dict[str, QuantumState] = {}
        self.remote_states: Dict[str, Dict[str, QuantumState]] = defaultdict(dict)
        self.entanglement = EntanglementManager(rng)
        self.decay_rate: float = 0.001
        self.sync_interval: float = 1.0
        self._sync_thread: Optional[threading.Thread] = None
        self._stop_sync = threading.Event()
        self._callbacks: List[Callable[[str, Any], None]] = []
        self._lock = threading.Lock()
    
    def register_state(self, state_id: str, initial_value: Any = None) -> QuantumState:
        """Register a local state for synchronization."""
        bases = [str(initial_value)] if initial_value is not None else ["0", "1"]
        
        state = QuantumState(
            id=f"{self.node_id}:{state_id}",
            amplitudes={b: complex(1.0 / len(bases), 0) for b in bases},
            metadata={"node": self.node_id, "local_id": state_id}
        )
        
        with self._lock:
            self.local_states[state_id] = state
        
        return state
    
    def update_state(self, state_id: str, value: Any) -> None:
        """Update a local state."""
        with self._lock:
            if state_id not in self.local_states:
                self.register_state(state_id, value)
                return
            
            state = self.local_states[state_id]
            
            # Update amplitudes to favor new value
            for k in state.amplitudes:
                state.amplitudes[k] *= complex(0.9, 0)
            
            str_value = str(value)
            state.amplitudes[str_value] = state.amplitudes.get(str_value, complex(0, 0))
            state.amplitudes[str_value] += complex(0.5, 0)
            
            state.normalize()
            state.last_sync = time.time()
            state.coherency = 1.0
    
    def get_state(self, state_id: str) -> Optional[Any]:
        """Get current value of a state."""
        with self._lock:
            if state_id not in self.local_states:
                return None
            
            state = self.local_states[state_id]
            
            # Return most probable basis
            if state.amplitudes:
                return max(state.amplitudes.keys(), key=lambda k: state.probability(k))
            
            return None
    
    def entangle_with_remote(self, local_state: str, remote_node: str, remote_state: str) -> None:
        """Create entanglement with a remote state."""
        local_full_id = f"{self.node_id}:{local_state}"
        remote_full_id = f"{remote_node}:{remote_state}"
        
        self.entanglement.entangle(local_full_id, remote_full_id)
    
    def sync_with_remote(self, remote_node: str, remote_states: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize with remote node states.
        
        Returns conflict resolutions.
        """
        conflicts = {}
        
        with self._lock:
            for state_id, remote_value in remote_states.items():
                if state_id in self.local_states:
                    local_state = self.local_states[state_id]
                    
                    # Check for conflict
                    local_prob = local_state.probability(str(remote_value))
                    
                    if local_prob < 0.5:
                        # Conflict detected
                        # Use quantum-inspired resolution
                        resolution = self._resolve_conflict(local_state, remote_value)
                        conflicts[state_id] = resolution
                        
                        # Notify callbacks
                        for cb in self._callbacks:
                            cb(state_id, resolution)
                else:
                    # New state from remote
                    self.register_state(state_id, remote_value)
        
        return conflicts
    
    def _resolve_conflict(self, local_state: QuantumState, remote_value: Any) -> Any:
        """Resolve conflict using quantum-inspired approach."""
        # Create superposition of local and remote values
        local_value = max(local_state.amplitudes.keys(), key=lambda k: local_state.probability(k))
        
        # Weight by coherency
        local_weight = local_state.coherency
        remote_weight = 1.0 - local_weight * 0.5  # Slight bias toward remote
        
        # Interfere and collapse
        states = [
            (complex(local_weight, 0), local_value),
            (complex(remote_weight, 0), remote_value)
        ]
        
        return self.rng.quantum_superposition(states)
    
    def apply_decay(self) -> None:
        """Apply coherency decay to all states."""
        with self._lock:
            current_time = time.time()
            
            for state in self.local_states.values():
                time_since_sync = current_time - state.last_sync
                state.coherency *= math.exp(-self.decay_rate * time_since_sync)
                
                if state.coherency < 0.3:
                    state.state = CoherencyState.DECOHERING
                if state.coherency < 0.1:
                    state.state = CoherencyState.DECOHERENT
    
    def revive_coherency(self, state_id: str) -> None:
        """Attempt to revive decohered state."""
        with self._lock:
            if state_id in self.local_states:
                state = self.local_states[state_id]
                state.coherency = 0.5
                state.state = CoherencyState.COHERENT
                state.last_sync = time.time()
    
    def on_sync(self, callback: Callable[[str, Any], None]) -> None:
        """Register callback for sync events."""
        self._callbacks.append(callback)
    
    def start_continuous_sync(self) -> None:
        """Start continuous synchronization thread."""
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
    
    def _sync_loop(self) -> None:
        """Continuous synchronization loop."""
        while not self._stop_sync.wait(timeout=self.sync_interval):
            self.apply_decay()
    
    def stop_sync(self) -> None:
        """Stop continuous synchronization."""
        self._stop_sync.set()
        if self._sync_thread:
            self._sync_thread.join()
    
    def get_status(self) -> Dict[str, Any]:
        """Get synchronization status."""
        with self._lock:
            return {
                "node_id": self.node_id,
                "local_states": len(self.local_states),
                "entangled_pairs": len(self.entanglement.links),
                "states": {
                    sid: {
                        "coherency": s.coherency,
                        "state": s.state.name,
                        "entangled_with": list(s.entangled_with)
                    }
                    for sid, s in self.local_states.items()
                }
            }


class DistributedConsensus:
    """Achieve consensus across distributed nodes using quantum-inspired voting."""
    
    def __init__(self, nodes: List[str], rng: Optional[QuantumRNG] = None):
        self.nodes = nodes
        self.rng = rng or QuantumRNG()
        self.votes: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.consensus_states: Dict[str, Any] = {}
    
    def submit_vote(self, node: str, proposal: str, value: Any, weight: float = 1.0) -> None:
        """Submit a vote for a proposal."""
        self.votes[proposal][node] = {"value": value, "weight": weight}
    
    def reach_consensus(self, proposal: str, threshold: float = 0.66) -> Optional[Any]:
        """Reach consensus on a proposal.
        
        Uses quantum-inspired superposition of votes.
        """
        if proposal not in self.votes:
            return None
        
        votes = self.votes[proposal]
        
        if len(votes) < len(self.nodes) * threshold:
            return None  # Not enough votes
        
        # Group by value
        value_weights: Dict[Any, float] = defaultdict(float)
        for vote in votes.values():
            value_weights[vote["value"]] += vote["weight"]
        
        # Normalize
        total = sum(value_weights.values())
        if total == 0:
            return None
        
        # Create superposition
        states = [
            (complex(w / total, 0), v)
            for v, w in value_weights.items()
        ]
        
        # Collapse to consensus
        consensus = self.rng.quantum_superposition(states)
        self.consensus_states[proposal] = consensus
        
        return consensus
    
    def get_consensus(self, proposal: str) -> Optional[Any]:
        """Get reached consensus for a proposal."""
        return self.consensus_states.get(proposal)


# Convenience functions
_sync: Optional[CoherencySynchronizer] = None


def initialize(node_id: str) -> CoherencySynchronizer:
    """Initialize global synchronizer."""
    global _sync
    _sync = CoherencySynchronizer(node_id)
    return _sync


def get_sync() -> CoherencySynchronizer:
    """Get global synchronizer."""
    if _sync is None:
        return initialize("default")
    return _sync
