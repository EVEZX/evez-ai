#!/usr/bin/env python3
"""
Agent Bootstrap System - Autonomize New Agents
Automatically configures new agents with autonomous authority,
domain delegation, and navigation capabilities.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class AgentBootstrap:
    """Bootstrap new agents with full autonomous capabilities."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.registry_file = self.data_dir / "agent_registry.jsonl"
        
        self.agents: Dict[str, Dict] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load existing agent registry."""
        if self.registry_file.exists():
            try:
                with self.registry_file.open("r") as f:
                    for line in f:
                        data = json.loads(line)
                        self.agents[data["agent_id"]] = data
            except Exception:
                pass
    
    def _save_agent(self, agent_data: Dict):
        """Save agent to registry."""
        with self.registry_file.open("a") as f:
            f.write(json.dumps(agent_data) + "\n")
    
    def _generate_agent_id(self, base_name: str) -> str:
        """Generate unique agent ID."""
        timestamp = str(time.time())
        hash_input = f"{base_name}-{timestamp}"
        short_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
        return f"{base_name}-{short_hash}"
    
    def bootstrap_agent(
        self,
        agent_name: str,
        role: str = "worker",
        domain: str = "general",
        autonomy_level: str = "full",
        capabilities: List[str] = None
    ) -> Dict[str, Any]:
        """
        Bootstrap a new autonomous agent.
        
        Args:
            agent_name: Base name for the agent
            role: Agent role (worker, orchestrator, etc.)
            domain: Primary domain
            autonomy_level: full, limited, or supervised
            capabilities: List of capability names
            
        Returns:
            Bootstrap configuration
        """
        agent_id = self._generate_agent_id(agent_name)
        
        agent_data = {
            "agent_id": agent_id,
            "name": agent_name,
            "role": role,
            "domain": domain,
            "autonomy_level": autonomy_level,
            "capabilities": capabilities or ["execute", "delegate", "navigate"],
            "bootstrap_time": time.time(),
            "status": "bootstrapped",
            "config": {
                "can_self_authorize": autonomy_level == "full",
                "can_delegate": "delegate" in (capabilities or ["execute"]),
                "can_navigate": "navigate" in (capabilities or ["execute"]),
                "requires_approval": autonomy_level != "full",
                "max_delegation_depth": 5 if autonomy_level == "full" else 1,
                "timeout_seconds": 300,
                "retry_attempts": 3
            }
        }
        
        self.agents[agent_id] = agent_data
        self._save_agent(agent_data)
        
        return agent_data
    
    def bootstrap_batch(
        self,
        count: int,
        base_name: str,
        domain: str = "general",
        capabilities: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Bootstrap multiple agents at once.
        
        Args:
            count: Number of agents
            base_name: Base name for agents
            domain: Primary domain
            capabilities: Capabilities for agents
            
        Returns:
            List of bootstrap configurations
        """
        agents = []
        
        for i in range(count):
            agent = self.bootstrap_agent(
                agent_name=f"{base_name}-{i:03d}",
                role="worker",
                domain=domain,
                autonomy_level="full",
                capabilities=capabilities
            )
            agents.append(agent)
        
        return agents
    
    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration."""
        return self.agents.get(agent_id)
    
    def get_agents_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Get all agents in a domain."""
        return [
            a for a in self.agents.values()
            if a.get("domain") == domain
        ]
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all registered agents."""
        return list(self.agents.values())
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        domains = {}
        roles = {}
        autonomy = {}
        
        for agent in self.agents.values():
            d = agent.get("domain", "unknown")
            r = agent.get("role", "unknown")
            a = agent.get("autonomy_level", "unknown")
            
            domains[d] = domains.get(d, 0) + 1
            roles[r] = roles.get(r, 0) + 1
            autonomy[a] = autonomy.get(a, 0) + 1
        
        return {
            "total_agents": len(self.agents),
            "by_domain": domains,
            "by_role": roles,
            "by_autonomy": autonomy
        }


def quick_bootstrap(agent_name: str, role: str = "worker") -> Dict[str, Any]:
    """Quick bootstrap single agent with defaults."""
    bootstrap = AgentBootstrap()
    return bootstrap.bootstrap_agent(
        agent_name=agent_name,
        role=role,
        autonomy_level="full"
    )


def batch_bootstrap(count: int, base_name: str = "agent") -> List[Dict[str, Any]]:
    """Bootstrap multiple agents."""
    bootstrap = AgentBootstrap()
    return bootstrap.bootstrap_batch(count, base_name)


if __name__ == "__main__":
    # Demo: Bootstrap new agents
    print("Agent Bootstrap Demo")
    print("=" * 50)
    
    bootstrap = AgentBootstrap()
    
    # Bootstrap single agents
    agent1 = bootstrap.bootstrap_agent(
        "orchestrator-001",
        role="orchestrator",
        domain="task_routing",
        autonomy_level="full",
        capabilities=["execute", "delegate", "navigate"]
    )
    print(f"\nBootstrapped: {agent1['agent_id']}")
    print(f"  Role: {agent1['role']}")
    print(f"  Domain: {agent1['domain']}")
    print(f"  Autonomy: {agent1['autonomy_level']}")
    print(f"  Config: {json.dumps(agent1['config'], indent=2)}")
    
    # Batch bootstrap
    workers = bootstrap.bootstrap_batch(
        count=3,
        base_name="worker",
        domain="task_execution",
        capabilities=["execute"]
    )
    print(f"\nBootstrapped {len(workers)} workers")
    
    # Stats
    stats = bootstrap.get_registry_stats()
    print(f"\nRegistry Stats: {json.dumps(stats, indent=2)}")