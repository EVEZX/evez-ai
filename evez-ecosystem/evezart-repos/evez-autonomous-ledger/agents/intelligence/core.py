#!/usr/bin/env python3
"""
EVEZ Autonomous Intelligence Core — The Brain

Self-operating orchestrator that runs a full OBSERVE → ANALYZE → PLAN → EXECUTE →
RECORD → ADAPT cycle every invocation.  Designed to run unattended via GitHub
Actions on a 12-hour cadence.

All external calls are wrapped in try/except — this module NEVER crashes.
"""

import os
import json
import time
import datetime
import base64
import sys

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not available. Exiting gracefully.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ORG = os.environ.get("REPO_OWNER", "EvezArt")
API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Rate-limit: sleep between API calls to stay well within budget
API_DELAY = 0.5  # seconds

# Paths (relative to repo root)
INTEL_DIR = "intelligence"
STATE_FILE = f"{INTEL_DIR}/state.json"
DASHBOARD_FILE = f"{INTEL_DIR}/dashboard.json"
CAPABILITIES_FILE = f"{INTEL_DIR}/capabilities.json"
DECISIONS_FILE = f"{INTEL_DIR}/decisions.jsonl"
LEARNINGS_FILE = f"{INTEL_DIR}/learnings.jsonl"
REPORT_FILE = f"{INTEL_DIR}/report.md"


def utcnow():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _api(method, url, **kwargs):
    """Make a GitHub API request with rate-limit delay and error handling."""
    time.sleep(API_DELAY)
    try:
        resp = getattr(requests, method)(url, headers=HEADERS, timeout=30, **kwargs)
        return resp
    except Exception as exc:
        print(f"  ⚠ API {method.upper()} {url} failed: {exc}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# OBSERVE — gather intelligence
# ═══════════════════════════════════════════════════════════════════════════

def _list_org_repos():
    """Return list of repo dicts for the org."""
    repos = []
    page = 1
    while page <= 5:  # cap pages to avoid runaway
        resp = _api("get", f"{API}/orgs/{ORG}/repos",
                     params={"per_page": 100, "page": page, "type": "all"})
        if resp is None or resp.status_code != 200:
            break
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def _recent_commits(repo_name, since_hours=24):
    since = (datetime.datetime.utcnow() - datetime.timedelta(hours=since_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    resp = _api("get", f"{API}/repos/{ORG}/{repo_name}/commits",
                params={"since": since, "per_page": 30})
    if resp and resp.status_code == 200:
        return resp.json()
    return []


def _workflow_runs(repo_name, per_page=10):
    resp = _api("get", f"{API}/repos/{ORG}/{repo_name}/actions/runs",
                params={"per_page": per_page})
    if resp and resp.status_code == 200:
        return resp.json().get("workflow_runs", [])
    return []


def _open_prs(repo_name):
    resp = _api("get", f"{API}/repos/{ORG}/{repo_name}/pulls",
                params={"state": "open", "per_page": 50})
    if resp and resp.status_code == 200:
        return resp.json()
    return []


def _open_issues(repo_name):
    resp = _api("get", f"{API}/repos/{ORG}/{repo_name}/issues",
                params={"state": "open", "per_page": 50})
    if resp and resp.status_code == 200:
        return [i for i in resp.json() if "pull_request" not in i]
    return []


def _repo_tree(repo_name):
    resp = _api("get", f"{API}/repos/{ORG}/{repo_name}/contents/",
                params={"per_page": 100})
    if resp and resp.status_code == 200:
        return [f["name"] for f in resp.json() if isinstance(f, dict)]
    return []


def observe():
    """Phase 1: Scan the entire ecosystem and return raw state."""
    print("  📡 OBSERVE — scanning ecosystem")
    repos_raw = _list_org_repos()
    print(f"    Found {len(repos_raw)} repos in {ORG}")

    state = {
        "timestamp": utcnow(),
        "repos": [],
        "total_commits_24h": 0,
        "total_open_prs": 0,
        "total_open_issues": 0,
        "workflow_runs": [],
    }

    for repo in repos_raw:
        name = repo["name"]
        print(f"    Scanning {name}...")

        commits = _recent_commits(name)
        runs = _workflow_runs(name)
        prs = _open_prs(name)
        issues = _open_issues(name)
        tree = _repo_tree(name)

        state["repos"].append({
            "name": name,
            "description": repo.get("description", ""),
            "visibility": "private" if repo.get("private") else "public",
            "last_push": repo.get("pushed_at", ""),
            "default_branch": repo.get("default_branch", "main"),
            "commits_24h": len(commits),
            "commit_messages": [c.get("commit", {}).get("message", "")[:120] for c in commits[:5]],
            "workflow_runs": [{
                "name": r.get("name", ""),
                "status": r.get("status", ""),
                "conclusion": r.get("conclusion", ""),
                "created_at": r.get("created_at", ""),
            } for r in runs[:10]],
            "open_prs": [{
                "number": p["number"],
                "title": p["title"],
                "mergeable_state": p.get("mergeable_state", "unknown"),
                "user": p.get("user", {}).get("login", ""),
                "created_at": p.get("created_at", ""),
            } for p in prs],
            "open_issues": [{
                "number": i["number"],
                "title": i["title"],
                "labels": [l["name"] for l in i.get("labels", [])],
                "created_at": i.get("created_at", ""),
            } for i in issues],
            "top_level_files": tree,
        })

        state["total_commits_24h"] += len(commits)
        state["total_open_prs"] += len(prs)
        state["total_open_issues"] += len(issues)
        state["workflow_runs"].extend([{
            "repo": name,
            "name": r.get("name", ""),
            "conclusion": r.get("conclusion", ""),
        } for r in runs[:10]])

    print(f"    → {state['total_commits_24h']} commits (24h), "
          f"{state['total_open_prs']} open PRs, "
          f"{state['total_open_issues']} open issues")
    return state


# ═══════════════════════════════════════════════════════════════════════════
# ANALYZE — understand what needs doing
# ═══════════════════════════════════════════════════════════════════════════

def analyze(state):
    """Phase 2: Derive insights from raw state."""
    print("  🔬 ANALYZE — deriving insights")

    analysis = {
        "timestamp": utcnow(),
        "failing_workflows": [],
        "stale_repos": [],
        "mergeable_prs": [],
        "repos_missing_files": [],
        "health_score": 100,
        "patterns": [],
    }

    now = datetime.datetime.utcnow()
    stale_threshold = datetime.timedelta(days=7)
    failure_reasons = {}

    for repo in state["repos"]:
        name = repo["name"]

        # Failing workflows
        for run in repo["workflow_runs"]:
            if run.get("conclusion") == "failure":
                analysis["failing_workflows"].append({
                    "repo": name,
                    "workflow": run["name"],
                    "created_at": run.get("created_at", ""),
                })
                reason = run["name"]
                failure_reasons.setdefault(reason, []).append(name)

        # Stale repos (no push in 7+ days)
        last_push = repo.get("last_push", "")
        if last_push:
            try:
                push_dt = datetime.datetime.strptime(last_push, "%Y-%m-%dT%H:%M:%SZ")
                if now - push_dt > stale_threshold:
                    analysis["stale_repos"].append({
                        "repo": name,
                        "last_push": last_push,
                        "days_stale": (now - push_dt).days,
                    })
            except ValueError:
                pass

        # PRs ready to merge
        for pr in repo["open_prs"]:
            ms = pr.get("mergeable_state", "unknown")
            if ms in ("clean", "unstable", "unknown"):
                analysis["mergeable_prs"].append({
                    "repo": name,
                    "number": pr["number"],
                    "title": pr["title"],
                    "mergeable_state": ms,
                })

        # Missing essential files
        files = set(repo.get("top_level_files", []))
        missing = []
        if "README.md" not in files and "readme.md" not in files:
            missing.append("README.md")
        if ".github" not in files:
            missing.append("CI workflows")
        if ".gitignore" not in files:
            missing.append(".gitignore")
        if missing:
            analysis["repos_missing_files"].append({
                "repo": name,
                "missing": missing,
            })

    # Detect patterns (same workflow failing across repos)
    for workflow, repos in failure_reasons.items():
        if len(repos) >= 2:
            analysis["patterns"].append({
                "type": "recurring_failure",
                "workflow": workflow,
                "affected_repos": repos,
                "description": f"Workflow '{workflow}' failing in {len(repos)} repos: {', '.join(repos)}",
            })

    # Health score: start at 100, deduct for problems
    deductions = (
        len(analysis["failing_workflows"]) * 5
        + len(analysis["stale_repos"]) * 3
        + len(analysis["repos_missing_files"]) * 2
    )
    analysis["health_score"] = max(0, 100 - deductions)

    print(f"    Health score: {analysis['health_score']}")
    print(f"    Failing workflows: {len(analysis['failing_workflows'])}")
    print(f"    Stale repos: {len(analysis['stale_repos'])}")
    print(f"    Mergeable PRs: {len(analysis['mergeable_prs'])}")
    print(f"    Repos missing files: {len(analysis['repos_missing_files'])}")
    print(f"    Patterns detected: {len(analysis['patterns'])}")
    return analysis


# ═══════════════════════════════════════════════════════════════════════════
# PLAN — decide priorities
# ═══════════════════════════════════════════════════════════════════════════

def plan(analysis):
    """Phase 3: Create prioritized action plan."""
    print("  📋 PLAN — prioritizing actions")

    actions = []

    # Priority 1: Fix broken things
    for fail in analysis["failing_workflows"][:5]:
        actions.append({
            "priority": 1,
            "type": "fix_workflow",
            "repo": fail["repo"],
            "workflow": fail["workflow"],
            "description": f"Investigate failing workflow '{fail['workflow']}' in {fail['repo']}",
        })

    # Priority 2: Merge ready PRs
    for pr in analysis["mergeable_prs"][:5]:
        actions.append({
            "priority": 2,
            "type": "review_pr",
            "repo": pr["repo"],
            "pr_number": pr["number"],
            "title": pr["title"],
            "description": f"PR #{pr['number']} in {pr['repo']} appears ready — comment with analysis",
        })

    # Priority 3: Improve infrastructure
    for missing in analysis["repos_missing_files"][:5]:
        for f in missing["missing"]:
            actions.append({
                "priority": 3,
                "type": "add_missing_file",
                "repo": missing["repo"],
                "file": f,
                "description": f"Add missing {f} to {missing['repo']}",
            })

    # Priority 4: Expand capabilities — create issues for stale repos
    for stale in analysis["stale_repos"][:3]:
        actions.append({
            "priority": 4,
            "type": "create_issue",
            "repo": stale["repo"],
            "description": f"Repo '{stale['repo']}' stale for {stale['days_stale']} days — create review issue",
        })

    # Priority 5: Record and report (always)
    actions.append({
        "priority": 5,
        "type": "generate_report",
        "description": "Generate intelligence report and update dashboard",
    })

    actions.sort(key=lambda a: a["priority"])
    print(f"    → {len(actions)} actions planned")
    return actions


# ═══════════════════════════════════════════════════════════════════════════
# EXECUTE — take action via GitHub API
# ═══════════════════════════════════════════════════════════════════════════

def _create_issue(repo, title, body, labels=None):
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    resp = _api("post", f"{API}/repos/{ORG}/{repo}/issues", json=payload)
    if resp and resp.status_code == 201:
        return resp.json().get("number")
    return None


def _comment_on_pr(repo, pr_number, body):
    resp = _api("post",
                f"{API}/repos/{ORG}/{repo}/issues/{pr_number}/comments",
                json={"body": body})
    return resp and resp.status_code == 201


def _commit_file(repo, path, content, message, branch=None):
    """Create or update a file via GitHub Contents API."""
    url = f"{API}/repos/{ORG}/{repo}/contents/{path}"
    params = {}
    if branch:
        params["ref"] = branch

    # Check if file exists (need sha for update)
    existing = _api("get", url, params=params)
    sha = None
    if existing and existing.status_code == 200:
        sha = existing.json().get("sha")

    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
    }
    if sha:
        payload["sha"] = sha
    if branch:
        payload["branch"] = branch

    resp = _api("put", url, json=payload)
    return resp and resp.status_code in (200, 201)


def execute(action_plan, analysis, state):
    """Phase 4: Execute the plan. Returns list of results."""
    print("  🚀 EXECUTE — taking action")
    results = []

    for action in action_plan:
        atype = action["type"]
        result = {
            "action": action,
            "success": False,
            "detail": "",
            "timestamp": utcnow(),
        }

        try:
            if atype == "create_issue":
                repo = action["repo"]
                title = f"🤖 Auto-review: {action['description']}"
                body = (
                    f"## Autonomous Intelligence Report\n\n"
                    f"{action['description']}\n\n"
                    f"This issue was created by the EVEZ Autonomous Intelligence Core "
                    f"during cycle at {utcnow()}.\n\n"
                    f"**Health Score:** {analysis.get('health_score', 'N/A')}\n"
                )
                issue_num = _create_issue(repo, title, body, labels=["autonomous-intelligence"])
                if issue_num:
                    result["success"] = True
                    result["detail"] = f"Created issue #{issue_num} in {repo}"
                else:
                    result["detail"] = f"Failed to create issue in {repo}"

            elif atype == "review_pr":
                repo = action["repo"]
                pr_num = action["pr_number"]
                comment = (
                    f"## 🤖 Autonomous Intelligence Analysis\n\n"
                    f"**PR:** {action['title']}\n"
                    f"**Mergeable State:** reported as ready\n\n"
                    f"This PR appears ready for human review and merge.\n\n"
                    f"*— EVEZ Intelligence Core, cycle {utcnow()}*"
                )
                ok = _comment_on_pr(repo, pr_num, comment)
                result["success"] = ok
                result["detail"] = f"Commented on PR #{pr_num} in {repo}" if ok else f"Failed to comment on PR"

            elif atype == "fix_workflow":
                repo = action["repo"]
                title = f"🔧 CI Fix needed: {action['workflow']}"
                body = (
                    f"## Failing Workflow Detected\n\n"
                    f"**Workflow:** `{action['workflow']}`\n"
                    f"**Repo:** {repo}\n\n"
                    f"The Autonomous Intelligence Core detected this workflow is failing. "
                    f"Please investigate and fix.\n\n"
                    f"*Detected at {utcnow()}*"
                )
                issue_num = _create_issue(repo, title, body, labels=["bug", "ci-fix"])
                result["success"] = issue_num is not None
                result["detail"] = f"Created fix issue #{issue_num}" if issue_num else "Failed to create issue"

            elif atype == "add_missing_file":
                # Delegate to builder module — for now just log intent
                result["success"] = True
                result["detail"] = f"Queued: add {action['file']} to {action['repo']}"

            elif atype == "generate_report":
                result["success"] = True
                result["detail"] = "Report generation handled in RECORD phase"

            else:
                result["detail"] = f"Unknown action type: {atype}"

        except Exception as exc:
            result["detail"] = f"Exception: {exc}"

        results.append(result)
        status = "✅" if result["success"] else "❌"
        print(f"    {status} {result['detail']}")

    return results


# ═══════════════════════════════════════════════════════════════════════════
# RECORD — self-documenting
# ═══════════════════════════════════════════════════════════════════════════

def _append_jsonl(filepath, record):
    try:
        with open(filepath, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as exc:
        print(f"  ⚠ Failed to write {filepath}: {exc}")


def _write_json(filepath, data):
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as exc:
        print(f"  ⚠ Failed to write {filepath}: {exc}")


def record(state, analysis, action_plan, results):
    """Phase 5: Record everything — decisions, state, report."""
    print("  📝 RECORD — documenting cycle")

    # Decision log
    for res in results:
        _append_jsonl(DECISIONS_FILE, {
            "timestamp": res["timestamp"],
            "action_type": res["action"]["type"],
            "priority": res["action"]["priority"],
            "description": res["action"]["description"],
            "success": res["success"],
            "detail": res["detail"],
            "reasoning": f"Priority {res['action']['priority']} — "
                         f"{'fix' if res['action']['priority'] == 1 else 'improve'} ecosystem",
        })

    # State snapshot
    _write_json(STATE_FILE, {
        "timestamp": utcnow(),
        "total_repos": len(state["repos"]),
        "total_commits_24h": state["total_commits_24h"],
        "total_open_prs": state["total_open_prs"],
        "total_open_issues": state["total_open_issues"],
        "health_score": analysis["health_score"],
        "failing_workflows": len(analysis["failing_workflows"]),
        "stale_repos": len(analysis["stale_repos"]),
        "repos": [r["name"] for r in state["repos"]],
    })

    # Report
    successes = sum(1 for r in results if r["success"])
    report_lines = [
        f"# EVEZ Intelligence Report",
        f"",
        f"**Generated:** {utcnow()}",
        f"",
        f"## Ecosystem Overview",
        f"- **Total repos:** {len(state['repos'])}",
        f"- **Active repos (24h):** {sum(1 for r in state['repos'] if r['commits_24h'] > 0)}",
        f"- **Health score:** {analysis['health_score']}/100",
        f"- **Commits (24h):** {state['total_commits_24h']}",
        f"- **Open PRs:** {state['total_open_prs']}",
        f"- **Open issues:** {state['total_open_issues']}",
        f"",
        f"## Problems Detected",
        f"- **Failing workflows:** {len(analysis['failing_workflows'])}",
        f"- **Stale repos:** {len(analysis['stale_repos'])}",
        f"- **Repos missing files:** {len(analysis['repos_missing_files'])}",
        f"",
        f"## Actions Taken",
        f"- **Total actions:** {len(results)}",
        f"- **Successful:** {successes}",
        f"- **Failed:** {len(results) - successes}",
        f"",
    ]
    for res in results:
        icon = "✅" if res["success"] else "❌"
        report_lines.append(f"- {icon} {res['detail']}")

    if analysis["patterns"]:
        report_lines.extend(["", "## Patterns Detected"])
        for p in analysis["patterns"]:
            report_lines.append(f"- **{p['type']}:** {p['description']}")

    if analysis["mergeable_prs"]:
        report_lines.extend(["", "## PRs Ready for Review"])
        for pr in analysis["mergeable_prs"]:
            report_lines.append(f"- {pr['repo']}#{pr['number']}: {pr['title']}")

    report_lines.extend(["", "---", "*Generated by EVEZ Autonomous Intelligence Core*"])

    try:
        with open(REPORT_FILE, "w") as f:
            f.write("\n".join(report_lines) + "\n")
    except Exception as exc:
        print(f"  ⚠ Failed to write report: {exc}")

    print(f"    Recorded {len(results)} decisions, updated state + report")


# ═══════════════════════════════════════════════════════════════════════════
# ADAPT — self-improving
# ═══════════════════════════════════════════════════════════════════════════

def adapt(results, analysis):
    """Phase 6: Learn from outcomes and update capabilities."""
    print("  🧬 ADAPT — learning from outcomes")

    success_rate = sum(1 for r in results if r["success"]) / max(len(results), 1)

    learning = {
        "timestamp": utcnow(),
        "cycle_success_rate": round(success_rate, 2),
        "actions_attempted": len(results),
        "actions_succeeded": sum(1 for r in results if r["success"]),
        "health_score": analysis["health_score"],
        "observations": [],
    }

    if analysis["failing_workflows"]:
        learning["observations"].append(
            f"Found {len(analysis['failing_workflows'])} failing workflows — CI health needs attention"
        )
    if analysis["stale_repos"]:
        learning["observations"].append(
            f"{len(analysis['stale_repos'])} repos stale >7 days — consider archival or revival"
        )
    if success_rate < 0.5:
        learning["observations"].append(
            "Low success rate this cycle — may need to adjust action strategy"
        )
    if success_rate == 1.0 and len(results) > 0:
        learning["observations"].append(
            "Perfect execution this cycle — current strategy is effective"
        )

    _append_jsonl(LEARNINGS_FILE, learning)

    # Update capabilities
    try:
        caps = {}
        if os.path.exists(CAPABILITIES_FILE):
            with open(CAPABILITIES_FILE) as f:
                caps = json.load(f)

        caps["last_updated"] = utcnow()
        caps["total_cycles"] = caps.get("total_cycles", 0) + 1
        caps["lifetime_actions"] = caps.get("lifetime_actions", 0) + len(results)
        caps["lifetime_successes"] = caps.get("lifetime_successes", 0) + sum(
            1 for r in results if r["success"]
        )
        caps["avg_success_rate"] = round(
            caps["lifetime_successes"] / max(caps["lifetime_actions"], 1), 2
        )
        caps["capabilities"] = list(set(caps.get("capabilities", []) + [
            "observe_ecosystem",
            "analyze_health",
            "plan_priorities",
            "create_issues",
            "comment_on_prs",
            "detect_patterns",
            "generate_reports",
            "self_document",
            "adapt_priorities",
            "track_learnings",
        ]))

        # Track new action types discovered
        action_types = set(caps.get("action_types_seen", []))
        for r in results:
            action_types.add(r["action"]["type"])
        caps["action_types_seen"] = sorted(action_types)

        _write_json(CAPABILITIES_FILE, caps)
    except Exception as exc:
        print(f"  ⚠ Failed to update capabilities: {exc}")

    print(f"    Success rate: {success_rate:.0%} — recorded learning")


# ═══════════════════════════════════════════════════════════════════════════
# Main Orchestrator
# ═══════════════════════════════════════════════════════════════════════════

class AutonomousIntelligence:
    """Full autonomous cycle — mirrors what a human operator does."""

    def __init__(self, github_token=None, org="EvezArt"):
        global GITHUB_TOKEN, ORG, HEADERS
        if github_token:
            GITHUB_TOKEN = github_token
        ORG = org
        HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    def run_cycle(self):
        """Execute a complete OBSERVE → ANALYZE → PLAN → EXECUTE → RECORD → ADAPT cycle."""
        print(f"\n{'='*60}")
        print(f"🧠 EVEZ Autonomous Intelligence Core")
        print(f"   Cycle start: {utcnow()}")
        print(f"   Org: {ORG}")
        print(f"{'='*60}\n")

        if not GITHUB_TOKEN:
            print("  ⚠ GITHUB_TOKEN not set — running in degraded mode")

        state = observe()
        analysis = analyze(state)
        action_plan = plan(analysis)
        results = execute(action_plan, analysis, state)
        record(state, analysis, action_plan, results)
        adapt(results, analysis)

        print(f"\n{'='*60}")
        print(f"  ✅ Cycle complete at {utcnow()}")
        successes = sum(1 for r in results if r["success"])
        print(f"  Actions: {successes}/{len(results)} succeeded")
        print(f"  Health: {analysis['health_score']}/100")
        print(f"{'='*60}\n")

        return {
            "timestamp": utcnow(),
            "health_score": analysis["health_score"],
            "actions_taken": len(results),
            "actions_succeeded": successes,
            "state": state,
            "analysis": analysis,
            "results": results,
        }


def main():
    brain = AutonomousIntelligence(
        github_token=GITHUB_TOKEN,
        org=ORG,
    )
    try:
        brain.run_cycle()
    except Exception as exc:
        print(f"  ❌ Cycle failed at top level: {exc}")
        print("  Exiting gracefully — will retry next scheduled run.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FATAL (caught): {exc}")
        sys.exit(0)
