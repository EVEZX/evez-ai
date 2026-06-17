import sys, os
"""Agent Housing — manages multiple AI agents living together, sharing work.

Agents can:
- Register themselves and declare capabilities
- Claim tasks from a shared queue
- Communicate with each other via messages
- Collaborate on complex tasks (divide and conquer)
- Specialize (research, coding, communication, monitoring)
"""
import json
import time
import asyncio
import httpx
from station.registry import AgentRegistry

class AgentHousing:
    """Manages a collective of AI agents working together."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.orchestrator_id = "orchestrator"

    def setup_default_agents(self):
        """Register the default agent team."""
        agents = [
            {
                "agent_id": "clawbreak-primary",
                "name": "ClawBreak Primary",
                "host": "127.0.0.1",
                "port": 8080,
                "capabilities": ["chat", "shell", "search", "memory", "email", "github", "weather", "file", "sysinfo", "image_gen"],
                "model": "zai-org/GLM-5.1-FP8",
                "metadata": {"role": "general", "primary": True}
            },
            {
                "agent_id": "openclaw-gateway",
                "name": "OpenClaw Gateway",
                "host": "127.0.0.1",
                "port": 18789,
                "capabilities": ["chat", "tools", "mcp", "subagents", "cron"],
                "model": "zai-org/GLM-5.1-FP8",
                "metadata": {"role": "backup", "fallback": True}
            },
            {
                "agent_id": "research-agent",
                "name": "Research Agent",
                "host": "127.0.0.1",
                "port": 8081,
                "capabilities": ["search", "memory", "file", "github"],
                "model": "nvidia/DeepSeek-V3.2-NVFP4",
                "metadata": {"role": "research", "specialized": True}
            },
            {
                "agent_id": "coding-agent",
                "name": "Coding Agent",
                "host": "127.0.0.1",
                "port": 8082,
                "capabilities": ["shell", "file", "memory", "github"],
                "model": "nvidia/DeepSeek-V3.2-NVFP4",
                "metadata": {"role": "coding", "specialized": True}
            },
            {
                "agent_id": "comm-agent",
                "name": "Communication Agent",
                "host": "127.0.0.1",
                "port": 8083,
                "capabilities": ["email", "search", "memory", "github"],
                "model": "MiniMaxAI/MiniMax-M2.5",
                "metadata": {"role": "communication", "specialized": True}
            },
        ]

        for a in agents:
            self.registry.register_agent(**a)

        return {"registered": len(agents), "agents": [a["agent_id"] for a in agents]}

    def health_check_all(self):
        """Check health of all registered agents."""
        agents = self.registry.list_agents(status="active")
        results = []
        for a in agents:
            try:
                resp = httpx.get(f"http://{a['host']}:{a['port']}/health", timeout=5)
                if resp.status_code == 200:
                    self.registry.heartbeat(a["agent_id"])
                    results.append({"agent_id": a["agent_id"], "status": "healthy", "details": resp.json()})
                else:
                    self.registry.mark_offline(a["agent_id"])
                    results.append({"agent_id": a["agent_id"], "status": "unhealthy", "code": resp.status_code})
            except:
                self.registry.mark_offline(a["agent_id"])
                results.append({"agent_id": a["agent_id"], "status": "offline"})
        return results

    def delegate_task(self, description, capability=None, priority=5):
        """Find the best agent for a task and assign it."""
        import uuid
        task_id = str(uuid.uuid4())[:8]

        # Create the task
        self.registry.create_task(task_id, description, priority)

        # Find capable agent
        if capability:
            agents = self.registry.find_capable(capability)
        else:
            agents = self.registry.list_agents(status="active")

        if not agents:
            return {"error": "No available agents", "task_id": task_id}

        # Pick the best agent (prefer specialized, then least busy)
        best = self._select_agent(agents, capability)
        if best:
            self.registry.assign_task(task_id, best["id"])
            return {"task_id": task_id, "assigned_to": best["id"], "agent_name": best["name"]}

        return {"task_id": task_id, "status": "unassigned"}

    def _select_agent(self, agents, capability):
        """Select the best agent for a task."""
        # Prefer specialized agents for the capability
        for a in agents:
            meta = json.loads(a.get("metadata", "{}"))
            if meta.get("specialized") and capability in json.loads(a.get("capabilities", "[]")):
                return a

        # Fall back to primary
        for a in agents:
            meta = json.loads(a.get("metadata", "{}"))
            if meta.get("primary"):
                return a

        # Any active agent
        return agents[0] if agents else None

    async def execute_delegated_task(self, task_id):
        """Execute a delegated task on the assigned agent."""
        tasks = self.registry.get_tasks()
        task = next((t for t in tasks if t["id"] == task_id), None)
        if not task:
            return {"error": f"Task {task_id} not found"}

        agent = self.registry.get_agent(task["assigned_to"])
        if not agent:
            return {"error": f"Agent {task['assigned_to']} not found"}

        self.registry.start_task(task_id)

        try:
            # Call the agent's chat endpoint
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"http://{agent['host']}:{agent['port']}/chat",
                    json={"message": task["description"], "session_id": f"task_{task_id}"}
                )
                result = resp.json()
                reply = result.get("reply", result.get("error", "No response"))
                self.registry.complete_task(task_id, {"reply": reply})
                return {"task_id": task_id, "status": "completed", "result": reply}
        except Exception as e:
            self.registry.fail_task(task_id, str(e))
            return {"task_id": task_id, "status": "failed", "error": str(e)}

    def broadcast(self, from_agent, message):
        """Broadcast a message to all active agents."""
        agents = self.registry.list_agents(status="active")
        for a in agents:
            if a["agent_id"] != from_agent:
                self.registry.send_message(from_agent, a["agent_id"], message)
        return {"broadcast_to": len(agents) - 1}

    def get_dashboard(self):
        """Get the full station dashboard."""
        return {
            "agents": self.registry.list_agents(),
            "tasks": self.registry.get_tasks(),
            "pending": self.registry.get_pending_tasks(),
            "transfers": self.registry.get_transfers(),
            "timestamp": time.time(),
        }
