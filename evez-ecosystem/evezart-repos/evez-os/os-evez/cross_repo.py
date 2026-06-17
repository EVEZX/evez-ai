#!/usr/bin/env python3
"""
EVEZ-OS Cross-Repo Coordination — manages relationships between all repos.

Capabilities:
    - Maps dependency relationships between EvezArt repos
    - When one repo changes, identifies affected downstream repos
    - Propagates fixes and improvements across the ecosystem
    - Tracks repo health across the org
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_bus import AgentBus, get_bus
from memory import MemorySystem


# ── Known repo topology ──────────────────────────────────────────────
# Static map of known inter-repo dependencies.
# Format: repo -> list of repos it depends on.

REPO_DEPENDENCIES = {
    "evez-os": [],
    "evez-autonomous-ledger": ["evez-os"],
    "evez-api": ["evez-os"],
    "evez-dashboard": ["evez-api"],
    "evez-vision": ["evez-os"],
    "evez-worldsim": ["evez-os"],
    "evez-hyperloop": ["evez-os", "evez-autonomous-ledger"],
    "evez-signal-detector": ["evez-os", "evez-api"],
    "evez-game-server": ["evez-os"],
    "evez-x-semantic": ["evez-os", "evez-signal-detector"],
}


class RepoInfo:
    """Information about a single repository."""

    def __init__(
        self,
        name: str,
        depends_on: Optional[List[str]] = None,
        dependents: Optional[List[str]] = None,
    ):
        self.name = name
        self.depends_on = depends_on or []
        self.dependents = dependents or []
        self.last_checked: Optional[str] = None
        self.health: str = "unknown"
        self.default_branch: str = "main"
        self.open_prs: int = 0
        self.failing_ci: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "depends_on": self.depends_on,
            "dependents": self.dependents,
            "last_checked": self.last_checked,
            "health": self.health,
            "default_branch": self.default_branch,
            "open_prs": self.open_prs,
            "failing_ci": self.failing_ci,
        }


class CrossRepoCoordinator:
    """
    Manages relationships between all EvezArt repos.
    """

    def __init__(
        self,
        bus: Optional[AgentBus] = None,
        memory: Optional[MemorySystem] = None,
        github_org: str = "EvezArt",
    ):
        self.bus = bus or get_bus()
        self.memory = memory or MemorySystem()
        self.github_org = github_org
        self._has_gh = self._check_gh_cli()
        self._repos: Dict[str, RepoInfo] = {}
        self._build_topology()

    def _check_gh_cli(self) -> bool:
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _run_gh(self, args: List[str], timeout: int = 30) -> Optional[str]:
        if not self._has_gh:
            return None
        try:
            result = subprocess.run(
                ["gh"] + args,
                capture_output=True, text=True, timeout=timeout,
            )
            return result.stdout if result.returncode == 0 else None
        except (subprocess.TimeoutExpired, OSError):
            return None

    # ── Topology ─────────────────────────────────────────────────────

    def _build_topology(self) -> None:
        """Build the repo dependency graph from static config."""
        # Forward deps (what each repo depends on)
        for repo, deps in REPO_DEPENDENCIES.items():
            self._repos[repo] = RepoInfo(name=repo, depends_on=deps)

        # Reverse deps (what depends on each repo)
        for repo, info in self._repos.items():
            for dep in info.depends_on:
                if dep in self._repos:
                    self._repos[dep].dependents.append(repo)

    def get_dependents(self, repo: str) -> List[str]:
        """Get all repos that depend on the given repo (direct + transitive)."""
        visited: Set[str] = set()
        stack = [repo]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            info = self._repos.get(current)
            if info:
                for dep in info.dependents:
                    if dep not in visited:
                        stack.append(dep)
        visited.discard(repo)  # don't include self
        return sorted(visited)

    def get_dependencies(self, repo: str) -> List[str]:
        """Get all repos that the given repo depends on (direct + transitive)."""
        visited: Set[str] = set()
        stack = [repo]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            info = self._repos.get(current)
            if info:
                for dep in info.depends_on:
                    if dep not in visited:
                        stack.append(dep)
        visited.discard(repo)
        return sorted(visited)

    # ── Health scanning ──────────────────────────────────────────────

    def scan_repo_health(self, repo: str) -> Dict[str, Any]:
        """Check health of a single repo via GitHub API."""
        info = self._repos.get(repo, RepoInfo(name=repo))
        info.last_checked = datetime.now(timezone.utc).isoformat()

        # Check open PRs
        pr_output = self._run_gh([
            "pr", "list",
            "--repo", f"{self.github_org}/{repo}",
            "--state", "open",
            "--json", "number",
        ])
        if pr_output:
            try:
                prs = json.loads(pr_output)
                info.open_prs = len(prs)
            except json.JSONDecodeError:
                pass

        # Check latest CI status
        run_output = self._run_gh([
            "run", "list",
            "--repo", f"{self.github_org}/{repo}",
            "--limit", "1",
            "--json", "conclusion",
        ])
        if run_output:
            try:
                runs = json.loads(run_output)
                if runs and runs[0].get("conclusion") == "failure":
                    info.failing_ci = True
                    info.health = "failing"
                else:
                    info.failing_ci = False
                    info.health = "healthy"
            except json.JSONDecodeError:
                pass

        self._repos[repo] = info
        return info.to_dict()

    def scan_all_health(self) -> Dict[str, Any]:
        """Scan health of all known repos."""
        results = {}
        for repo in self._repos:
            try:
                results[repo] = self.scan_repo_health(repo)
            except Exception as e:
                results[repo] = {"name": repo, "error": str(e)}
        return results

    # ── Impact analysis ──────────────────────────────────────────────

    def analyze_change_impact(self, repo: str) -> Dict[str, Any]:
        """Analyze the impact of a change in the given repo."""
        dependents = self.get_dependents(repo)
        return {
            "repo": repo,
            "direct_dependents": self._repos.get(repo, RepoInfo(name=repo)).dependents,
            "all_affected": dependents,
            "impact_radius": len(dependents),
            "recommendation": self._impact_recommendation(repo, dependents),
        }

    def _impact_recommendation(self, repo: str, dependents: List[str]) -> str:
        if not dependents:
            return f"Changes to {repo} are isolated — no downstream impact."
        if len(dependents) > 5:
            return (
                f"HIGH IMPACT: {repo} has {len(dependents)} downstream dependents. "
                f"Test thoroughly and coordinate rollout."
            )
        return (
            f"Changes to {repo} affect {len(dependents)} repo(s): "
            f"{', '.join(dependents)}. Verify downstream compatibility."
        )

    # ── Cross-repo fix propagation ───────────────────────────────────

    def propagate_fix(self, source_repo: str, fix_description: str) -> Dict[str, Any]:
        """When a fix is applied to one repo, check if it should propagate."""
        affected = self.get_dependents(source_repo)
        propagation = {
            "source": source_repo,
            "fix": fix_description,
            "affected_repos": affected,
            "actions": [],
        }

        for dep_repo in affected:
            # Emit bus event for each affected repo
            self.bus.emit("CROSS_REPO", "cross_repo_coordinator", {
                "action": "check_compatibility",
                "source_repo": source_repo,
                "target_repo": dep_repo,
                "fix_description": fix_description,
            })
            propagation["actions"].append({
                "repo": dep_repo,
                "action": "compatibility_check_requested",
            })

        return propagation

    # ── Full coordination cycle ──────────────────────────────────────

    def run_coordination_cycle(self) -> Dict[str, Any]:
        """Run a full cross-repo coordination cycle."""
        cycle = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repos_total": len(self._repos),
            "topology": {},
            "health": {},
            "failing_repos": [],
        }

        # Build topology summary
        for repo, info in self._repos.items():
            cycle["topology"][repo] = {
                "depends_on": info.depends_on,
                "dependents": info.dependents,
            }

        # Scan health
        health = self.scan_all_health()
        cycle["health"] = health
        cycle["failing_repos"] = [
            r for r, h in health.items()
            if isinstance(h, dict) and h.get("failing_ci")
        ]

        # Emit summary
        self.bus.emit("CROSS_REPO", "cross_repo_coordinator", {
            "action": "coordination_cycle",
            "repos": cycle["repos_total"],
            "failing": len(cycle["failing_repos"]),
        })

        self.memory.append_to_spine({
            "kind": "cross_repo.cycle",
            "repos_total": cycle["repos_total"],
            "failing_count": len(cycle["failing_repos"]),
            "failing_repos": cycle["failing_repos"],
            "timestamp": cycle["timestamp"],
        })

        return cycle

    # ── Status ───────────────────────────────────────────────────────

    def repo_map(self) -> Dict[str, Any]:
        """Return the full repo dependency map."""
        return {
            repo: info.to_dict()
            for repo, info in self._repos.items()
        }


# ── Entry point ──────────────────────────────────────────────────────

def run_coordination() -> Dict[str, Any]:
    """Run a cross-repo coordination cycle."""
    coordinator = CrossRepoCoordinator()
    return coordinator.run_coordination_cycle()


if __name__ == "__main__":
    result = run_coordination()
    print(json.dumps(result, indent=2, default=str))
