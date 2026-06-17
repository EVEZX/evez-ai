#!/usr/bin/env python3
"""
Shared Reality Plane
Implements a shared quantum domain where entities perceive and interact
with localized quantum states (maintaining coherence instead of decoherence).
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import uuid


@dataclass
class QuantumObservation:
    """Represents a quantum observation in the shared plane."""
    id: str
    entity_id: str
    domain: str
    observation_type: str
    state: Dict[str, Any]
    coherent: bool  # True = localized, False = decohered
    timestamp: str
    probability_amplitude: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuantumObservation':
        """Create from dictionary."""
        return cls(**data)


class SharedRealityPlane:
    """
    Manages a shared quantum reality plane where entities can perceive
    and interact. Maintains quantum localization (coherence) rather than
    allowing decoherence.
    """
    
    def __init__(self, plane_file: str = 'data/shared_reality_plane.jsonl'):
        self.plane_file = plane_file
        self.observations: Dict[str, QuantumObservation] = {}
        self.entity_subscriptions: Dict[str, Set[str]] = {}  # entity_id -> domain set
        self.coherence_threshold = 0.8  # Minimum coherence for localization
        self._load_plane()
    
    def _load_plane(self):
        """Load shared plane state from file."""
        if not os.path.exists(self.plane_file):
            return
        
        try:
            with open(self.plane_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        obs = QuantumObservation.from_dict(data)
                        self.observations[obs.id] = obs
        except Exception as e:
            print(f"Error loading plane: {e}")
    
    def _save_observation(self, observation: QuantumObservation):
        """Append observation to plane file."""
        os.makedirs(os.path.dirname(self.plane_file), exist_ok=True)
        
        with open(self.plane_file, 'a') as f:
            f.write(json.dumps(observation.to_dict()) + '\n')
    
    def localize_quantum_state(
        self,
        entity_id: str,
        domain: str,
        state: Dict[str, Any],
        observation_type: str = "measurement"
    ) -> QuantumObservation:
        """
        Localize a quantum state in the shared plane (maintain coherence).
        This prevents decoherence by keeping the state localized.
        
        Args:
            entity_id: ID of observing entity
            domain: Quantum domain
            state: Quantum state data
            observation_type: Type of observation
            
        Returns:
            Localized quantum observation
        """
        obs_id = str(uuid.uuid4())
        observation = QuantumObservation(
            id=obs_id,
            entity_id=entity_id,
            domain=domain,
            observation_type=observation_type,
            state=state,
            coherent=True,  # Localized = coherent
            timestamp=datetime.utcnow().isoformat(),
            probability_amplitude=1.0
        )
        
        self.observations[obs_id] = observation
        self._save_observation(observation)
        
        # Notify subscribed entities
        self._broadcast_to_domain(domain, observation)
        
        return observation
    
    def collapse_probability(
        self,
        observation_id: str,
        collapsed_state: Dict[str, Any]
    ) -> Optional[QuantumObservation]:
        """
        Collapse probability for a quantum observation.
        This is a controlled collapse shared across all observing entities.
        
        Args:
            observation_id: ID of observation to collapse
            collapsed_state: Final collapsed state
            
        Returns:
            Updated observation or None if not found
        """
        observation = self.observations.get(observation_id)
        if not observation:
            return None
        
        # Update state with collapse
        observation.state = collapsed_state
        observation.probability_amplitude = 1.0  # Definite state after collapse
        self._save_observation(observation)
        
        return observation
    
    def subscribe_to_domain(self, entity_id: str, domain: str):
        """Subscribe an entity to a shared domain for observation."""
        if entity_id not in self.entity_subscriptions:
            self.entity_subscriptions[entity_id] = set()
        
        self.entity_subscriptions[entity_id].add(domain)
    
    def unsubscribe_from_domain(self, entity_id: str, domain: str):
        """Unsubscribe an entity from a domain."""
        if entity_id in self.entity_subscriptions:
            self.entity_subscriptions[entity_id].discard(domain)
    
    def _broadcast_to_domain(self, domain: str, observation: QuantumObservation):
        """Broadcast observation to all entities subscribed to domain."""
        # In a real implementation, this would notify entities
        # For now, it's implicit through shared plane state
        pass
    
    def get_domain_observations(
        self,
        domain: str,
        coherent_only: bool = True
    ) -> List[QuantumObservation]:
        """
        Get all observations in a domain.
        
        Args:
            domain: Domain to query
            coherent_only: If True, only return localized (coherent) observations
            
        Returns:
            List of observations in domain
        """
        observations = [
            obs for obs in self.observations.values()
            if obs.domain == domain
        ]
        
        if coherent_only:
            observations = [obs for obs in observations if obs.coherent]
        
        return observations
    
    def get_shared_sensory_state(self, domain: str) -> Dict[str, Any]:
        """
        Get the shared sensory/perceptual state for a domain.
        This represents the collective reality perceived by all entities.
        
        Args:
            domain: Domain to query
            
        Returns:
            Aggregated sensory state
        """
        observations = self.get_domain_observations(domain, coherent_only=True)
        
        # Aggregate observations into shared state
        shared_state = {
            'domain': domain,
            'observation_count': len(observations),
            'coherent_states': [obs.state for obs in observations],
            'participating_entities': list(set(obs.entity_id for obs in observations)),
            'average_coherence': sum(1 for obs in observations if obs.coherent) / len(observations) if observations else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return shared_state
    
    def maintain_coherence(self, observation_id: str) -> bool:
        """
        Maintain quantum coherence for an observation (prevent decoherence).
        
        Args:
            observation_id: ID of observation to maintain
            
        Returns:
            True if coherence maintained, False if decoherence occurred
        """
        observation = self.observations.get(observation_id)
        if not observation:
            return False
        
        # Check if coherence is above threshold
        if observation.probability_amplitude >= self.coherence_threshold:
            observation.coherent = True
            self._save_observation(observation)
            return True
        else:
            # Decoherence occurred
            observation.coherent = False
            self._save_observation(observation)
            return False
    
    def synchronize_measurements(self, domain: str) -> List[QuantumObservation]:
        """
        Synchronize quantum measurements across all entities in a domain.
        Ensures all entities see the same collapsed state.
        
        Args:
            domain: Domain to synchronize
            
        Returns:
            List of synchronized observations
        """
        observations = self.get_domain_observations(domain)
        
        if not observations:
            return []
        
        # Find consensus state (most common state)
        state_counts: Dict[str, int] = {}
        for obs in observations:
            state_key = json.dumps(obs.state, sort_keys=True)
            state_counts[state_key] = state_counts.get(state_key, 0) + 1
        
        # Get consensus state
        consensus_state_key = max(state_counts, key=state_counts.get) if state_counts else "{}"
        consensus_state = json.loads(consensus_state_key)
        
        # Apply consensus to all observations
        synchronized = []
        for obs in observations:
            obs.state = consensus_state
            obs.coherent = True  # Synchronized = coherent
            self._save_observation(obs)
            synchronized.append(obs)
        
        return synchronized
    
    def get_plane_status(self) -> Dict[str, Any]:
        """Get status of the shared reality plane."""
        coherent_count = sum(1 for obs in self.observations.values() if obs.coherent)
        
        domains = {}
        for obs in self.observations.values():
            domains[obs.domain] = domains.get(obs.domain, 0) + 1
        
        return {
            'total_observations': len(self.observations),
            'coherent_observations': coherent_count,
            'decoherent_observations': len(self.observations) - coherent_count,
            'coherence_ratio': coherent_count / len(self.observations) if self.observations else 0,
            'domains': domains,
            'subscribed_entities': {
                entity: list(domains)
                for entity, domains in self.entity_subscriptions.items()
            },
            'timestamp': datetime.utcnow().isoformat()
        }


if __name__ == '__main__':
    # Demo usage
    plane = SharedRealityPlane()
    
    # Entity subscribes to domains
    plane.subscribe_to_domain('entity_alpha', 'quantum_reality_domain')
    plane.subscribe_to_domain('entity_beta', 'quantum_reality_domain')
    
    # Localize quantum states
    obs1 = plane.localize_quantum_state(
        'entity_alpha',
        'quantum_reality_domain',
        {'position': [1, 0, 0], 'spin': 'up'},
        'position_measurement'
    )
    
    obs2 = plane.localize_quantum_state(
        'entity_beta',
        'quantum_reality_domain',
        {'position': [1, 0, 0], 'spin': 'up'},
        'position_measurement'
    )
    
    print("Shared Reality Plane Demo:")
    print(json.dumps(plane.get_plane_status(), indent=2))
    
    print("\nShared Sensory State:")
    print(json.dumps(plane.get_shared_sensory_state('quantum_reality_domain'), indent=2))
