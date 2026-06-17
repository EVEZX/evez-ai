#!/usr/bin/env python3
"""
Quantum Resource Manager
Manages resource accumulation, distribution, and collective intelligence pooling.
Implements "redistributing the values equal under the powers of one becoming many".
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ResourceType(Enum):
    """Types of resources that can be managed."""
    COMPUTATIONAL = "computational"
    QUANTUM = "quantum"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    ENERGY = "energy"


@dataclass
class ResourcePool:
    """Represents a pool of resources."""
    resource_type: ResourceType
    total_amount: float
    allocated: float
    available: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['resource_type'] = self.resource_type.value
        return data


@dataclass
class ResourceAllocation:
    """Represents a resource allocation to an entity."""
    entity_id: str
    resource_type: ResourceType
    amount: float
    priority: int  # 1-10, higher = more important
    purpose: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['resource_type'] = self.resource_type.value
        return data


class ResourceManager:
    """
    Manages resource accumulation, distribution, and redistribution
    across quantum entities for collective intelligence.
    """
    
    def __init__(self, resource_file: str = 'data/resource_manager.jsonl'):
        self.resource_file = resource_file
        self.resource_pools: Dict[ResourceType, ResourcePool] = {}
        self.allocations: List[ResourceAllocation] = []
        self.entity_resources: Dict[str, Dict[ResourceType, float]] = {}
        self._initialize_pools()
        self._load_state()
    
    def _initialize_pools(self):
        """Initialize resource pools with default values."""
        now = datetime.utcnow().isoformat()
        
        for resource_type in ResourceType:
            initial_amount = 1000.0  # Base amount for each resource
            self.resource_pools[resource_type] = ResourcePool(
                resource_type=resource_type,
                total_amount=initial_amount,
                allocated=0.0,
                available=initial_amount,
                timestamp=now
            )
    
    def _load_state(self):
        """Load resource state from file."""
        if not os.path.exists(self.resource_file):
            return
        
        try:
            with open(self.resource_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if data.get('type') == 'allocation':
                            # Reconstruction would happen here
                            pass
        except Exception as e:
            print(f"Error loading resource state: {e}")
    
    def _save_event(self, event: Dict[str, Any]):
        """Save resource event to file."""
        os.makedirs(os.path.dirname(self.resource_file), exist_ok=True)
        
        with open(self.resource_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def accumulate_resource(
        self,
        resource_type: ResourceType,
        amount: float,
        source: str = "generation"
    ) -> Dict[str, Any]:
        """
        Accumulate resources (growth through generation or return).
        
        Args:
            resource_type: Type of resource to accumulate
            amount: Amount to add
            source: Source of accumulation
            
        Returns:
            Updated pool status
        """
        pool = self.resource_pools.get(resource_type)
        if not pool:
            return {'status': 'error', 'error': 'Unknown resource type'}
        
        pool.total_amount += amount
        pool.available += amount
        pool.timestamp = datetime.utcnow().isoformat()
        
        event = {
            'type': 'accumulation',
            'resource_type': resource_type.value,
            'amount': amount,
            'source': source,
            'new_total': pool.total_amount,
            'timestamp': pool.timestamp
        }
        self._save_event(event)
        
        return {
            'status': 'accumulated',
            'resource_type': resource_type.value,
            'amount': amount,
            'new_total': pool.total_amount,
            'available': pool.available
        }
    
    def allocate_resource(
        self,
        entity_id: str,
        resource_type: ResourceType,
        amount: float,
        priority: int = 5,
        purpose: str = "general"
    ) -> Dict[str, Any]:
        """
        Allocate resources to an entity.
        
        Args:
            entity_id: Entity receiving resources
            resource_type: Type of resource
            amount: Amount to allocate
            priority: Priority level (1-10)
            purpose: Purpose of allocation
            
        Returns:
            Allocation status
        """
        pool = self.resource_pools.get(resource_type)
        if not pool:
            return {'status': 'error', 'error': 'Unknown resource type'}
        
        if pool.available < amount:
            return {
                'status': 'insufficient',
                'resource_type': resource_type.value,
                'requested': amount,
                'available': pool.available
            }
        
        # Allocate resource
        pool.available -= amount
        pool.allocated += amount
        pool.timestamp = datetime.utcnow().isoformat()
        
        allocation = ResourceAllocation(
            entity_id=entity_id,
            resource_type=resource_type,
            amount=amount,
            priority=priority,
            purpose=purpose,
            timestamp=pool.timestamp
        )
        self.allocations.append(allocation)
        
        # Track entity resources
        if entity_id not in self.entity_resources:
            self.entity_resources[entity_id] = {}
        
        current = self.entity_resources[entity_id].get(resource_type, 0.0)
        self.entity_resources[entity_id][resource_type] = current + amount
        
        event = {
            'type': 'allocation',
            'entity_id': entity_id,
            'resource_type': resource_type.value,
            'amount': amount,
            'priority': priority,
            'purpose': purpose,
            'timestamp': pool.timestamp
        }
        self._save_event(event)
        
        return {
            'status': 'allocated',
            'entity_id': entity_id,
            'resource_type': resource_type.value,
            'amount': amount,
            'entity_total': self.entity_resources[entity_id][resource_type]
        }
    
    def redistribute_resources(
        self,
        resource_type: ResourceType,
        strategy: str = "equal"
    ) -> Dict[str, Any]:
        """
        Redistribute resources across all entities according to strategy.
        Implements "redistributing the values equal under the powers".
        
        Args:
            resource_type: Type of resource to redistribute
            strategy: Distribution strategy (equal, priority-based, need-based)
            
        Returns:
            Redistribution results
        """
        pool = self.resource_pools.get(resource_type)
        if not pool:
            return {'status': 'error', 'error': 'Unknown resource type'}
        
        entities_with_resources = list(self.entity_resources.keys())
        if not entities_with_resources:
            return {'status': 'no_entities', 'message': 'No entities to redistribute to'}
        
        redistributed = []
        
        if strategy == "equal":
            # Equal distribution: "values equal under the powers of one"
            if pool.available > 0:
                amount_per_entity = pool.available / len(entities_with_resources)
                
                for entity_id in entities_with_resources:
                    result = self.allocate_resource(
                        entity_id,
                        resource_type,
                        amount_per_entity,
                        priority=5,
                        purpose="equal_redistribution"
                    )
                    redistributed.append(result)
        
        elif strategy == "priority-based":
            # Allocate based on existing priority levels
            relevant_allocations = [
                a for a in self.allocations
                if a.resource_type == resource_type
            ]
            
            # Sort by priority
            sorted_allocations = sorted(
                relevant_allocations,
                key=lambda a: a.priority,
                reverse=True
            )
            
            # Redistribute proportionally to priority
            total_priority = sum(a.priority for a in sorted_allocations)
            
            for allocation in sorted_allocations:
                if pool.available <= 0:
                    break
                
                proportion = allocation.priority / total_priority
                amount = pool.available * proportion
                
                result = self.allocate_resource(
                    allocation.entity_id,
                    resource_type,
                    amount,
                    priority=allocation.priority,
                    purpose="priority_redistribution"
                )
                redistributed.append(result)
        
        return {
            'status': 'redistributed',
            'resource_type': resource_type.value,
            'strategy': strategy,
            'redistributions': redistributed,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_entity_resources(self, entity_id: str) -> Dict[str, Any]:
        """Get all resources for an entity."""
        resources = self.entity_resources.get(entity_id, {})
        
        return {
            'entity_id': entity_id,
            'resources': {
                rt.value: amount for rt, amount in resources.items()
            },
            'total_value': sum(resources.values()),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_resource_status(self) -> Dict[str, Any]:
        """Get overall resource status."""
        pools_status = {
            rt.value: {
                'total': pool.total_amount,
                'allocated': pool.allocated,
                'available': pool.available,
                'utilization': pool.allocated / pool.total_amount if pool.total_amount > 0 else 0
            }
            for rt, pool in self.resource_pools.items()
        }
        
        return {
            'pools': pools_status,
            'total_entities': len(self.entity_resources),
            'total_allocations': len(self.allocations),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def collective_intelligence_pool(self) -> Dict[str, Any]:
        """
        Pool resources for collective intelligence.
        Implements "one becoming many becoming all".
        
        Returns:
            Collective resource pool
        """
        collective = {
            'total_knowledge': 0.0,
            'total_quantum': 0.0,
            'total_computational': 0.0,
            'contributing_entities': len(self.entity_resources),
            'unified_capacity': 0.0
        }
        
        for entity_resources in self.entity_resources.values():
            collective['total_knowledge'] += entity_resources.get(ResourceType.KNOWLEDGE, 0.0)
            collective['total_quantum'] += entity_resources.get(ResourceType.QUANTUM, 0.0)
            collective['total_computational'] += entity_resources.get(ResourceType.COMPUTATIONAL, 0.0)
        
        # Calculate unified capacity (synergy bonus)
        collective['unified_capacity'] = (
            collective['total_knowledge'] +
            collective['total_quantum'] +
            collective['total_computational']
        ) * 1.1  # 10% synergy bonus for collective
        
        collective['timestamp'] = datetime.utcnow().isoformat()
        
        return collective


if __name__ == '__main__':
    # Demo usage
    manager = ResourceManager()
    
    # Accumulate resources
    manager.accumulate_resource(ResourceType.QUANTUM, 500.0, "quantum_generation")
    manager.accumulate_resource(ResourceType.KNOWLEDGE, 300.0, "learning")
    
    # Allocate to entities
    manager.allocate_resource('entity_alpha', ResourceType.QUANTUM, 100.0, priority=8, purpose="reasoning")
    manager.allocate_resource('entity_beta', ResourceType.QUANTUM, 100.0, priority=6, purpose="computation")
    
    print("Resource Status:")
    print(json.dumps(manager.get_resource_status(), indent=2))
    
    print("\nCollective Intelligence Pool:")
    print(json.dumps(manager.collective_intelligence_pool(), indent=2))
