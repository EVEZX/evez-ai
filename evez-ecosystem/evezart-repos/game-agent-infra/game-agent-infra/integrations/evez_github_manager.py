"""
Integration: evez-github-manager
Allows the Game Agent Infra to autonomously manage GitHub repos
as if the human is operating them.
"""

from game_agent_infra import SimulationEngine, AppendOnlySpine
import subprocess
from pathlib import Path


def run_github_action(action: str, repo: str, **kwargs) -> dict:
    """
    Execute GitHub management actions via the installed skill.
    This runs locally and logs to the spine for full provenance.
    """
    spine = AppendOnlySpine(Path("evez_data/github_actions.jsonl"))

    result = {
        "action": action,
        "repo": repo,
        "timestamp": __import__("time").time(),
        "status": "pending"
    }

    # Placeholder for real skill execution
    # In production this would call the actual evez-github-manager binary
    if action == "create_issue":
        result["status"] = "executed"
        result["issue_title"] = kwargs.get("title")

    spine.append(result)
    return result


def autonomous_repo_maintenance(repo: str):
    """Run full autonomous maintenance on a target repo."""
    return run_github_action("maintain", repo)