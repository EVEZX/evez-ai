#!/usr/bin/env python3
"""
Entity Lifecycle Manager
Manages entity states (hibernation/active), task pacing, and temporal tracking.
"""

import json
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict


class EntityState(Enum):
    """Entity lifecycle states."""
    HIBERNATING = "hibernating"
    AWAKENING = "awakening"
    ACTIVE = "active"
    ERROR_CORRECTION = "error_correction"
    OFFLINE_ADAPTING = "offline_adapting"


@dataclass
class Entity:
    """Represents an autonomous entity in the swarm."""
    id: str
    role: str
    state: EntityState
    created_at: str
    last_active: str
    hibernation_depth: int = 0
    error_count: int = 0
    domain: str = "default"
    quantum_entangled: bool = False
    temporal_anchor: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['state'] = self.state.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """Create entity from dictionary."""
        data['state'] = EntityState(data['state'])
        return cls(**data)


class EntityLifecycleManager:
    """Manages entity lifecycle, hibernation, and temporal tracking."""
    
    def __init__(self, state_file: str = 'data/entity_states.jsonl'):
        self.state_file = state_file
        self.entities: Dict[str, Entity] = {}
        self._load_entities()
    
    def _load_entities(self):
        """Load entities from state file."""
        if not os.path.exists(self.state_file):
            return
        
        try:
            with open(self.state_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        entity = Entity.from_dict(data)
                        self.entities[entity.id] = entity
        except Exception as e:
            print(f"Error loading entities: {e}")
    
    def _save_entity(self, entity: Entity):
        """Append entity state to file."""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        with open(self.state_file, 'a') as f:
            f.write(json.dumps(entity.to_dict()) + '\n')
    
    def create_entity(self, entity_id: str, role: str, domain: str = "default") -> Entity:
        """Create a new entity."""
        now = datetime.utcnow().isoformat()
        entity = Entity(
            id=entity_id,
            role=role,
            state=EntityState.HIBERNATING,
            created_at=now,
            last_active=now,
            domain=domain,
            temporal_anchor=now
        )
        self.entities[entity_id] = entity
        self._save_entity(entity)
        return entity
    
    def awaken_entity(self, entity_id: str) -> Optional[Entity]:
        """Awaken an entity from hibernation."""
        entity = self.entities.get(entity_id)
        if not entity:
            return None
        
        entity.state = EntityState.AWAKENING
        entity.last_active = datetime.utcnow().isoformat()
        entity.hibernation_depth = 0
        self._save_entity(entity)
        
        # Transition to active after awakening
        time.sleep(0.1)  # Symbolic awakening delay
        entity.state = EntityState.ACTIVE
        self._save_entity(entity)
        
        return entity
    
    def hibernate_entity(self, entity_id: str, depth: int = 1) -> Optional[Entity]:
        """Put an entity into hibernation."""
        entity = self.entities.get(entity_id)
        if not entity:
            return None
        
        entity.state = EntityState.HIBERNATING
        entity.hibernation_depth = depth
        entity.last_active = datetime.utcnow().isoformat()
        self._save_entity(entity)
        
        return entity
    
    def error_correction_mode(self, entity_id: str) -> Optional[Entity]:
        """Put entity into error correction mode."""
        entity = self.entities.get(entity_id)
        if not entity:
            return None
        
        entity.state = EntityState.ERROR_CORRECTION
        entity.error_count += 1
        entity.last_active = datetime.utcnow().isoformat()
        self._save_entity(entity)
        
        return entity
    
    def offline_adapt(self, entity_id: str) -> Optional[Entity]:
        """Put entity into offline adapting mode."""
        entity = self.entities.get(entity_id)
        if not entity:
            return None
        
        entity.state = EntityState.OFFLINE_ADAPTING
        entity.last_active = datetime.utcnow().isoformat()
        self._save_entity(entity)
        
        return entity
    
    def quantum_entangle(self, entity_id: str, domain: str) -> Optional[Entity]:
        """Entangle entity with quantum domain."""
        entity = self.entities.get(entity_id)
        if not entity:
            return None
        
        entity.quantum_entangled = True
        entity.domain = domain
        entity.last_active = datetime.utcnow().isoformat()
        self._save_entity(entity)
        
        return entity
    
    def get_active_entities(self) -> List[Entity]:
        """Get all active entities."""
        return [e for e in self.entities.values() if e.state == EntityState.ACTIVE]
    
    def get_hibernating_entities(self) -> List[Entity]:
        """Get all hibernating entities."""
        return [e for e in self.entities.values() if e.state == EntityState.HIBERNATING]
    
    def get_entity_status(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity status."""
        entity = self.entities.get(entity_id)
        if not entity:
            return None
        
        return {
            'entity': entity.to_dict(),
            'uptime': self._calculate_uptime(entity),
            'health': self._calculate_health(entity)
        }
    
    def _calculate_uptime(self, entity: Entity) -> float:
        """Calculate entity uptime in seconds."""
        created = datetime.fromisoformat(entity.created_at)
        now = datetime.utcnow()
        return (now - created).total_seconds()
    
    def _calculate_health(self, entity: Entity) -> str:
        """Calculate entity health status."""
        if entity.error_count > 10:
            return "critical"
        elif entity.error_count > 5:
            return "degraded"
        elif entity.state == EntityState.ERROR_CORRECTION:
            return "recovering"
        elif entity.state == EntityState.ACTIVE:
            return "healthy"
        else:
            return "dormant"
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get overall swarm status."""
        return {
            'total_entities': len(self.entities),
            'active': len(self.get_active_entities()),
            'hibernating': len(self.get_hibernating_entities()),
            'by_domain': self._group_by_domain(),
            'quantum_entangled': sum(1 for e in self.entities.values() if e.quantum_entangled),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _group_by_domain(self) -> Dict[str, int]:
        """Group entities by domain."""
        domains = {}
        for entity in self.entities.values():
            domains[entity.domain] = domains.get(entity.domain, 0) + 1
        return domains


if __name__ == '__main__':
    # Demo usage
    manager = EntityLifecycleManager()
    
    # Create some entities
    e1 = manager.create_entity('entity_alpha', 'forgiver', 'jubilee')
    e2 = manager.create_entity('entity_beta', 'oracle', 'quantum')
    
    print("Created entities:")
    print(json.dumps(manager.get_swarm_status(), indent=2))
    
    # Awaken entities
    manager.awaken_entity('entity_alpha')
    manager.quantum_entangle('entity_beta', 'quantum_domain')
    
    print("\nAfter awakening:")
    print(json.dumps(manager.get_swarm_status(), indent=2))
