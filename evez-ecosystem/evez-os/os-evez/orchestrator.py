#!/usr/bin/env python3
"""
EVEZ-OS Agent Orchestrator — central brain coordinating all agents.

Implements the OODA loop:
    Observe  — scan ecosystem state (agents, buses, repos, memory)
    Orient   — prioritize based on health, urgency, opportunity
    Decide   — select actions and assign to agents
    Act      — dispatch tasks via the agent bus

All decisions are written to spine/EVENT_SPINE.jsonl for auditability.
"""
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Sibling imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_bus import AgentBus, Event, get_bus
from memory import MemorySystem


# ── Agent Registry ───────────────────────────────────────────────────

class AgentRecord:
    """Single agent registration."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        capabilities: List[str],
        status: str = "ACTIVE",
        metadata: Optional[Dict] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.status = status
        self.metadata = metadata or {}
        self.last_heartbeat = datetime.now(timezone.utc).isoformat()
        self.tasks_completed = 0
        self.tasks_failed = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "status": self.status,
            "metadata": self.metadata,
            "last_heartbeat": self.last_heartbeat,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
        }


class AgentRegistry:
    """Tracks which agents are alive, their capabilities, and health."""

    def __init__(self):
        self._agents: Dict[str, AgentRecord] = {}

    def register(self, agent: AgentRecord) -> None:
        self._agents[agent.agent_id] = agent

    def deregister(self, agent_id: str) -> Optional[AgentRecord]:
        return self._agents.pop(agent_id, None)

    def get(self, agent_id: str) -> Optional[AgentRecord]:
        return self._agents.get(agent_id)

    def heartbeat(self, agent_id: str) -> bool:
        agent = self._agents.get(agent_id)
        if agent:
            agent.last_heartbeat = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def find_by_capability(self, capability: str) -> List[AgentRecord]:
        """Find all active agents that have a given capability."""
        return [
            a for a in self._agents.values()
            if a.status == "ACTIVE" and capability in a.capabilities
        ]

    def active_agents(self) -> List[AgentRecord]:
        return [a for a in self._agents.values() if a.status == "ACTIVE"]

    def all_agents(self) -> List[AgentRecord]:
        return list(self._agents.values())

    def to_dict(self) -> Dict[str, Any]:
        return {aid: a.to_dict() for aid, a in self._agents.items()}


# ── Task ─────────────────────────────────────────────────────────────

class Task:
    """A unit of work to be dispatched to an agent."""

    def __init__(
        self,
        description: str,
        required_capability: str,
        priority: int = 5,
        data: Optional[Dict] = None,
        source: str = "orchestrator",
    ):
        self.task_id = uuid.uuid4().hex[:12]
        self.description = description
        self.required_capability = required_capability
        self.priority = priority  # 1 = highest, 10 = lowest
        self.data = data or {}
        self.source = source
        self.status = "pending"
        self.assigned_to: Optional[str] = None
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.completed_at: Optional[str] = None
        self.result: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "required_capability": self.required_capability,
            "priority": self.priority,
            "data": self.data,
            "source": self.source,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "result": self.result,
        }


# ── OODA Orchestrator ────────────────────────────────────────────────

class Orchestrator:
    """
    Central brain: runs the OODA loop, maintains registry, routes tasks.
    """

    def __init__(
        self,
        bus: Optional[AgentBus] = None,
        memory: Optional[MemorySystem] = None,
        spine_path: Optional[Path] = None,
    ):
        self.bus = bus or get_bus()
        self.memory = memory or MemorySystem()
        self.registry = AgentRegistry()
        self._spine_path = spine_path or Path("spine/EVENT_SPINE.jsonl")
        self._task_queue: List[Task] = []
        self._completed_tasks: List[Task] = []

        # Bootstrap: register known agents from agents/registry.py
        self._bootstrap_agents()

        # Subscribe to bus events
        self.bus.subscribe("TASK_COMPLETED", self._on_task_completed)
        self.bus.subscribe("AGENT_DIED", self._on_agent_died)
        self.bus.subscribe("HEARTBEAT", self._on_heartbeat)

    def _bootstrap_agents(self) -> None:
        """Load agents from the static registry."""
        try:
            registry_path = Path(__file__).resolve().parent.parent / "agents" / "registry.py"
            if not registry_path.exists():
                return
            # Parse the registry without exec for safety
            content = registry_path.read_text()
            # Extract AGENTS list using json-compatible parsing
            import ast
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "AGENTS":
                            agents_data = ast.literal_eval(node.value)
                            for agent_data in agents_data:
                                status = agent_data.get("status", "UNKNOWN")
                                is_active = "ACTIVE" in status
                                record = AgentRecord(
                                    agent_id=agent_data["id"],
                                    name=agent_data["name"],
                                    capabilities=[agent_data["name"].lower()],
                                    status="ACTIVE" if is_active else "BLOCKED",
                                    metadata={"original_status": status},
                                )
                                self.registry.register(record)
        except Exception:
            pass  # graceful degradation

    # ── OODA Loop ────────────────────────────────────────────────────

    def run_ooda_cycle(self) -> Dict[str, Any]:
        """Execute one full OODA cycle. Returns cycle report."""
        cycle_id = f"OODA-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        report = {
            "cycle_id": cycle_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phases": {},
        }

        # OBSERVE
        observations = self._observe()
        report["phases"]["observe"] = observations

        # ORIENT
        priorities = self._orient(observations)
        report["phases"]["orient"] = priorities

        # DECIDE
        decisions = self._decide(priorities)
        report["phases"]["decide"] = decisions

        # ACT
        actions = self._act(decisions)
        report["phases"]["act"] = actions

        # Write to spine
        spine_event = {
            "kind": "ooda.cycle",
            "cycle_id": cycle_id,
            "timestamp": report["timestamp"],
            "observations": len(observations.get("issues", [])),
            "priorities": len(priorities),
            "decisions": len(decisions),
            "actions_dispatched": len(actions),
            "summary": self._summarize_cycle(report),
        }
        self._write_to_spine(spine_event)

        # Emit bus event
        self.bus.emit("OODA_CYCLE", "orchestrator", spine_event)

        # Store in memory
        self.memory.working.set(f"last_ooda_{cycle_id}", report)

        return report

    def _observe(self) -> Dict[str, Any]:
        """Phase 1: Observe ecosystem state."""
        obs: Dict[str, Any] = {
            "agents": {},
            "bus_health": {},
            "issues": [],
            "opportunities": [],
        }

        # Agent health
        for agent in self.registry.all_agents():
            obs["agents"][agent.agent_id] = {
                "name": agent.name,
                "status": agent.status,
                "last_heartbeat": agent.last_heartbeat,
            }
            if agent.status == "BLOCKED":
                obs["issues"].append({
                    "type": "agent_blocked",
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "severity": "medium",
                })

        # Pending tasks
        pending = [t for t in self._task_queue if t.status == "pending"]
        if len(pending) > 10:
            obs["issues"].append({
                "type": "task_backlog",
                "count": len(pending),
                "severity": "high",
            })

        # Memory state
        try:
            mem_status = self.memory.status()
            obs["memory"] = mem_status
        except Exception:
            obs["memory"] = {"error": "unavailable"}

        # Recent bus events (check for errors)
        recent_errors = self.bus.read_log_by_type("ERROR", limit=10)
        if recent_errors:
            obs["issues"].append({
                "type": "recent_errors",
                "count": len(recent_errors),
                "severity": "high",
                "latest": recent_errors[-1].to_dict() if recent_errors else None,
            })

        return obs

    def _orient(self, observations: Dict) -> List[Dict[str, Any]]:
        """Phase 2: Prioritize based on observations."""
        priorities = []

        for issue in observations.get("issues", []):
            severity_score = {"critical": 1, "high": 2, "medium": 5, "low": 8}.get(
                issue.get("severity", "medium"), 5
            )
            priorities.append({
                "issue": issue,
                "priority": severity_score,
                "action_type": self._classify_action(issue),
            })

        # Sort by priority (lowest number = highest priority)
        priorities.sort(key=lambda p: p["priority"])
        return priorities

    def _classify_action(self, issue: Dict) -> str:
        """Classify what kind of action an issue needs."""
        issue_type = issue.get("type", "")
        if issue_type == "agent_blocked":
            return "unblock_agent"
        elif issue_type == "task_backlog":
            return "scale_processing"
        elif issue_type == "recent_errors":
            return "investigate_errors"
        elif issue_type == "ci_failure":
            return "trigger_repair"
        elif issue_type == "missing_coverage":
            return "trigger_expansion"
        return "investigate"

    def _decide(self, priorities: List[Dict]) -> List[Dict[str, Any]]:
        """Phase 3: Select actions for top priorities."""
        decisions = []
        for p in priorities[:5]:  # cap at 5 actions per cycle
            action_type = p["action_type"]
            if action_type == "trigger_repair":
                decisions.append({
                    "action": "self_repair",
                    "target": p["issue"],
                    "capability": "ci_repair",
                })
            elif action_type == "trigger_expansion":
                decisions.append({
                    "action": "expansion_scan",
                    "target": p["issue"],
                    "capability": "expansion",
                })
            elif action_type == "investigate_errors":
                decisions.append({
                    "action": "error_triage",
                    "target": p["issue"],
                    "capability": "ci_repair",
                })
            else:
                decisions.append({
                    "action": action_type,
                    "target": p["issue"],
                    "capability": "general",
                })
        return decisions

    def _act(self, decisions: List[Dict]) -> List[Dict[str, Any]]:
        """Phase 4: Dispatch tasks to agents."""
        dispatched = []
        for dec in decisions:
            cap = dec.get("capability", "general")
            agents = self.registry.find_by_capability(cap)
            if not agents:
                agents = self.registry.active_agents()

            task = Task(
                description=f"{dec['action']}: {json.dumps(dec.get('target', {}), default=str)[:200]}",
                required_capability=cap,
                priority=3,
                data=dec,
                source="orchestrator",
            )

            if agents:
                task.assigned_to = agents[0].agent_id
                task.status = "dispatched"

            self._task_queue.append(task)

            # Emit task event
            self.bus.emit(
                "TASK_CREATED",
                "orchestrator",
                task.to_dict(),
                correlation_id=task.task_id,
            )

            dispatched.append({
                "task_id": task.task_id,
                "action": dec["action"],
                "assigned_to": task.assigned_to,
            })

        return dispatched

    def _summarize_cycle(self, report: Dict) -> str:
        obs = report["phases"].get("observe", {})
        issues = len(obs.get("issues", []))
        decisions = len(report["phases"].get("decide", []))
        actions = len(report["phases"].get("act", []))
        agents = len(obs.get("agents", {}))
        return f"agents={agents} issues={issues} decisions={decisions} dispatched={actions}"

    # ── Bus event handlers ───────────────────────────────────────────

    def _on_task_completed(self, event: Event) -> None:
        task_id = event.data.get("task_id")
        if not task_id:
            return
        for task in self._task_queue:
            if task.task_id == task_id:
                task.status = "completed"
                task.completed_at = datetime.now(timezone.utc).isoformat()
                task.result = event.data.get("result")
                self._completed_tasks.append(task)
                if task.assigned_to:
                    agent = self.registry.get(task.assigned_to)
                    if agent:
                        agent.tasks_completed += 1
                break

    def _on_agent_died(self, event: Event) -> None:
        agent_id = event.data.get("agent_id")
        if agent_id:
            agent = self.registry.get(agent_id)
            if agent:
                agent.status = "DEAD"

    def _on_heartbeat(self, event: Event) -> None:
        agent_id = event.data.get("agent_id")
        if agent_id:
            self.registry.heartbeat(agent_id)

    # ── Task management ──────────────────────────────────────────────

    def submit_task(self, task: Task) -> Task:
        """Submit a task to the queue."""
        self._task_queue.append(task)
        self.bus.emit("TASK_CREATED", "orchestrator", task.to_dict())
        return task

    def route_task(self, task: Task) -> Optional[str]:
        """Route a task to the best agent based on capability."""
        agents = self.registry.find_by_capability(task.required_capability)
        if not agents:
            agents = self.registry.active_agents()
        if not agents:
            return None
        # Pick the agent with fewest in-flight tasks
        best = min(agents, key=lambda a: a.tasks_completed)
        task.assigned_to = best.agent_id
        task.status = "dispatched"
        return best.agent_id

    # ── Spine integration ────────────────────────────────────────────

    def _write_to_spine(self, event: Dict) -> None:
        """Append a decision event to the event spine."""
        try:
            with open(self._spine_path, "a") as f:
                f.write(json.dumps(event, separators=(",", ":")) + "\n")
        except OSError:
            pass

    # ── Status ───────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Full orchestrator status."""
        active = self.registry.active_agents()
        pending = [t for t in self._task_queue if t.status == "pending"]
        dispatched = [t for t in self._task_queue if t.status == "dispatched"]
        return {
            "agents_total": len(self.registry.all_agents()),
            "agents_active": len(active),
            "tasks_pending": len(pending),
            "tasks_dispatched": len(dispatched),
            "tasks_completed": len(self._completed_tasks),
            "registry": {a.agent_id: a.name for a in self.registry.all_agents()},
        }


# ── Entry point ──────────────────────────────────────────────────────

def run_cycle() -> Dict[str, Any]:
    """Run a single OODA cycle. Suitable for cron / GitHub Action."""
    orch = Orchestrator()
    return orch.run_ooda_cycle()


if __name__ == "__main__":
    report = run_cycle()
    print(json.dumps(report, indent=2, default=str))
