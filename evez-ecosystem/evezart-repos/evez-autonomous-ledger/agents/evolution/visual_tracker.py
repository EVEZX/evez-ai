#!/usr/bin/env python3
"""
EVEZ Visual Tracker — Dashboard Data Generator

Reads the evolution state and generates a dashboard.json file
with ecosystem health metrics, per-repo scores, commit velocity,
workflow success rates, and evolution history.

Runs after self_evolve.py in the same GitHub Actions workflow.
"""
import os
import sys
import json
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
DASHBOARD_PATH = os.path.join(EVOLUTION_DIR, "dashboard.json")
MAX_HISTORY_POINTS = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("visual_tracker")


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def load_json(path, default=None):
    """Load a JSON file, returning default if missing or invalid."""
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception as e:
        log.warning("load_json(%s): %s", path, e)
    return default if default is not None else {}


def save_json(path, data):
    """Save data as JSON."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        log.info("Saved: %s", path)
    except Exception as e:
        log.error("save_json(%s): %s", path, e)


def gh_get(url, params=None):
    """Make an authenticated GET to the GitHub API."""
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        log.warning("GET %s failed: %s", url, e)
    return None


def compute_workflow_success_rate(repo_name):
    """Compute the success rate of recent workflow runs for a repo."""
    runs = gh_get(
        f"https://api.github.com/repos/{OWNER}/{repo_name}/actions/runs",
        {"per_page": 30},
    )
    if not runs or not runs.get("workflow_runs"):
        return None

    total = 0
    successes = 0
    for run in runs["workflow_runs"]:
        conclusion = run.get("conclusion")
        if conclusion in ("success", "failure"):
            total += 1
            if conclusion == "success":
                successes += 1

    if total == 0:
        return None
    return round((successes / total) * 100, 1)


def build_dashboard():
    """Build the dashboard data from evolution state."""
    log.info("Building dashboard...")

    # Load current state
    state = load_json(STATE_PATH, {
        "cycle": 0,
        "repos": {},
        "previous_health_score": 0,
        "improvements_made": 0,
        "issues_created": 0,
    })

    # Load existing dashboard for history
    existing = load_json(DASHBOARD_PATH, {
        "history": [],
    })

    # Build per-repo entries
    repos = []
    total_commits_24h = 0
    total_commits_7d = 0
    total_health = 0
    repo_count = 0

    for repo_name, repo_data in state.get("repos", {}).items():
        health = repo_data.get("health", 0)
        total_health += health
        repo_count += 1

        commits_7d = repo_data.get("commits_7d", 0)
        total_commits_7d += commits_7d

        # Compute workflow success rate (live API call)
        success_rate = compute_workflow_success_rate(repo_name)

        repos.append({
            "name": repo_name,
            "health": health,
            "last_commit": repo_data.get("last_commit"),
            "ci_status": repo_data.get("ci_status", "unknown"),
            "open_prs": repo_data.get("open_prs", 0),
            "open_issues": repo_data.get("open_issues", 0),
            "workflow_success_rate": success_rate,
        })

    # Sort repos by health (worst first, so problems are visible)
    repos.sort(key=lambda r: r.get("health", 0))

    # Overall health score
    health_score = round(total_health / repo_count) if repo_count > 0 else 0

    # Compute velocity from state data
    for repo_name, repo_data in state.get("repos", {}).items():
        # Rough 24h estimate: commits_7d / 7
        pass

    # Use the state's cycle commits for 24h velocity
    # We'll derive it from the per-repo data
    commits_24h_total = 0
    for repo_name in state.get("repos", {}):
        # Get fresh 24h commits count
        now = datetime.datetime.utcnow()
        since_24h = (now - datetime.timedelta(days=1)).isoformat() + "Z"
        commits_data = gh_get(
            f"https://api.github.com/repos/{OWNER}/{repo_name}/commits",
            {"since": since_24h, "per_page": 100},
        )
        if commits_data:
            commits_24h_total += len(commits_data)

    commits_7d_avg = round(total_commits_7d / 7, 1) if total_commits_7d > 0 else 0

    # Build history (keep last N data points)
    history = existing.get("history", [])
    history.append({
        "timestamp": now_iso(),
        "health_score": health_score,
        "cycle": state.get("cycle", 0),
        "commits_24h": commits_24h_total,
        "repos_count": repo_count,
    })
    # Trim to max points
    if len(history) > MAX_HISTORY_POINTS:
        history = history[-MAX_HISTORY_POINTS:]

    # Assemble dashboard
    dashboard = {
        "last_updated": now_iso(),
        "health_score": health_score,
        "repos": repos,
        "velocity": {
            "commits_24h": commits_24h_total,
            "commits_7d_avg": commits_7d_avg,
        },
        "evolution_cycle": state.get("cycle", 0),
        "improvements_made": state.get("improvements_made", 0),
        "issues_created": state.get("issues_created", 0),
        "history": history,
    }

    save_json(DASHBOARD_PATH, dashboard)

    log.info("Dashboard built:")
    log.info("  Health Score: %d/100", health_score)
    log.info("  Repos tracked: %d", repo_count)
    log.info("  Commits (24h): %d", commits_24h_total)
    log.info("  Commits (7d avg/day): %.1f", commits_7d_avg)
    log.info("  Evolution cycle: %d", state.get("cycle", 0))
    log.info("  History points: %d", len(history))

    return dashboard


def main():
    print(f"\n{'='*60}")
    print(f"  EVEZ VISUAL TRACKER — {now_iso()}")
    print(f"  Generating dashboard.json")
    print(f"{'='*60}\n")

    if not GH_TOKEN:
        log.error("GITHUB_TOKEN not set. Cannot query GitHub API.")
        # Still try to build from cached state
        log.info("Attempting to build dashboard from cached state only...")

    dashboard = build_dashboard()

    print(f"\n  Dashboard generated: {DASHBOARD_PATH}")
    print(f"  Health: {dashboard.get('health_score', 0)}/100")
    print(f"  Repos: {len(dashboard.get('repos', []))}")
    print(f"  Cycle: {dashboard.get('evolution_cycle', 0)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("FATAL: %s", e, exc_info=True)
        sys.exit(0)
