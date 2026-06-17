#!/usr/bin/env python3
"""
EVEZ Health Dashboard Generator — Monitor Module

Generates a comprehensive dashboard.json with ecosystem health metrics,
velocity stats, action summaries, and capability tracking.
"""

import os
import json
import datetime
import sys

INTEL_DIR = "intelligence"
DASHBOARD_FILE = f"{INTEL_DIR}/dashboard.json"
CAPABILITIES_FILE = f"{INTEL_DIR}/capabilities.json"
DECISIONS_FILE = f"{INTEL_DIR}/decisions.jsonl"
LEARNINGS_FILE = f"{INTEL_DIR}/learnings.jsonl"


def utcnow():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_jsonl(filepath):
    """Read all records from a JSONL file."""
    records = []
    if not os.path.exists(filepath):
        return records
    try:
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass
    return records


def _read_json(filepath, default=None):
    if default is None:
        default = {}
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath) as f:
            return json.load(f)
    except Exception:
        return default


def _get_cycle_number():
    """Derive cycle number from capabilities or learnings count."""
    caps = _read_json(CAPABILITIES_FILE)
    return caps.get("total_cycles", 0)


def generate_dashboard(state=None, analysis=None, results=None):
    """Generate the comprehensive dashboard.json.

    Can be called with live cycle data or standalone to rebuild from files.
    """
    print("  📊 MONITOR — generating dashboard")

    cycle_number = _get_cycle_number()
    decisions = _read_jsonl(DECISIONS_FILE)
    learnings = _read_jsonl(LEARNINGS_FILE)
    caps = _read_json(CAPABILITIES_FILE)

    # Ecosystem metrics (from live state or fallback)
    if state:
        repos = state.get("repos", [])
        total_repos = len(repos)
        active_24h = sum(1 for r in repos if r.get("commits_24h", 0) > 0)
        commits_24h = state.get("total_commits_24h", 0)
        open_prs = state.get("total_open_prs", 0)
        open_issues = state.get("total_open_issues", 0)
    else:
        # Read from state.json
        saved_state = _read_json(f"{INTEL_DIR}/state.json")
        total_repos = saved_state.get("total_repos", 0)
        active_24h = 0
        commits_24h = saved_state.get("total_commits_24h", 0)
        open_prs = saved_state.get("total_open_prs", 0)
        open_issues = saved_state.get("total_open_issues", 0)

    health_score = 100
    failing_workflows = 0
    passing_workflows = 0

    if analysis:
        health_score = analysis.get("health_score", 100)
        failing_workflows = len(analysis.get("failing_workflows", []))
        # Count passing: total runs minus failures
        total_runs = 0
        if state:
            for r in state.get("repos", []):
                total_runs += len(r.get("workflow_runs", []))
        passing_workflows = max(0, total_runs - failing_workflows)

    # Actions taken this cycle
    actions_taken = []
    if results:
        for r in results:
            actions_taken.append({
                "type": r["action"]["type"],
                "description": r["action"]["description"],
                "success": r["success"],
                "detail": r["detail"],
                "timestamp": r["timestamp"],
            })

    # Next priorities (from analysis)
    next_priorities = []
    if analysis:
        if analysis.get("failing_workflows"):
            next_priorities.append({
                "priority": 1,
                "description": f"Fix {len(analysis['failing_workflows'])} failing workflows",
            })
        if analysis.get("mergeable_prs"):
            next_priorities.append({
                "priority": 2,
                "description": f"Review {len(analysis['mergeable_prs'])} mergeable PRs",
            })
        if analysis.get("repos_missing_files"):
            next_priorities.append({
                "priority": 3,
                "description": f"Add missing files to {len(analysis['repos_missing_files'])} repos",
            })
        if analysis.get("stale_repos"):
            next_priorities.append({
                "priority": 4,
                "description": f"Address {len(analysis['stale_repos'])} stale repos",
            })

    # Repo details
    repo_summaries = []
    if state:
        for r in state.get("repos", []):
            repo_summaries.append({
                "name": r["name"],
                "visibility": r.get("visibility", "unknown"),
                "commits_24h": r.get("commits_24h", 0),
                "open_prs": len(r.get("open_prs", [])),
                "open_issues": len(r.get("open_issues", [])),
                "workflow_health": "healthy" if all(
                    run.get("conclusion") != "failure"
                    for run in r.get("workflow_runs", [])
                ) else "failing",
            })

    # Velocity (from learnings history)
    commits_7d = commits_24h * 7  # rough estimate; future cycles will have real data
    recent_decisions = [d for d in decisions[-50:]]
    prs_merged_7d = sum(
        1 for d in recent_decisions
        if d.get("action_type") == "review_pr" and d.get("success")
    )
    issues_closed_7d = sum(
        1 for d in recent_decisions
        if d.get("action_type") == "create_issue" and d.get("success")
    )

    capabilities_list = caps.get("capabilities", [
        "observe_ecosystem",
        "analyze_health",
        "create_issues",
        "generate_readmes",
        "generate_ci_workflows",
        "commit_files",
        "research_trends",
        "self_document",
        "adapt_priorities",
    ])

    dashboard = {
        "timestamp": utcnow(),
        "cycle_number": cycle_number,
        "ecosystem": {
            "total_repos": total_repos,
            "active_repos_24h": active_24h,
            "health_score": health_score,
            "total_open_prs": open_prs,
            "total_open_issues": open_issues,
            "failing_workflows": failing_workflows,
            "passing_workflows": passing_workflows,
        },
        "repos": repo_summaries,
        "velocity": {
            "commits_24h": commits_24h,
            "commits_7d": commits_7d,
            "prs_merged_7d": prs_merged_7d,
            "issues_closed_7d": issues_closed_7d,
        },
        "actions_taken": actions_taken,
        "next_priorities": next_priorities,
        "capabilities": capabilities_list,
        "meta": {
            "total_decisions_recorded": len(decisions),
            "total_learnings_recorded": len(learnings),
            "lifetime_actions": caps.get("lifetime_actions", 0),
            "lifetime_successes": caps.get("lifetime_successes", 0),
            "avg_success_rate": caps.get("avg_success_rate", 0),
        },
    }

    # Write dashboard
    os.makedirs(INTEL_DIR, exist_ok=True)
    try:
        with open(DASHBOARD_FILE, "w") as f:
            json.dump(dashboard, f, indent=2)
        print(f"    Dashboard written to {DASHBOARD_FILE}")
    except Exception as exc:
        print(f"  ⚠ Failed to write dashboard: {exc}")

    return dashboard


if __name__ == "__main__":
    dashboard = generate_dashboard()
    print(json.dumps(dashboard, indent=2))
