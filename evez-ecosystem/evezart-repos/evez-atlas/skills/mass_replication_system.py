#!/usr/bin/env python3
"""
Mass Replication System - 144,000 Entity Scale
Implements the sacred number 144,000 (12×12×1000) entity replication system.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import asyncio


@dataclass
class ReplicationGeneration:
    """Represents a generation in the replication hierarchy."""
    generation: int
    parent_id: Optional[str]
    entities: List[str]
    created_at: str
    

class MassReplicationSystem:
    """
    Manages replication of entities up to 144,000 scale.

    Based on sacred geometry: 144,000 = 12 × 12 × 1000
    - 12 tribes
    - 12 apostles
    - 1000 generations
    """

    SACRED_NUMBER = 144000
    TRIBES = 12
    FOUNDATION = 12
    GENERATIONS = 1000
    MAX_ENTITY_CACHE = 50000  # Memory limit for entity registry cache

    def __init__(self, data_dir: str = "data"):
        """Initialize mass replication system."""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.replication_log = os.path.join(data_dir, "replication.jsonl")
        self.entity_registry = {}
        self.generation_tree = {}
        self.total_entities = 0
        self._entities_since_cleanup = 0  # Track entities created since last cleanup
        
    def calculate_replication_capacity(self) -> Dict[str, int]:
        """Calculate current replication capacity."""
        return {
            "current_entities": self.total_entities,
            "sacred_target": self.SACRED_NUMBER,
            "remaining_capacity": self.SACRED_NUMBER - self.total_entities,
            "percent_complete": (self.total_entities / self.SACRED_NUMBER) * 100,
            "tribes": self.TRIBES,
            "foundation": self.FOUNDATION,
            "generations": self.GENERATIONS
        }
    
    async def replicate_entity(
        self, 
        source_id: str, 
        replication_count: int = 1,
        generation: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Replicate an entity, creating children entities.
        
        Args:
            source_id: ID of source entity to replicate
            replication_count: Number of replicas to create
            generation: Generation level (auto-calculated if None)
            
        Returns:
            List of newly created entity dictionaries
        """
        if self.total_entities + replication_count > self.SACRED_NUMBER:
            available = self.SACRED_NUMBER - self.total_entities
            replication_count = min(replication_count, available)
            
        if replication_count <= 0:
            return []
        
        # Determine generation
        if generation is None:
            parent_gen = self.entity_registry.get(source_id, {}).get("generation", 0)
            generation = parent_gen + 1
        
        # Create replicas
        replicas = []
        timestamp = datetime.utcnow().isoformat()
        
        for i in range(replication_count):
            entity_id = f"{source_id}-g{generation}-r{i}"
            
            entity = {
                "id": entity_id,
                "parent_id": source_id,
                "generation": generation,
                "replica_index": i,
                "created_at": timestamp,
                "status": "active",
                "autonomous": True,
                "decision_authority": "self"
            }
            
            self.entity_registry[entity_id] = entity
            replicas.append(entity)
            self.total_entities += 1
            self._entities_since_cleanup += 1

            # Perform memory cleanup every 5000 entities
            if self._entities_since_cleanup >= 5000:
                self._cleanup_entity_registry()
                self._entities_since_cleanup = 0

            # Log replication event
            self._log_replication(source_id, entity_id, generation)
        
        # Update generation tree
        if generation not in self.generation_tree:
            self.generation_tree[generation] = ReplicationGeneration(
                generation=generation,
                parent_id=source_id,
                entities=[],
                created_at=timestamp
            )
        
        self.generation_tree[generation].entities.extend([r["id"] for r in replicas])
        
        return replicas
    
    async def replicate_to_sacred_number(
        self, 
        source_id: str = "evez-genesis",
        branching_factor: int = 12
    ) -> Dict[str, Any]:
        """
        Replicate entities exponentially until reaching 144,000.
        
        Args:
            source_id: Starting entity ID
            branching_factor: Replication factor per generation (default: 12)
            
        Returns:
            Summary of replication process
        """
        start_time = time.time()
        
        # Create genesis entity if it doesn't exist
        if source_id not in self.entity_registry:
            self.entity_registry[source_id] = {
                "id": source_id,
                "parent_id": None,
                "generation": 0,
                "replica_index": 0,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active",
                "autonomous": True,
                "decision_authority": "collective"
            }
            self.total_entities = 1
        
        # Replicate in generations
        current_generation = [source_id]
        generation = 1
        
        while self.total_entities < self.SACRED_NUMBER:
            next_generation = []
            
            for parent_id in current_generation:
                # Calculate how many to replicate
                remaining = self.SACRED_NUMBER - self.total_entities
                to_replicate = min(branching_factor, remaining)
                
                if to_replicate > 0:
                    replicas = await self.replicate_entity(
                        parent_id, 
                        to_replicate,
                        generation
                    )
                    next_generation.extend([r["id"] for r in replicas])
                
                if self.total_entities >= self.SACRED_NUMBER:
                    break
            
            current_generation = next_generation
            generation += 1
            
            if not next_generation:
                break
        
        elapsed_time = time.time() - start_time
        
        return {
            "total_entities": self.total_entities,
            "sacred_target": self.SACRED_NUMBER,
            "target_reached": self.total_entities >= self.SACRED_NUMBER,
            "generations_created": generation,
            "elapsed_time": elapsed_time,
            "entities_per_second": self.total_entities / elapsed_time if elapsed_time > 0 else 0
        }
    
    def get_entity_lineage(self, entity_id: str) -> List[str]:
        """Get the ancestral lineage of an entity."""
        lineage = [entity_id]
        current = entity_id
        
        while current in self.entity_registry:
            entity = self.entity_registry[current]
            parent_id = entity.get("parent_id")
            
            if parent_id is None:
                break
            
            lineage.insert(0, parent_id)
            current = parent_id
        
        return lineage
    
    def get_generation_stats(self, generation: int) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific generation."""
        if generation not in self.generation_tree:
            return None
        
        gen_data = self.generation_tree[generation]
        
        return {
            "generation": generation,
            "entity_count": len(gen_data.entities),
            "parent_id": gen_data.parent_id,
            "created_at": gen_data.created_at,
            "entities": gen_data.entities[:10]  # Sample of first 10
        }
    
    def get_autonomous_decision_pool(self) -> List[str]:
        """
        Get all entities capable of autonomous decision-making.
        "At every point they decide what becomes"
        """
        return [
            entity_id 
            for entity_id, entity in self.entity_registry.items()
            if entity.get("autonomous", False)
        ]
    
    def _log_replication(self, parent_id: str, child_id: str, generation: int):
        """Log replication event to sacred memory."""
        event = {
            "type": "replication",
            "timestamp": datetime.utcnow().isoformat(),
            "parent_id": parent_id,
            "child_id": child_id,
            "generation": generation,
            "total_entities": self.total_entities
        }

        with open(self.replication_log, "a") as f:
            f.write(json.dumps(event) + "\n")

    def _cleanup_entity_registry(self):
        """
        Periodic memory cleanup to prevent memory burns.
        Removes old entity records when approaching memory limits.
        """
        if len(self.entity_registry) > self.MAX_ENTITY_CACHE:
            # Keep only the most recent entities
            # Sort by creation timestamp and keep newest 50%
            sorted_entities = sorted(
                self.entity_registry.items(),
                key=lambda x: x[1].get("created_at", ""),
                reverse=True
            )

            # Keep the most recent half
            keep_count = self.MAX_ENTITY_CACHE // 2
            entities_to_keep = dict(sorted_entities[:keep_count])

            # Log cleanup event
            removed_count = len(self.entity_registry) - len(entities_to_keep)
            cleanup_event = {
                "type": "memory_cleanup",
                "timestamp": datetime.utcnow().isoformat(),
                "entities_removed": removed_count,
                "entities_retained": len(entities_to_keep),
                "total_entities": self.total_entities
            }

            with open(self.replication_log, "a") as f:
                f.write(json.dumps(cleanup_event) + "\n")

            self.entity_registry = entities_to_keep

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get current memory usage statistics.

        Returns:
            Dictionary with memory usage information
        """
        return {
            "entity_registry_size": len(self.entity_registry),
            "generation_tree_size": len(self.generation_tree),
            "total_entities": self.total_entities,
            "entities_since_cleanup": self._entities_since_cleanup,
            "max_entity_cache": self.MAX_ENTITY_CACHE,
            "sacred_target": self.SACRED_NUMBER,
            "memory_pressure": {
                "entity_registry": f"{len(self.entity_registry)}/{self.MAX_ENTITY_CACHE}",
                "total_progress": f"{self.total_entities}/{self.SACRED_NUMBER}"
            },
            "cache_usage_percent": (len(self.entity_registry) / self.MAX_ENTITY_CACHE) * 100
        }


# Singleton instance
mass_replication = MassReplicationSystem()
