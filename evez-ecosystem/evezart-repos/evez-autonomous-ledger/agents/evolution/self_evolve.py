#!/usr/bin/env python3
"""
EVEZ Self-Evolution Engine — OODA Loop

Observe → Orient → Decide → Act

Runs every 6 hours via GitHub Actions. Scans the entire EvezArt org,
evaluates ecosystem health, identifies problems and opportunities,
takes corrective action, and records everything for the next cycle.

The system is IMMORTAL — it handles all errors gracefully and never crashes.
"""
import os
import sys
import json
import hashlib
import logging
import datetime

try:
    import requests
except ImportError:
    print("ERROR: 'requests' module not available. Exiting gracefully.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "EvezArt"
HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVOLUTION_DIR = os.path.join(BASE_DIR, "evolution")
STATE_PATH = os.path.join(EVOLUTION_DIR, "state.json")
PLAN_PATH = os.path.join(EVOLUTION_DIR, "plan.json")
DECISIONS_PATH = os.path.join(EVOLUTION_DIR, "decisions.jsonl")
REPORTS_DIR = os.path.join(EVOLUTION_DIR, "reports")

STALE_DAYS = 7
MAX_ISSUES_PER_CYCLE = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("self_evolve")


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def days_since(iso_str):
    """Return days elapsed since an ISO timestamp string."""
    try:
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        delta = datetime.datetime.utcnow().replace(tzinfo=dt.tzinfo) - dt
        return delta.total_seconds() / 86400
    except Exception:
        return 999


def gh_get(url, params=None):
    """Make an authenticated GET to the GitHub API."""
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=20)
        if r.status_code == 200:
            return r.json()
        log.warning("GET %s → %d", url, r.status_code)
    except Exception as e:
        log.warning("GET %s failed: %s", url, e)
    return None


def gh_post(url, payload):
    """Make an authenticated POST to the GitHub API."""
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=20)
        return r.status_code in (200, 201), r.status_code
    except Exception as e:
        log.warning("POST %s failed: %s", url, e)
        return False, 0


def load_state():
    """Load previous evolution state from disk."""
    try:
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, "r") as f:
                return json.load(f)
    except Exception as e:
        log.warning("load_state: %s", e)
    return {
        "last_updated": None,
        "cycle": 0,
        "repos": {},
        "previous_health_score": None,
        "improvements_made": 0,
        "issues_created": 0,
    }


def save_state(state):
    """Persist evolution state to disk."""
    try:
        os.makedirs(EVOLUTION_DIR, exist_ok=True)
        with open(STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
        log.info("State saved to %s", STATE_PATH)
    except Exception as e:
        log.error("save_state: %s", e)


def save_plan(plan):
    """Persist the current action plan to disk."""
    try:
        os.makedirs(EVOLUTION_DIR, exist_ok=True)
        with open(PLAN_PATH, "w") as f:
            json.dump(plan, f, indent=2)
        log.info("Plan saved to %s", PLAN_PATH)
    except Exception as e:
        log.error("save_plan: %s", e)


def append_decision(decision):
    """Append a decision record to the decisions log."""
    try:
        os.makedirs(EVOLUTION_DIR, exist_ok=True)
        with open(DECISIONS_PATH, "a") as f:
            f.write(json.dumps(decision) + "\n")
    except Exception as e:
        log.error("append_decision: %s", e)


def save_report(report):
    """Save a timestamped evolution report."""
    try:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        ts = now_iso().replace(":", "-").replace(".", "-")
        path = os.path.join(REPORTS_DIR, f"{ts}_evolution.json")
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        log.info("Report saved: %s", path)
    except Exception as e:
        log.error("save_report: %s", e)


# ===========================================================================
# OBSERVE — scan the entire EvezArt org
# ===========================================================================

def observe():
    """Scan all repos in the EvezArt org and collect ecosystem state."""
    log.info("=== OBSERVE ===")
    ecosystem = {
        "timestamp": now_iso(),
        "repos": {},
        "total_repos": 0,
        "total_open_issues": 0,
        "total_open_prs": 0,
        "total_commits_24h": 0,
        "total_commits_7d": 0,
        "failing_workflows": [],
    }

    # Discover repos in the org
    repos_data = gh_get(f"https://api.github.com/orgs/{OWNER}/repos", {"per_page": 100})
    if not repos_data:
        # Fallback: try as user
        repos_data = gh_get(f"https://api.github.com/users/{OWNER}/repos", {"per_page": 100, "type": "owner"})
    if not repos_data:
        log.error("Could not list repos for %s", OWNER)
        return ecosystem

    ecosystem["total_repos"] = len(repos_data)
    log.info("Found %d repos in %s", len(repos_data), OWNER)

    for repo_info in repos_data:
        repo_name = repo_info.get("name", "unknown")
        log.info("  Scanning %s...", repo_name)
        repo_state = observe_repo(repo_name, repo_info)
        ecosystem["repos"][repo_name] = repo_state

        ecosystem["total_open_issues"] += repo_state.get("open_issues", 0)
        ecosystem["total_open_prs"] += repo_state.get("open_prs", 0)
        ecosystem["total_commits_24h"] += repo_state.get("commits_24h", 0)
        ecosystem["total_commits_7d"] += repo_state.get("commits_7d", 0)
        ecosystem["failing_workflows"].extend(repo_state.get("failing_workflows", []))

    return ecosystem


def observe_repo(repo_name, repo_info):
    """Collect state for a single repo."""
    state = {
        "name": repo_name,
        "last_push": repo_info.get("pushed_at"),
        "last_commit": None,
        "last_commit_message": None,
        "open_issues": 0,
        "open_prs": 0,
        "commits_24h": 0,
        "commits_7d": 0,
        "ci_status": "unknown",
        "failing_workflows": [],
        "stale": False,
        "health": 100,
    }

    # Last commit
    commits = gh_get(
        f"https://api.github.com/repos/{OWNER}/{repo_name}/commits",
        {"per_page": 1},
    )
    if commits and len(commits) > 0:
        state["last_commit"] = commits[0].get("commit", {}).get("committer", {}).get("date")
        state["last_commit_message"] = commits[0].get("commit", {}).get("message", "")[:200]

    # Staleness
    push_date = state["last_push"] or state["last_commit"]
    if push_date:
        state["stale"] = days_since(push_date) > STALE_DAYS

    # Commit velocity (24h and 7d)
    now = datetime.datetime.utcnow()
    since_24h = (now - datetime.timedelta(days=1)).isoformat() + "Z"
    since_7d = (now - datetime.timedelta(days=7)).isoformat() + "Z"

    commits_24h_data = gh_get(
        f"https://api.github.com/repos/{OWNER}/{repo_name}/commits",
        {"since": since_24h, "per_page": 100},
    )
    if commits_24h_data:
        state["commits_24h"] = len(commits_24h_data)

    commits_7d_data = gh_get(
        f"https://api.github.com/repos/{OWNER}/{repo_name}/commits",
        {"since": since_7d, "per_page": 100},
    )
    if commits_7d_data:
        state["commits_7d"] = len(commits_7d_data)

    # Open issues and PRs
    issues = gh_get(
        f"https://api.github.com/repos/{OWNER}/{repo_name}/issues",
        {"state": "open", "per_page": 100},
    )
    if issues:
        prs = [i for i in issues if i.get("pull_request")]
        state["open_prs"] = len(prs)
        state["open_issues"] = len(issues) - len(prs)

    # Workflow status — check last run
    runs = gh_get(
        f"https://api.github.com/repos/{OWNER}/{repo_name}/actions/runs",
        {"per_page": 10},
    )
    if runs and runs.get("workflow_runs"):
        latest = runs["workflow_runs"][0]
        conclusion = latest.get("conclusion")
        if conclusion == "success":
            state["ci_status"] = "passing"
        elif conclusion == "failure":
            state["ci_status"] = "failing"
        elif latest.get("status") == "in_progress":
            state["ci_status"] = "running"
        else:
            state["ci_status"] = conclusion or "unknown"

        # Collect all failing workflows from recent runs
        for run in runs["workflow_runs"]:
            if run.get("conclusion") == "failure":
                state["failing_workflows"].append({
                    "name": run.get("name", "unknown"),
                    "repo": repo_name,
                    "run_id": run.get("id"),
                    "url": run.get("html_url", ""),
                    "created_at": run.get("created_at"),
                })

    return state


# ===========================================================================
# ORIENT — compare, score, and identify opportunities
# ===========================================================================

def orient(ecosystem, previous_state):
    """Analyze ecosystem state and compute health scores."""
    log.info("=== ORIENT ===")

    analysis = {
        "timestamp": now_iso(),
        "health_score": 100,
        "repo_scores": {},
        "failing_repos": [],
        "stale_repos": [],
        "unmerged_prs": [],
        "new_issues": [],
        "improvements": [],
        "degradations": [],
    }

    total_score = 0
    repo_count = 0

    for repo_name, repo_state in ecosystem.get("repos", {}).items():
        score = compute_repo_health(repo_state)
        repo_state["health"] = score
        analysis["repo_scores"][repo_name] = score
        total_score += score
        repo_count += 1

        if repo_state.get("ci_status") == "failing":
            analysis["failing_repos"].append(repo_name)

        if repo_state.get("stale"):
            analysis["stale_repos"].append(repo_name)

        if repo_state.get("open_prs", 0) > 0:
            analysis["unmerged_prs"].append({
                "repo": repo_name,
                "count": repo_state["open_prs"],
            })

    # Overall health score
    if repo_count > 0:
        analysis["health_score"] = round(total_score / repo_count)
    else:
        analysis["health_score"] = 0

    # Compare to previous state
    prev_score = previous_state.get("previous_health_score")
    if prev_score is not None:
        if analysis["health_score"] > prev_score:
            analysis["improvements"].append(
                f"Health improved: {prev_score} → {analysis['health_score']}"
            )
        elif analysis["health_score"] < prev_score:
            analysis["degradations"].append(
                f"Health degraded: {prev_score} → {analysis['health_score']}"
            )

    log.info("  Ecosystem health: %d/100", analysis["health_score"])
    log.info("  Failing repos: %s", analysis["failing_repos"] or "none")
    log.info("  Stale repos: %s", analysis["stale_repos"] or "none")
    log.info("  Repos with unmerged PRs: %d", len(analysis["unmerged_prs"]))

    return analysis


def compute_repo_health(repo_state):
    """Compute a 0-100 health score for a single repo."""
    score = 100

    # CI status
    ci = repo_state.get("ci_status", "unknown")
    if ci == "failing":
        score -= 30
    elif ci == "unknown":
        score -= 10

    # Staleness
    if repo_state.get("stale"):
        score -= 20

    # Too many open issues
    open_issues = repo_state.get("open_issues", 0)
    if open_issues > 20:
        score -= 15
    elif open_issues > 10:
        score -= 10
    elif open_issues > 5:
        score -= 5

    # Unmerged PRs piling up
    open_prs = repo_state.get("open_prs", 0)
    if open_prs > 10:
        score -= 15
    elif open_prs > 5:
        score -= 10
    elif open_prs > 2:
        score -= 5

    # No recent commits at all
    if repo_state.get("commits_7d", 0) == 0:
        score -= 10

    return max(0, min(100, score))


# ===========================================================================
# DECIDE — prioritize and plan actions
# ===========================================================================

def decide(analysis, ecosystem, previous_state):
    """Generate an action plan based on the analysis."""
    log.info("=== DECIDE ===")

    actions = []

    # Priority 1: Fix failing workflows
    for repo_name in analysis.get("failing_repos", []):
        repo_data = ecosystem["repos"].get(repo_name, {})
        failing = repo_data.get("failing_workflows", [])
        if failing:
            actions.append({
                "priority": 1,
                "type": "fix_failure",
                "repo": repo_name,
                "target": failing[0].get("name", "unknown"),
                "url": failing[0].get("url", ""),
                "reason": f"Workflow '{failing[0].get('name')}' is failing in {repo_name}",
            })

    # Priority 2: Flag stale repos
    for repo_name in analysis.get("stale_repos", []):
        actions.append({
            "priority": 2,
            "type": "flag_stale",
            "repo": repo_name,
            "reason": f"{repo_name} has had no activity in {STALE_DAYS}+ days",
        })

    # Priority 3: Flag repos with many unmerged PRs
    for pr_info in analysis.get("unmerged_prs", []):
        if pr_info["count"] > 3:
            actions.append({
                "priority": 3,
                "type": "flag_unmerged_prs",
                "repo": pr_info["repo"],
                "count": pr_info["count"],
                "reason": f"{pr_info['repo']} has {pr_info['count']} unmerged PRs",
            })

    # Sort by priority
    actions.sort(key=lambda a: a.get("priority", 99))

    plan = {
        "last_updated": now_iso(),
        "cycle": previous_state.get("cycle", 0) + 1,
        "health_score": analysis.get("health_score", 0),
        "actions": actions,
        "total_actions": len(actions),
        "priority": "critical" if analysis.get("failing_repos") else
                    "warning" if analysis.get("stale_repos") else "healthy",
        "reasoning": generate_reasoning(analysis),
    }

    # Log decision
    decision_record = {
        "timestamp": now_iso(),
        "cycle": plan["cycle"],
        "health_score": plan["health_score"],
        "actions_planned": len(actions),
        "priority": plan["priority"],
        "failing_repos": analysis.get("failing_repos", []),
        "stale_repos": analysis.get("stale_repos", []),
    }
    append_decision(decision_record)

    log.info("  Plan: %d actions, priority=%s", len(actions), plan["priority"])
    for a in actions[:5]:
        log.info("    [P%d] %s: %s", a["priority"], a["type"], a["reason"])

    return plan


def generate_reasoning(analysis):
    """Generate human-readable reasoning for the plan."""
    parts = []
    score = analysis.get("health_score", 0)
    parts.append(f"Ecosystem health: {score}/100.")

    if analysis.get("failing_repos"):
        parts.append(
            f"Critical: {len(analysis['failing_repos'])} repo(s) have failing CI "
            f"({', '.join(analysis['failing_repos'])}). Fix these first."
        )

    if analysis.get("stale_repos"):
        parts.append(
            f"Warning: {len(analysis['stale_repos'])} repo(s) are stale "
            f"({', '.join(analysis['stale_repos'][:5])}). "
            f"Consider archiving or reviving."
        )

    if analysis.get("unmerged_prs"):
        total_prs = sum(p["count"] for p in analysis["unmerged_prs"])
        parts.append(f"{total_prs} unmerged PR(s) across the ecosystem.")

    if analysis.get("improvements"):
        parts.append(" ".join(analysis["improvements"]))

    if analysis.get("degradations"):
        parts.append(" ".join(analysis["degradations"]))

    if not parts[1:]:
        parts.append("All systems nominal. No action required.")

    return " ".join(parts)


# ===========================================================================
# ACT — execute the plan
# ===========================================================================

def act(plan, ecosystem, previous_state):
    """Execute actions from the plan."""
    log.info("=== ACT ===")

    issues_created = 0
    improvements_made = 0

    for action in plan.get("actions", []):
        if issues_created >= MAX_ISSUES_PER_CYCLE:
            log.info("  Issue limit reached (%d), deferring remaining actions", MAX_ISSUES_PER_CYCLE)
            break

        action_type = action.get("type")

        if action_type == "fix_failure":
            created = create_failure_issue(action)
            if created:
                issues_created += 1
                improvements_made += 1

        elif action_type == "flag_stale":
            created = create_stale_issue(action)
            if created:
                issues_created += 1

        elif action_type == "flag_unmerged_prs":
            created = create_unmerged_prs_issue(action)
            if created:
                issues_created += 1

    # Update state
    new_state = {
        "last_updated": now_iso(),
        "cycle": plan.get("cycle", 1),
        "repos": {},
        "previous_health_score": plan.get("health_score"),
        "improvements_made": previous_state.get("improvements_made", 0) + improvements_made,
        "issues_created": previous_state.get("issues_created", 0) + issues_created,
    }

    # Store per-repo state for next cycle comparison
    for repo_name, repo_data in ecosystem.get("repos", {}).items():
        new_state["repos"][repo_name] = {
            "health": repo_data.get("health", 0),
            "ci_status": repo_data.get("ci_status", "unknown"),
            "last_commit": repo_data.get("last_commit"),
            "open_prs": repo_data.get("open_prs", 0),
            "open_issues": repo_data.get("open_issues", 0),
            "commits_7d": repo_data.get("commits_7d", 0),
        }

    save_state(new_state)
    save_plan(plan)

    # Save report
    report = {
        "timestamp": now_iso(),
        "cycle": plan.get("cycle", 1),
        "health_score": plan.get("health_score", 0),
        "actions_taken": issues_created,
        "improvements": improvements_made,
        "plan_summary": plan.get("reasoning", ""),
        "repo_scores": {
            name: data.get("health", 0)
            for name, data in ecosystem.get("repos", {}).items()
        },
    }
    save_report(report)

    log.info("  Actions completed: %d issues created, %d improvements", issues_created, improvements_made)
    return new_state


def create_failure_issue(action):
    """Create a GitHub issue for a failing workflow."""
    repo = action.get("repo", "evez-autonomous-ledger")
    target = action.get("target", "unknown")
    url = action.get("url", "")

    # Check for existing open issue to avoid duplicates
    existing = gh_get(
        f"https://api.github.com/repos/{OWNER}/{repo}/issues",
        {"state": "open", "labels": "evolution-engine", "per_page": 50},
    )
    if existing:
        for issue in existing:
            if target in issue.get("title", ""):
                log.info("  Skipping duplicate issue for %s/%s", repo, target)
                return False

    body = (
        f"The evolution engine detected a failing workflow.\n\n"
        f"**Workflow:** {target}\n"
        f"**Repo:** {OWNER}/{repo}\n"
        f"**Run URL:** {url}\n\n"
        f"### Action Required\n"
        f"1. Check the workflow logs for the root cause\n"
        f"2. Fix the underlying issue\n"
        f"3. Verify the workflow passes\n\n"
        f"*Auto-created by self_evolve.py — Evolution Engine cycle*"
    )

    ok, status = gh_post(
        f"https://api.github.com/repos/{OWNER}/{repo}/issues",
        {
            "title": f"[EVOLUTION] Fix failing workflow: {target}",
            "body": body,
            "labels": ["evolution-engine", "autonomous-repair"],
        },
    )
    if ok:
        log.info("  Created issue: fix %s in %s", target, repo)
    else:
        log.warning("  Failed to create issue (HTTP %d)", status)
    return ok


def create_stale_issue(action):
    """Create a GitHub issue for a stale repo."""
    repo = action.get("repo", "evez-autonomous-ledger")

    existing = gh_get(
        f"https://api.github.com/repos/{OWNER}/{repo}/issues",
        {"state": "open", "labels": "evolution-engine", "per_page": 50},
    )
    if existing:
        for issue in existing:
            if "stale" in issue.get("title", "").lower():
                log.info("  Skipping duplicate stale issue for %s", repo)
                return False

    body = (
        f"The evolution engine detected that **{repo}** has had no activity "
        f"in {STALE_DAYS}+ days.\n\n"
        f"### Options\n"
        f"- Archive the repo if it's no longer needed\n"
        f"- Push a maintenance commit to keep it alive\n"
        f"- Add it to the evolution engine's ignore list\n\n"
        f"*Auto-created by self_evolve.py — Evolution Engine cycle*"
    )

    ok, _ = gh_post(
        f"https://api.github.com/repos/{OWNER}/{repo}/issues",
        {
            "title": f"[EVOLUTION] Repo stale — no activity in {STALE_DAYS}+ days",
            "body": body,
            "labels": ["evolution-engine", "maintenance"],
        },
    )
    if ok:
        log.info("  Created stale issue for %s", repo)
    return ok


def create_unmerged_prs_issue(action):
    """Create a GitHub issue for repos with too many unmerged PRs."""
    repo = action.get("repo", "evez-autonomous-ledger")
    count = action.get("count", 0)

    existing = gh_get(
        f"https://api.github.com/repos/{OWNER}/{repo}/issues",
        {"state": "open", "labels": "evolution-engine", "per_page": 50},
    )
    if existing:
        for issue in existing:
            if "unmerged" in issue.get("title", "").lower():
                log.info("  Skipping duplicate unmerged PRs issue for %s", repo)
                return False

    body = (
        f"The evolution engine detected **{count}** unmerged pull requests in "
        f"**{repo}**.\n\n"
        f"### Action Required\n"
        f"- Review and merge ready PRs\n"
        f"- Close stale or abandoned PRs\n"
        f"- Consider enabling auto-merge for trusted authors\n\n"
        f"*Auto-created by self_evolve.py — Evolution Engine cycle*"
    )

    ok, _ = gh_post(
        f"https://api.github.com/repos/{OWNER}/{repo}/issues",
        {
            "title": f"[EVOLUTION] {count} unmerged PRs need attention",
            "body": body,
            "labels": ["evolution-engine", "maintenance"],
        },
    )
    if ok:
        log.info("  Created unmerged PRs issue for %s", repo)
    return ok


# ===========================================================================
# Main — OODA Loop
# ===========================================================================

def main():
    print(f"\n{'='*60}")
    print(f"  EVEZ SELF-EVOLUTION ENGINE — {now_iso()}")
    print(f"  OODA Loop: Observe → Orient → Decide → Act")
    print(f"{'='*60}\n")

    if not GH_TOKEN:
        log.error("GITHUB_TOKEN not set. Cannot proceed.")
        return

    # Load previous state
    previous_state = load_state()
    cycle = previous_state.get("cycle", 0) + 1
    log.info("Starting evolution cycle #%d", cycle)
    log.info("Previous health score: %s", previous_state.get("previous_health_score", "N/A"))

    # OBSERVE
    ecosystem = observe()
    log.info("Observed %d repos, %d total commits (7d)",
             ecosystem["total_repos"], ecosystem["total_commits_7d"])

    # ORIENT
    analysis = orient(ecosystem, previous_state)

    # DECIDE
    plan = decide(analysis, ecosystem, previous_state)

    # ACT
    new_state = act(plan, ecosystem, previous_state)

    # Summary
    print(f"\n{'='*60}")
    print(f"  Evolution Cycle #{cycle} Complete")
    print(f"  Health Score: {plan.get('health_score', 0)}/100")
    print(f"  Actions: {plan.get('total_actions', 0)} planned")
    print(f"  Issues Created (this cycle): {new_state.get('issues_created', 0) - previous_state.get('issues_created', 0)}")
    print(f"  Total Issues Created (all time): {new_state.get('issues_created', 0)}")
    print(f"  Total Improvements (all time): {new_state.get('improvements_made', 0)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("FATAL: %s", e, exc_info=True)
        # Never crash — exit cleanly for GitHub Actions
        sys.exit(0)
