import sys, os
"""ClawBreak Station API — transfer & multi-agent housing endpoints.

Adds to the main ClawBreak server:
- /station/agents — list/register agents
- /station/tasks — create/list/assign tasks
- /station/transfer — snapshot and transfer agents
- /station/messages — inter-agent communication
- /station/dashboard — full station overview
- /station/snapshots — list available snapshots
"""
import json
import time
import uuid
from pathlib import Path
from fastapi import Request
from station.registry import AgentRegistry
from station.transfer import TransferStation
from station.housing import AgentHousing

# Init
registry = AgentRegistry()
transfer = TransferStation(registry)
housing = AgentHousing(registry)

# Register default team
housing.setup_default_agents()

def register_station_routes(app):
    """Register all station routes on the FastAPI app."""

    @app.get("/station/dashboard")
    async def station_dashboard():
        """Full station overview."""
        return housing.get_dashboard()

    # --- Agents ---

    @app.get("/station/agents")
    async def list_agents(status: str = None):
        """List all registered agents."""
        return {"agents": registry.list_agents(status)}

    @app.post("/station/agents")
    async def register_agent(request: Request):
        """Register a new agent."""
        body = await request.json()
        registry.register_agent(
            id=body.get("id", str(uuid.uuid4())[:8]),
            name=body.get("name", "Unnamed Agent"),
            host=body.get("host", "127.0.0.1"),
            port=body.get("port", 8080),
            capabilities=body.get("capabilities", []),
            model=body.get("model", ""),
            metadata=body.get("metadata", {}),
        )
        return {"status": "registered"}

    @app.get("/station/agents/{agent_id}")
    async def get_agent(agent_id: str):
        """Get agent details."""
        agent = registry.get_agent(agent_id)
        if not agent:
            return {"error": f"Agent {agent_id} not found"}
        return agent

    @app.delete("/station/agents/{agent_id}")
    async def deregister_agent(agent_id: str):
        """Remove an agent."""
        registry.deregister_agent(agent_id)
        return {"status": "deregistered"}

    @app.post("/station/agents/{agent_id}/heartbeat")
    async def agent_heartbeat(agent_id: str):
        """Agent heartbeat."""
        registry.heartbeat(agent_id)
        return {"status": "ok", "timestamp": time.time()}

    @app.get("/station/agents/capable/{capability}")
    async def find_capable(capability: str):
        """Find agents with a specific capability."""
        return {"agents": registry.find_capable(capability)}

    # --- Tasks ---

    @app.get("/station/tasks")
    async def list_tasks(status: str = None):
        """List tasks."""
        return {"tasks": registry.get_tasks(status)}

    @app.post("/station/tasks")
    async def create_task(request: Request):
        """Create and auto-delegate a task."""
        body = await request.json()
        description = body.get("description", "")
        capability = body.get("capability")
        priority = body.get("priority", 5)

        result = housing.delegate_task(description, capability, priority)
        return result

    @app.post("/station/tasks/{task_id}/execute")
    async def execute_task(task_id: str):
        """Execute a delegated task on the assigned agent."""
        result = await housing.execute_delegated_task(task_id)
        return result

    # --- Transfer ---

    @app.get("/station/transfers")
    async def list_transfers():
        """List all transfers."""
        return {"transfers": registry.get_transfers()}

    @app.post("/station/transfer/snapshot/{agent_id}")
    async def snapshot_agent(agent_id: str):
        """Create a snapshot of an agent for transfer."""
        result = transfer.snapshot_agent(agent_id)
        return result

    @app.get("/station/snapshots")
    async def list_snapshots():
        """List available snapshots."""
        return {"snapshots": transfer.list_snapshots()}

    @app.post("/station/transfer/{agent_id}")
    async def transfer_agent(agent_id: str, request: Request):
        """Transfer an agent to a remote host."""
        body = await request.json()
        target_host = body.get("target_host")
        ssh_key = body.get("ssh_key")
        target_user = body.get("target_user", "root")

        if not target_host:
            return {"error": "target_host is required"}

        result = await transfer.transfer_to_host(agent_id, target_host, ssh_key, target_user)
        return result

    # --- Messages ---

    @app.get("/station/messages/{agent_id}")
    async def get_messages(agent_id: str, unread_only: bool = False):
        """Get messages for an agent."""
        return {"messages": registry.get_messages(agent_id, unread_only)}

    @app.post("/station/messages")
    async def send_message(request: Request):
        """Send a message between agents."""
        body = await request.json()
        registry.send_message(
            body.get("from", "system"),
            body.get("to"),
            body.get("content", ""),
        )
        return {"status": "sent"}

    @app.post("/station/broadcast")
    async def broadcast(request: Request):
        """Broadcast a message to all agents."""
        body = await request.json()
        result = housing.broadcast(body.get("from", "system"), body.get("content", ""))
        return result

    # --- Health ---

    @app.post("/station/health-check")
    async def health_check_all():
        """Check health of all agents."""
        return {"results": housing.health_check_all()}
