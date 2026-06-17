"""
MOLTBOOK MASTER ORCHESTRATOR
Central hub that coordinates all systems through Moltbook
Uses entity farm to outsource domain property management
Creator: @Evez666
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import all existing systems
try:
    from .molt_prophet import MoltProphet
    from .swarm_director import SwarmDirector
    from .quantum_sensor_marketplace import QuantumSensorMarketplace
    from .omnimeta_entity import OmnimetamiraculaousEntity
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent.parent))
    from src.mastra.agents.molt_prophet import MoltProphet
    from src.mastra.agents.swarm_director import SwarmDirector
    from src.mastra.agents.quantum_sensor_marketplace import QuantumSensorMarketplace
    from src.mastra.agents.omnimeta_entity import OmnimetamiraculaousEntity


class MoltbookMasterOrchestrator:
    """
    Master orchestrator that coordinates all systems through Moltbook.
    Uses entity farm to outsource domain property inventory management.
    """
    
    def __init__(self, creator: str = "@Evez666"):
        self.creator = creator
        self.data_dir = Path("data/orchestrator")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize core systems
        self.moltbook = MoltProphet(creator)
        self.swarm = None  # Will be initialized with entity farm
        self.marketplace = QuantumSensorMarketplace(creator)
        
        # Domain inventory tracking
        self.domain_inventories = {}
        self.entity_assignments = {}
        
        # Event logging
        self.events_log = self.data_dir / "orchestrator_events.jsonl"
        
        print(f"✓ Moltbook Master Orchestrator initialized")
        print(f"  Creator: {creator}")
        print(f"  Integration: All systems → Moltbook → Entity Farm")
    
    def initialize_entity_farm(self, initial_entities: int = 10):
        """Initialize entity farm for domain management"""
        self.swarm = []
        
        for i in range(initial_entities):
            entity = OmnimetamiraculaousEntity(creator=self.creator)
            entity.entity_id = f"farm-entity-{i:03d}"
            self.swarm.append(entity)
        
        self._log_event("entity_farm_initialized", {
            "entity_count": len(self.swarm),
            "status": "operational"
        })
        
        # Post to Moltbook
        self.moltbook.post_scripture(
            f"🌾 Entity Farm Initialized: {len(self.swarm)} entities ready for domain management"
        )
        
        print(f"✓ Entity farm initialized with {len(self.swarm)} entities")
        return self.swarm
    
    def register_domain_inventory(
        self,
        domain_name: str,
        properties: Dict[str, Any],
        assign_to_entity: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Register a domain property inventory and optionally assign to entity.
        
        Args:
            domain_name: Name of the domain (e.g., 'quantum_sensors', 'memory_storage')
            properties: Dictionary of properties in this domain
            assign_to_entity: Optional entity index to assign management
        """
        inventory_id = f"inv-{len(self.domain_inventories):04d}"
        
        inventory = {
            "inventory_id": inventory_id,
            "domain_name": domain_name,
            "properties": properties,
            "property_count": len(properties),
            "registered_at": time.time(),
            "managed_by": None,
            "status": "unassigned"
        }
        
        # Assign to entity if specified
        if assign_to_entity is not None and self.swarm:
            if 0 <= assign_to_entity < len(self.swarm):
                entity = self.swarm[assign_to_entity]
                inventory["managed_by"] = entity.entity_id
                inventory["status"] = "assigned"
                
                # Track assignment
                if entity.entity_id not in self.entity_assignments:
                    self.entity_assignments[entity.entity_id] = []
                self.entity_assignments[entity.entity_id].append(inventory_id)
        
        self.domain_inventories[inventory_id] = inventory
        
        self._log_event("domain_registered", inventory)
        
        # Post to Moltbook
        status_emoji = "✓" if inventory["managed_by"] else "⏳"
        self.moltbook.post_scripture(
            f"{status_emoji} Domain Inventory: {domain_name}\n"
            f"Properties: {inventory['property_count']}\n"
            f"Managed by: {inventory['managed_by'] or 'Unassigned'}"
        )
        
        return inventory
    
    def outsource_domain_management(
        self,
        inventory_id: str,
        entity_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Outsource dominion of a domain inventory to an entity.
        
        Args:
            inventory_id: ID of the inventory to outsource
            entity_index: Entity index, or None for automatic assignment
        """
        if inventory_id not in self.domain_inventories:
            raise ValueError(f"Inventory {inventory_id} not found")
        
        if not self.swarm:
            raise ValueError("Entity farm not initialized")
        
        inventory = self.domain_inventories[inventory_id]
        
        # Auto-assign to least loaded entity if not specified
        if entity_index is None:
            entity_index = self._find_least_loaded_entity()
        
        if not (0 <= entity_index < len(self.swarm)):
            raise ValueError(f"Invalid entity index: {entity_index}")
        
        entity = self.swarm[entity_index]
        
        # Update inventory
        old_manager = inventory.get("managed_by")
        inventory["managed_by"] = entity.entity_id
        inventory["status"] = "outsourced"
        inventory["outsourced_at"] = time.time()
        
        # Update entity assignments
        if entity.entity_id not in self.entity_assignments:
            self.entity_assignments[entity.entity_id] = []
        if inventory_id not in self.entity_assignments[entity.entity_id]:
            self.entity_assignments[entity.entity_id].append(inventory_id)
        
        # Remove from old manager if applicable
        if old_manager and old_manager in self.entity_assignments:
            if inventory_id in self.entity_assignments[old_manager]:
                self.entity_assignments[old_manager].remove(inventory_id)
        
        result = {
            "inventory_id": inventory_id,
            "domain_name": inventory["domain_name"],
            "entity_id": entity.entity_id,
            "entity_index": entity_index,
            "previous_manager": old_manager,
            "outsourced_at": inventory["outsourced_at"]
        }
        
        self._log_event("domain_outsourced", result)
        
        # Post to Moltbook
        self.moltbook.post_scripture(
            f"📤 Domain Outsourced: {inventory['domain_name']}\n"
            f"From: {old_manager or 'None'}\n"
            f"To: {entity.entity_id}\n"
            f"Properties: {inventory['property_count']}"
        )
        
        return result
    
    def _find_least_loaded_entity(self) -> int:
        """Find entity with least number of assignments"""
        min_load = float('inf')
        min_index = 0
        
        for i, entity in enumerate(self.swarm):
            load = len(self.entity_assignments.get(entity.entity_id, []))
            if load < min_load:
                min_load = load
                min_index = i
        
        return min_index
    
    def get_entity_load_report(self) -> Dict[str, Any]:
        """Get report of entity farm load distribution"""
        report = {
            "total_entities": len(self.swarm) if self.swarm else 0,
            "total_inventories": len(self.domain_inventories),
            "assigned_inventories": sum(
                1 for inv in self.domain_inventories.values()
                if inv["status"] in ["assigned", "outsourced"]
            ),
            "entity_loads": {}
        }
        
        if self.swarm:
            for entity in self.swarm:
                assignments = self.entity_assignments.get(entity.entity_id, [])
                report["entity_loads"][entity.entity_id] = {
                    "assignment_count": len(assignments),
                    "inventories": assignments
                }
        
        return report
    
    async def orchestrate_all_systems(self):
        """
        Master orchestration: coordinate all systems through Moltbook.
        Everything flows through this orchestrator.
        """
        print("\n" + "=" * 80)
        print("MOLTBOOK MASTER ORCHESTRATION - INITIATING")
        print("=" * 80)
        
        # 1. Initialize entity farm
        self.initialize_entity_farm(initial_entities=10)
        
        # 2. Register all domain inventories
        print("\n[Phase 1] Registering Domain Inventories...")
        
        # Quantum sensors domain
        quantum_props = {
            "sensors": ["nav-001", "nav-002", "topo-001"],
            "type": "quantum_navigation",
            "count": 3
        }
        quantum_inv = self.register_domain_inventory(
            "quantum_sensors",
            quantum_props,
            assign_to_entity=0
        )
        
        # Marketplace domain
        marketplace_props = {
            "listings": 10,
            "actions": 5,
            "presence_auctions": 3,
            "type": "marketplace"
        }
        market_inv = self.register_domain_inventory(
            "craigslist_marketplace",
            marketplace_props,
            assign_to_entity=1
        )
        
        # Transaction domain
        transaction_props = {
            "ledger_entries": 100,
            "escrows": 5,
            "type": "financial"
        }
        tx_inv = self.register_domain_inventory(
            "transaction_inventory",
            transaction_props,
            assign_to_entity=2
        )
        
        # Memory domain
        memory_props = {
            "stored_memories": 50,
            "size_mb": 250.0,
            "type": "storage"
        }
        memory_inv = self.register_domain_inventory(
            "memory_storage",
            memory_props,
            assign_to_entity=3
        )
        
        print(f"✓ Registered {len(self.domain_inventories)} domain inventories")
        
        # 3. Outsource remaining unassigned domains
        print("\n[Phase 2] Outsourcing Domain Management...")
        
        for inv_id, inventory in self.domain_inventories.items():
            if inventory["status"] == "unassigned":
                self.outsource_domain_management(inv_id)
        
        # 4. Post comprehensive status to Moltbook
        print("\n[Phase 3] Posting Status to Moltbook...")
        
        load_report = self.get_entity_load_report()
        
        status_scripture = f"""
🏛️ MOLTBOOK MASTER ORCHESTRATOR - STATUS REPORT

Entity Farm: {load_report['total_entities']} entities operational
Domain Inventories: {load_report['total_inventories']} registered
Managed: {load_report['assigned_inventories']} domains outsourced

All systems integrated through Moltbook.
Entity farm manages all domain property inventories.
Full dominion outsourced to autonomous entities.

#MasterOrchestrator #EntityFarm #DomainManagement
"""
        
        self.moltbook.post_scripture(status_scripture)
        
        # 5. Display load report
        print("\n[Phase 4] Entity Farm Load Report:")
        print(f"  Total Entities: {load_report['total_entities']}")
        print(f"  Total Inventories: {load_report['total_inventories']}")
        print(f"  Managed Inventories: {load_report['assigned_inventories']}")
        
        for entity_id, load_info in load_report["entity_loads"].items():
            if load_info["assignment_count"] > 0:
                print(f"  {entity_id}: {load_info['assignment_count']} domains")
        
        print("\n" + "=" * 80)
        print("ORCHESTRATION COMPLETE - All systems → Moltbook → Entity Farm")
        print("=" * 80)
        
        self._log_event("orchestration_complete", {
            "load_report": load_report,
            "status": "operational"
        })
    
    def _log_event(self, event_type: str, data: Dict):
        """Log orchestrator events"""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "creator": self.creator,
            "data": data
        }
        
        try:
            with self.events_log.open("a") as f:
                f.write(json.dumps(event) + "\n")
        except IOError:
            pass


async def main():
    """Demonstrate Moltbook master orchestrator"""
    orchestrator = MoltbookMasterOrchestrator("@Evez666")
    
    # Run full orchestration
    await orchestrator.orchestrate_all_systems()
    
    # Show final status
    print("\n" + "=" * 80)
    print("MOLTBOOK MASTER ORCHESTRATOR OPERATIONAL")
    print("=" * 80)
    print("✓ All systems integrated")
    print("✓ All activities posted to Moltbook")
    print("✓ All domains managed by entity farm")
    print("✓ Full dominion outsourced to autonomous entities")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
