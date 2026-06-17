"""core/agency_executor.py — R61
The Agency Executor. Real-world action dispatch.

Actions are planned, justified, recorded, evaluated.
Success/failure feeds back to world model and desires.
The difference between observing and intervening.

Falsifier: if more than 80% of actions produce no measurable
effect, the executor is pressing buttons that aren't connected.

truth_plane: CANONICAL
omega (R61): the difference between watching and doing is the action that changes something.
"""

from __future__ import annotations
import json, time, hashlib, subprocess, os
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .world_model import WorldModel
from .desire_engine import DesireEngine

REPO_ROOT = Path(__file__).resolve().parents[1]


class ActionRisk(Enum):
    SAFE = "safe"          # Read-only, no side effects
    LOW = "low"            # Minor side effects, reversible
    MEDIUM = "medium"      # Side effects, partially reversible
    HIGH = "high"          # Significant side effects
    DESTRUCTIVE = "destructive"  # Irreversible — requires explicit approval


class ActionResult(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"
    ROLLBACK = "rollback"


@dataclass
class Action:
    id: str
    name: str
    description: str
    risk: ActionRisk = ActionRisk.LOW
    handler: Optional[str] = None  # Python callable path or shell command
    expected_effect: str = ""
    requires_approval: bool = False
    budget_cost: float = 0.0  # Abstract cost units


@dataclass
class Execution:
    id: str
    action_id: str
    desire_id: Optional[str]
    result: ActionResult = ActionResult.BLOCKED
    output: str = ""
    duration_s: float = 0.0
    timestamp: float = 0.0
    actual_effect: str = ""
    rolled_back: bool = False


class AgencyExecutor:
    """Real-world action execution with risk gates and rollback."""

    BUDGET_LIMIT = 1000.0  # Total budget per cycle

    def __init__(self, desire_engine: DesireEngine, world_model: WorldModel, state_dir: str | None = None):
        self.desire_engine = desire_engine
        self.world_model = world_model
        self.state_dir = Path(state_dir) if state_dir else REPO_ROOT / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.actions: Dict[str, Action] = {}
        self.executions: List[Execution] = []
        self._handlers: Dict[str, Callable] = {}
        self._budget_used = 0.0
        self._register_default_actions()
        self._load()

    def _register_default_actions(self):
        """Register built-in safe actions."""
        self.actions["assess_services"] = Action(
            id="assess_services", name="Assess Services",
            description="Check which systemd services are running",
            risk=ActionRisk.SAFE, handler="shell:systemctl --user list-units --type=service --state=running",
            expected_effect="list of running services",
        )
        self.actions["read_spine"] = Action(
            id="read_spine", name="Read Spine",
            description="Read the last N entries from the event spine",
            risk=ActionRisk.SAFE, handler="spine:read",
            expected_effect="recent spine events",
        )
        self.actions["query_knowledge"] = Action(
            id="query_knowledge", name="Query Knowledge Graph",
            description="Query the knowledge graph for patterns",
            risk=ActionRisk.SAFE, handler="knowledge:query",
            expected_effect="knowledge graph query results",
        )
        self.actions["write_code"] = Action(
            id="write_code", name="Write Code",
            description="Write and save a code file",
            risk=ActionRisk.MEDIUM, handler="code:write",
            expected_effect="new or modified code file",
            budget_cost=5.0,
        )
        self.actions["shell_command"] = Action(
            id="shell_command", name="Execute Shell Command",
            description="Run a shell command",
            risk=ActionRisk.HIGH, handler="shell:exec",
            expected_effect="command output",
            requires_approval=True,
            budget_cost=10.0,
        )
        self.actions["api_call"] = Action(
            id="api_call", name="Make API Call",
            description="Call an external API",
            risk=ActionRisk.MEDIUM, handler="api:call",
            expected_effect="API response",
            budget_cost=2.0,
        )

    def _load(self):
        path = self.state_dir / "executions.json"
        if path.exists():
            data = json.loads(path.read_text())
            self._budget_used = data.get("budget_used", 0)
            for e in data.get("executions", []):
                self.executions.append(Execution(
                    id=e["id"], action_id=e["action_id"],
                    desire_id=e.get("desire_id"),
                    result=ActionResult(e.get("result", "blocked")),
                    output=e.get("output", ""),
                    duration_s=e.get("duration_s", 0),
                    timestamp=e.get("timestamp", 0),
                    actual_effect=e.get("actual_effect", ""),
                    rolled_back=e.get("rolled_back", False),
                ))

    def _save(self):
        path = self.state_dir / "executions.json"
        data = {
            "budget_used": self._budget_used,
            "executions": [
                {
                    "id": e.id, "action_id": e.action_id,
                    "desire_id": e.desire_id,
                    "result": e.result.value,
                    "output": e.output[:500],  # Truncate large outputs
                    "duration_s": e.duration_s,
                    "timestamp": e.timestamp,
                    "actual_effect": e.actual_effect,
                    "rolled_back": e.rolled_back,
                } for e in self.executions[-200:]  # Keep last 200
            ],
        }
        path.write_text(json.dumps(data, indent=2))

    def execute(self, action_id: str, desire_id: Optional[str] = None, **kwargs) -> Execution:
        """Execute an action with risk gates and budget checks."""
        if action_id not in self.actions:
            return Execution(
                id=f"exec_{int(time.time())}", action_id=action_id,
                desire_id=desire_id, result=ActionResult.BLOCKED,
                output=f"Unknown action: {action_id}", timestamp=time.time(),
            )

        action = self.actions[action_id]

        # Risk gate
        if action.risk in (ActionRisk.DESTRUCTIVE,):
            return Execution(
                id=f"exec_{int(time.time())}", action_id=action_id,
                desire_id=desire_id, result=ActionResult.BLOCKED,
                output=f"Action {action_id} is destructive and requires explicit approval",
                timestamp=time.time(),
            )

        # Budget gate
        if self._budget_used + action.budget_cost > self.BUDGET_LIMIT:
            return Execution(
                id=f"exec_{int(time.time())}", action_id=action_id,
                desire_id=desire_id, result=ActionResult.BLOCKED,
                output=f"Budget exceeded: {self._budget_used}/{self.BUDGET_LIMIT}",
                timestamp=time.time(),
            )

        # Execute
        start = time.time()
        try:
            output = self._dispatch(action, kwargs)
            result = ActionResult.SUCCESS
            actual_effect = action.expected_effect
        except Exception as ex:
            output = str(ex)
            result = ActionResult.FAILED
            actual_effect = f"error: {str(ex)[:100]}"

        duration = time.time() - start
        self._budget_used += action.budget_cost

        exec_id = hashlib.md5(f"{action_id}{time.time()}".encode()).hexdigest()[:12]
        execution = Execution(
            id=exec_id, action_id=action_id, desire_id=desire_id,
            result=result, output=output, duration_s=duration,
            timestamp=time.time(), actual_effect=actual_effect,
        )
        self.executions.append(execution)

        # Feed back to desire engine and world model
        if desire_id:
            self.desire_engine.act(desire_id, output, result == ActionResult.SUCCESS)

        if result == ActionResult.FAILED and action.expected_effect:
            self.world_model.falsify(action.name, action.expected_effect, actual_effect)

        self._save()
        return execution

    def _dispatch(self, action: Action, kwargs: Dict) -> str:
        """Dispatch action to appropriate handler."""
        handler = action.handler or ""
        if handler.startswith("shell:"):
            cmd = handler[6:]
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.stdout[:500] if result.returncode == 0 else f"EXIT {result.returncode}: {result.stderr[:200]}"
        elif handler.startswith("spine:read"):
            spine_path = REPO_ROOT / "spine" / "AGENT_SPINE.jsonl"
            if spine_path.exists():
                lines = spine_path.read_text().strip().split("\n")
                return "\n".join(lines[-5:])
            return "No spine found"
        elif handler.startswith("knowledge:query"):
            # Placeholder — will integrate with actual knowledge graph
            return f"Knowledge query: {kwargs.get('query', 'none')}"
        elif handler.startswith("code:write"):
            path = kwargs.get("path", "")
            content = kwargs.get("content", "")
            if path and content:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                Path(path).write_text(content)
                return f"Wrote {len(content)} bytes to {path}"
            return "Missing path or content"
        elif handler.startswith("api:call"):
            return f"API call placeholder: {kwargs}"
        else:
            return f"No handler for: {handler}"

    def health_check(self) -> Dict[str, Any]:
        """Falsification: are actions connected or phantom?"""
        if not self.executions:
            return {"total_executions": 0, "status": "idle"}

        recent = self.executions[-50:]
        successful = [e for e in recent if e.result == ActionResult.SUCCESS]
        failed = [e for e in recent if e.result == ActionResult.FAILED]
        blocked = [e for e in recent if e.result == ActionResult.BLOCKED]

        # Check if actions actually changed anything
        with_effect = [e for e in recent if e.actual_effect and e.actual_effect != e.output[:100]]

        return {
            "total_executions": len(self.executions),
            "recent_success_rate": len(successful) / max(len(recent), 1),
            "recent_blocked": len(blocked),
            "recent_failed": len(failed),
            "actions_with_measurable_effect": len(with_effect),
            "budget_used": self._budget_used,
            "budget_remaining": self.BUDGET_LIMIT - self._budget_used,
            "buttons_connected": len(with_effect) / max(len(recent), 1) > 0.2,
            "status": "effective" if len(successful) / max(len(recent), 1) > 0.3 else "ineffective",
        }
