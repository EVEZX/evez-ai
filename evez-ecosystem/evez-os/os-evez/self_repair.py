#!/usr/bin/env python3
"""
EVEZ-OS Self-Repair Daemon — monitors repos for CI failures
and auto-generates fixes or detailed issues.

Capabilities:
    - Scans GitHub repos for failing Actions/CI
    - Classifies error patterns (missing deps, import errors, config issues)
    - For known patterns: generates fix PRs
    - For unknown errors: creates detailed diagnostic issues
    - Monitors Vercel deployments and flags failures
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_bus import AgentBus, get_bus
from memory import MemorySystem


# ── Known fix patterns ───────────────────────────────────────────────

KNOWN_PATTERNS = [
    {
        "name": "missing_dependency",
        "pattern": r"ModuleNotFoundError: No module named '(\w+)'",
        "fix_type": "add_dependency",
        "description": "Missing Python dependency",
    },
    {
        "name": "import_error",
        "pattern": r"ImportError: cannot import name '(\w+)' from '([\w.]+)'",
        "fix_type": "fix_import",
        "description": "Broken import statement",
    },
    {
        "name": "missing_file",
        "pattern": r"FileNotFoundError: \[Errno 2\] No such file or directory: '([^']+)'",
        "fix_type": "create_file",
        "description": "Missing file referenced in code",
    },
    {
        "name": "syntax_error",
        "pattern": r"SyntaxError: (.+)",
        "fix_type": "fix_syntax",
        "description": "Python syntax error",
    },
    {
        "name": "vercel_build_fail",
        "pattern": r"Error: Command .+ exited with (\d+)",
        "fix_type": "fix_build_config",
        "description": "Vercel build command failure",
    },
    {
        "name": "missing_env_var",
        "pattern": r"KeyError: '([A-Z_]+)'",
        "fix_type": "add_env_fallback",
        "description": "Missing environment variable",
    },
    {
        "name": "vercel_config_missing",
        "pattern": r"(?:vercel\.json|now\.json).*not found",
        "fix_type": "create_vercel_config",
        "description": "Missing Vercel configuration",
    },
    {
        "name": "type_error",
        "pattern": r"TypeError: (.+)",
        "fix_type": "fix_type_error",
        "description": "Python type error",
    },
]


class ErrorClassification:
    """Result of classifying a CI error."""

    def __init__(
        self,
        pattern_name: str,
        fix_type: str,
        description: str,
        match_groups: Tuple[str, ...],
        raw_error: str,
    ):
        self.pattern_name = pattern_name
        self.fix_type = fix_type
        self.description = description
        self.match_groups = match_groups
        self.raw_error = raw_error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern_name,
            "fix_type": self.fix_type,
            "description": self.description,
            "match_groups": list(self.match_groups),
            "raw_error": self.raw_error[:500],
        }


class SelfRepairDaemon:
    """
    Monitors GitHub repos for CI/CD failures and auto-generates fixes.
    Requires GITHUB_TOKEN env var for API access; degrades gracefully without it.
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
        self._gh_token = os.environ.get("GITHUB_TOKEN", "")
        self._has_gh = self._check_gh_cli()

    def _check_gh_cli(self) -> bool:
        """Check if gh CLI is available."""
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _run_gh(self, args: List[str], timeout: int = 30) -> Optional[str]:
        """Run a gh CLI command, return stdout or None on failure."""
        if not self._has_gh:
            return None
        try:
            result = subprocess.run(
                ["gh"] + args,
                capture_output=True, text=True, timeout=timeout,
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except (subprocess.TimeoutExpired, OSError):
            return None

    # ── Scanning ─────────────────────────────────────────────────────

    def scan_repo(self, repo: str) -> Dict[str, Any]:
        """Scan a single repo for failing CI runs."""
        report = {
            "repo": repo,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "failing_runs": [],
            "classifications": [],
            "actions_taken": [],
        }

        # Get recent failing workflow runs
        output = self._run_gh([
            "run", "list",
            "--repo", f"{self.github_org}/{repo}",
            "--status", "failure",
            "--limit", "5",
            "--json", "databaseId,name,conclusion,headBranch,createdAt",
        ])

        if not output:
            report["error"] = "Could not fetch workflow runs (no gh CLI or no token)"
            return report

        try:
            runs = json.loads(output)
        except json.JSONDecodeError:
            report["error"] = "Invalid JSON from gh CLI"
            return report

        for run in runs:
            run_id = run.get("databaseId")
            if not run_id:
                continue

            report["failing_runs"].append(run)

            # Get logs for this run
            log_output = self._run_gh([
                "run", "view", str(run_id),
                "--repo", f"{self.github_org}/{repo}",
                "--log-failed",
            ], timeout=15)

            if log_output:
                classifications = self.classify_errors(log_output)
                for c in classifications:
                    report["classifications"].append(c.to_dict())

        return report

    def scan_all_repos(self, repos: Optional[List[str]] = None) -> List[Dict]:
        """Scan multiple repos. Falls back to listing org repos."""
        if repos is None:
            repos = self._list_org_repos()
        results = []
        for repo in repos:
            try:
                result = self.scan_repo(repo)
                results.append(result)
                # Emit bus event for each failing repo
                if result.get("failing_runs"):
                    self.bus.emit("ERROR", "self_repair", {
                        "repo": repo,
                        "failing_runs": len(result["failing_runs"]),
                        "classifications": len(result["classifications"]),
                    })
            except Exception as e:
                results.append({"repo": repo, "error": str(e)})
        return results

    def _list_org_repos(self) -> List[str]:
        """List repos in the org."""
        output = self._run_gh([
            "repo", "list", self.github_org,
            "--limit", "50",
            "--json", "name",
        ])
        if not output:
            return []
        try:
            repos = json.loads(output)
            return [r["name"] for r in repos]
        except (json.JSONDecodeError, KeyError):
            return []

    # ── Classification ───────────────────────────────────────────────

    def classify_errors(self, log_text: str) -> List[ErrorClassification]:
        """Classify errors in CI log output against known patterns."""
        classifications = []
        for pattern in KNOWN_PATTERNS:
            matches = re.finditer(pattern["pattern"], log_text)
            for match in matches:
                classifications.append(ErrorClassification(
                    pattern_name=pattern["name"],
                    fix_type=pattern["fix_type"],
                    description=pattern["description"],
                    match_groups=match.groups(),
                    raw_error=log_text[max(0, match.start() - 100):match.end() + 100],
                ))
        return classifications

    # ── Fix generation ───────────────────────────────────────────────

    def generate_fix(
        self, repo: str, classification: ErrorClassification,
    ) -> Dict[str, Any]:
        """Generate a fix based on the error classification."""
        fix_type = classification.fix_type

        if fix_type == "add_dependency":
            module = classification.match_groups[0] if classification.match_groups else "unknown"
            return {
                "type": "pr",
                "title": f"fix: add missing dependency `{module}`",
                "body": (
                    f"## Summary\n"
                    f"CI is failing due to missing module `{module}`.\n\n"
                    f"## Error\n```\n{classification.raw_error[:300]}\n```\n\n"
                    f"Auto-generated by EVEZ-OS Self-Repair Daemon."
                ),
                "changes": [
                    {"file": "requirements.txt", "action": "append", "content": f"{module}\n"},
                ],
            }

        elif fix_type == "add_env_fallback":
            var = classification.match_groups[0] if classification.match_groups else "UNKNOWN"
            return {
                "type": "issue",
                "title": f"fix: missing env var `{var}` causing CI failure",
                "body": (
                    f"## Summary\n"
                    f"CI is failing because `{var}` is not set.\n\n"
                    f"## Error\n```\n{classification.raw_error[:300]}\n```\n\n"
                    f"## Suggested fix\n"
                    f"Use `os.environ.get('{var}', '')` instead of `os.environ['{var}']`.\n\n"
                    f"Auto-generated by EVEZ-OS Self-Repair Daemon."
                ),
            }

        elif fix_type == "create_vercel_config":
            return {
                "type": "pr",
                "title": "fix: add vercel.json configuration",
                "body": (
                    "## Summary\n"
                    "Deployment failing due to missing vercel.json.\n\n"
                    "Auto-generated by EVEZ-OS Self-Repair Daemon."
                ),
                "changes": [
                    {
                        "file": "vercel.json",
                        "action": "create",
                        "content": json.dumps({
                            "version": 2,
                            "builds": [{"src": "*.py", "use": "@vercel/python"}],
                            "routes": [{"src": "/(.*)", "dest": "/api/$1"}],
                        }, indent=2),
                    },
                ],
            }

        # Default: create an issue with diagnosis
        return {
            "type": "issue",
            "title": f"CI failure: {classification.description}",
            "body": (
                f"## Error Classification\n"
                f"- **Pattern**: {classification.pattern_name}\n"
                f"- **Type**: {classification.fix_type}\n\n"
                f"## Error\n```\n{classification.raw_error[:500]}\n```\n\n"
                f"Auto-generated by EVEZ-OS Self-Repair Daemon."
            ),
        }

    def apply_fix(self, repo: str, fix: Dict) -> Dict[str, Any]:
        """Apply a fix by creating a PR or issue via gh CLI."""
        fix_type = fix.get("type", "issue")
        result = {"repo": repo, "fix_type": fix_type, "success": False}

        if fix_type == "issue":
            output = self._run_gh([
                "issue", "create",
                "--repo", f"{self.github_org}/{repo}",
                "--title", fix["title"],
                "--body", fix["body"],
            ])
            result["success"] = output is not None
            result["output"] = (output or "").strip()

        elif fix_type == "pr":
            # For PRs we'd need to clone, branch, commit, push, and create PR.
            # Log the intent instead of executing (safer for autonomous operation).
            result["intent"] = fix
            result["note"] = "PR creation requires clone+branch+commit flow"

            # Emit to bus so the orchestrator can route to a code agent
            self.bus.emit("REPAIR", "self_repair", {
                "repo": repo,
                "fix": fix,
                "action": "create_pr",
            })
            result["success"] = True

        return result

    # ── Vercel monitoring ────────────────────────────────────────────

    def check_vercel_deployments(self, repos: Optional[List[str]] = None) -> List[Dict]:
        """Check Vercel deployment status for repos. Requires VERCEL_TOKEN."""
        vercel_token = os.environ.get("VERCEL_TOKEN", "")
        if not vercel_token:
            return [{"error": "VERCEL_TOKEN not set — skipping deployment check"}]

        # Without the vercel CLI or API client, we can check via gh
        results = []
        for repo in (repos or []):
            # Check for deployment status checks on recent commits
            output = self._run_gh([
                "api", f"repos/{self.github_org}/{repo}/deployments",
                "--jq", ".[0:3] | .[] | {environment, state, created_at}",
            ])
            if output:
                results.append({"repo": repo, "deployments": output.strip()})
            else:
                results.append({"repo": repo, "status": "no deployment data"})
        return results

    # ── Full repair cycle ────────────────────────────────────────────

    def run_repair_cycle(self, repos: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run a full repair cycle: scan, classify, fix."""
        cycle = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repos_scanned": 0,
            "failures_found": 0,
            "fixes_generated": 0,
            "fixes_applied": 0,
        }

        scan_results = self.scan_all_repos(repos)
        cycle["repos_scanned"] = len(scan_results)

        for result in scan_results:
            classifications = result.get("classifications", [])
            cycle["failures_found"] += len(classifications)

            for cls_dict in classifications:
                cls = ErrorClassification(
                    pattern_name=cls_dict["pattern"],
                    fix_type=cls_dict["fix_type"],
                    description=cls_dict["description"],
                    match_groups=tuple(cls_dict.get("match_groups", [])),
                    raw_error=cls_dict.get("raw_error", ""),
                )
                fix = self.generate_fix(result["repo"], cls)
                cycle["fixes_generated"] += 1

                apply_result = self.apply_fix(result["repo"], fix)
                if apply_result.get("success"):
                    cycle["fixes_applied"] += 1

        # Write to memory
        self.memory.append_to_spine({
            "kind": "repair.cycle",
            **cycle,
        })

        self.bus.emit("REPAIR", "self_repair", cycle)
        return cycle


# ── Entry point ──────────────────────────────────────────────────────

def run_repair(repos: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run a repair cycle. Callable from CLI or GitHub Action."""
    daemon = SelfRepairDaemon()
    return daemon.run_repair_cycle(repos)


if __name__ == "__main__":
    import sys as _sys
    repos = _sys.argv[1:] if len(_sys.argv) > 1 else None
    result = run_repair(repos)
    print(json.dumps(result, indent=2, default=str))
