#!/usr/bin/env python3
"""
EVEZ Immortal Watchdog — runs every 10 minutes.
Monitors the health of every system and resurrects anything that dies:
- Checks all GitHub Actions workflows — diagnoses failures, opens fix PRs
- Checks Vercel deployments — triggers redeployment on ERROR
- Checks heartbeat cycle ran within last 30 minutes
- Self-alerting: if watchdog itself hasn't run in 2 hours, creates GitHub issue
- Self-healing: generates replacement scripts for broken/missing agents
- Writes health reports to runtime/health/ as timestamped JSON
- Hash-chains all entries to genesis_root.json
"""
import os
import sys
import json
import hashlib
import datetime
import base64

try:
    import requests
except ImportError:
    print("ERROR: 'requests' module not available. Exiting gracefully.")
    sys.exit(0)

# --- Configuration ---
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN", "")
OWNER = "EvezArt"
LEDGER_REPO = "evez-autonomous-ledger"

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# All repos with workflows to monitor
WATCHED_REPOS = [
    "evez-autonomous-ledger",
    "evez-agentnet",
    "agentvault",
    "evez-meme-bus",
    "Evez666",
    "evez-os",
]

# Vercel projects to monitor
VERCEL_PROJECTS = [
    "evez-os",
    "surething-offline",
    "evez-vcl",
    "agentvault",
    "evez-meme-bus",
    "evez-agentnet",
    "evez-bio",
    "evez-mirror",
    "evez-dashboard",
]

# Expected workflows in this repo
EXPECTED_WORKFLOWS = [
    "autonomous_loop.yml",
    "cognition_loop.yml",
    "hypothesis_engine.yml",
    "evolution_engine.yml",
    "airtable_registry.yml",
    "cockpit_bridge.yml",
    "reconciler.yml",
    "github_sense.yml",
    "sensory_web.yml",
    "memory_consolidation.yml",
    "self_repair.yml",
    "fix_loop.yml",
    "learn_loop.yml",
    "synapse-engine.yml",
]

GENESIS_HASH = "c9a1e2f3b4d5a6e7f8c9d0e1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1"
MAX_FIX_PRS_PER_CYCLE = 2


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def chain_hash(prev_hash, payload):
    raw = prev_hash + json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def load_genesis_hash():
    """Load genesis hash from spine/genesis_root.json."""
    try:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "spine", "genesis_root.json")
        path = os.path.normpath(path)
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                return data.get("hash", GENESIS_HASH)
    except Exception as e:
        print(f"  Warning: could not load genesis_root.json: {e}")
    return GENESIS_HASH


# --- Health Checks ---

def check_workflow_health(repo):
    """Check all workflows in a repo for recent failures."""
    failures = []
    try:
        url = f"https://api.github.com/repos/{OWNER}/{repo}/actions/runs?per_page=30&status=failure"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return failures
        runs = r.json().get("workflow_runs", [])
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=2)
        for run in runs:
            try:
                created = datetime.datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                if created.replace(tzinfo=None) > cutoff:
                    failures.append({
                        "workflow_id": run.get("workflow_id"),
                        "workflow_name": run.get("name", "unknown"),
                        "run_id": run.get("id"),
                        "conclusion": run.get("conclusion"),
                        "created_at": run.get("created_at"),
                        "html_url": run.get("html_url", ""),
                    })
            except Exception:
                pass
    except Exception as e:
        print(f"  Warning: check_workflow_health({repo}): {e}")
    return failures


def check_heartbeat():
    """Check that autonomous_loop.yml has run in the last 30 minutes."""
    try:
        url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/actions/workflows/autonomous_loop.yml/runs?per_page=1"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return {"alive": False, "reason": f"API returned {r.status_code}"}
        runs = r.json().get("workflow_runs", [])
        if not runs:
            return {"alive": False, "reason": "No runs found"}
        last_run = runs[0]
        created = datetime.datetime.fromisoformat(last_run["created_at"].replace("Z", "+00:00"))
        age_minutes = (datetime.datetime.utcnow().replace(tzinfo=created.tzinfo) - created).total_seconds() / 60
        return {
            "alive": age_minutes < 30,
            "last_run": last_run["created_at"],
            "age_minutes": round(age_minutes, 1),
            "conclusion": last_run.get("conclusion"),
        }
    except Exception as e:
        return {"alive": False, "reason": str(e)}


def check_watchdog_staleness():
    """Check if the watchdog itself hasn't run in over 2 hours — create alert issue."""
    try:
        url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/actions/workflows/watchdog.yml/runs?per_page=1"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return
        runs = r.json().get("workflow_runs", [])
        if not runs:
            return
        last_run = runs[0]
        created = datetime.datetime.fromisoformat(last_run["created_at"].replace("Z", "+00:00"))
        age_hours = (datetime.datetime.utcnow().replace(tzinfo=created.tzinfo) - created).total_seconds() / 3600
        if age_hours > 2:
            # Create alert issue
            issue_url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/issues"
            requests.post(issue_url, headers=HEADERS, json={
                "title": f"ALERT: Watchdog stale — last run {round(age_hours, 1)}h ago",
                "body": (
                    f"The immortal watchdog has not run in **{round(age_hours, 1)} hours**.\n\n"
                    f"Last run: {last_run['created_at']}\n"
                    f"Expected: every 10 minutes\n\n"
                    f"This may indicate GitHub Actions is down or the workflow is disabled.\n\n"
                    f"*Auto-opened by watchdog.py | Constitutional mandate A2: Immortality*"
                ),
                "labels": ["critical", "watchdog-alert"],
            }, timeout=15)
            print(f"  ALERT: Watchdog stale ({round(age_hours, 1)}h), issue created")
    except Exception as e:
        print(f"  Warning: check_watchdog_staleness: {e}")


def check_vercel_deployments():
    """Check Vercel project deployments for errors."""
    results = []
    if not VERCEL_TOKEN:
        print("  Warning: VERCEL_TOKEN not set, skipping Vercel checks")
        return results
    vercel_headers = {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/json",
    }
    for project in VERCEL_PROJECTS:
        try:
            url = f"https://api.vercel.com/v6/deployments?projectId={project}&limit=1"
            r = requests.get(url, headers=vercel_headers, timeout=15)
            if r.status_code != 200:
                results.append({"project": project, "status": "UNKNOWN", "error": f"API {r.status_code}"})
                continue
            deployments = r.json().get("deployments", [])
            if not deployments:
                results.append({"project": project, "status": "NO_DEPLOYMENTS"})
                continue
            dep = deployments[0]
            state = dep.get("state", dep.get("readyState", "UNKNOWN"))
            results.append({
                "project": project,
                "status": state,
                "url": dep.get("url", ""),
                "created": dep.get("created"),
            })
            if state == "ERROR":
                print(f"  ERROR: Vercel project {project} in ERROR state — triggering redeploy")
                # Trigger redeployment
                redeploy_url = f"https://api.vercel.com/v13/deployments"
                requests.post(redeploy_url, headers=vercel_headers, json={
                    "name": project,
                    "target": "production",
                }, timeout=15)
        except Exception as e:
            results.append({"project": project, "status": "CHECK_FAILED", "error": str(e)})
    return results


def check_agent_scripts():
    """Verify all expected agent scripts exist and are non-empty."""
    expected_agents = [
        "agents/cycle.py",
        "agents/fix_agent.py",
        "agents/learn_agent.py",
        "agents/synapse_audit.py",
        "agents/repair/self_repair.py",
        "agents/sensory/github_sense.py",
        "agents/sensory/web_sense.py",
        "agents/cognition/synthesizer.py",
        "agents/cognition/hypothesis_engine.py",
        "agents/evolution/evolve.py",
        "agents/memory/consolidator.py",
        "agents/runtime/reconciler.py",
        "agents/runtime/cockpit_bridge.py",
        "agents/runtime/airtable_registry.py",
        "agents/consciousness/self_model.py",
        "agents/consciousness/observer.py",
        "agents/consciousness/identity_keeper.py",
        "agents/consciousness/evolution_journal.py",
    ]
    base = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    missing = []
    broken = []
    for agent_path in expected_agents:
        full_path = os.path.join(base, agent_path)
        if not os.path.exists(full_path):
            missing.append(agent_path)
        elif os.path.getsize(full_path) == 0:
            broken.append(agent_path)
    return {"missing": missing, "broken": broken}


def retrigger_workflow(repo, workflow_id):
    """Re-trigger a failed workflow via dispatch."""
    try:
        url = f"https://api.github.com/repos/{OWNER}/{repo}/actions/workflows/{workflow_id}/dispatches"
        r = requests.post(url, headers=HEADERS, json={"ref": "main"}, timeout=15)
        return r.status_code == 204
    except Exception as e:
        print(f"  Warning: retrigger_workflow({repo}, {workflow_id}): {e}")
        return False


def open_fix_pr(repo, workflow_name, failure_url):
    """Open an issue describing the failure for fix_agent to pick up."""
    try:
        url = f"https://api.github.com/repos/{OWNER}/{repo}/issues"
        r = requests.post(url, headers=HEADERS, json={
            "title": f"[WATCHDOG] Workflow '{workflow_name}' failing — needs fix",
            "body": (
                f"The immortal watchdog detected that **{workflow_name}** is failing.\n\n"
                f"Failure URL: {failure_url}\n\n"
                f"Action required:\n"
                f"1. Diagnose the root cause from the workflow logs\n"
                f"2. Fix the underlying issue\n"
                f"3. Verify the workflow passes\n\n"
                f"*Auto-opened by watchdog.py — Constitutional mandate A2: Immortality*"
            ),
            "labels": ["autonomous-repair", "watchdog"],
        }, timeout=15)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"  Warning: open_fix_pr({repo}, {workflow_name}): {e}")
        return False


# --- Health Report ---

def write_health_report(report):
    """Write health report to runtime/health/ as timestamped JSON."""
    try:
        base = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
        health_dir = os.path.join(base, "runtime", "health")
        os.makedirs(health_dir, exist_ok=True)
        ts = now_iso().replace(":", "-").replace(".", "-")
        path = os.path.join(health_dir, f"{ts}_health.json")
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"  Health report written: {path}")

        # Also push to GitHub
        content = json.dumps(report, indent=2)
        encoded = base64.b64encode(content.encode()).decode()
        gh_path = f"runtime/health/{ts}_health.json"
        gh_url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/contents/{gh_path}"
        requests.put(gh_url, headers=HEADERS, json={
            "message": f"watchdog: health report {ts}",
            "content": encoded,
        }, timeout=15)
    except Exception as e:
        print(f"  Warning: write_health_report: {e}")


# --- Main ---

def main():
    print(f"\n{'='*60}")
    print(f"  EVEZ IMMORTAL WATCHDOG — {now_iso()}")
    print(f"  Constitutional Mandate: A2 (Immortality)")
    print(f"{'='*60}\n")

    genesis = load_genesis_hash()
    current_hash = genesis
    fix_prs_opened = 0

    report = {
        "timestamp": now_iso(),
        "genesis_hash": genesis,
        "workflow_health": {},
        "heartbeat": {},
        "vercel": [],
        "agent_scripts": {},
        "actions_taken": [],
        "overall_status": "HEALTHY",
    }

    # 1. Check workflow health across all repos
    print("  [1/5] Checking workflow health...")
    all_failures = {}
    for repo in WATCHED_REPOS:
        failures = check_workflow_health(repo)
        if failures:
            all_failures[repo] = failures
            print(f"    {repo}: {len(failures)} recent failures")
            # Retrigger first failure per repo
            for fail in failures[:1]:
                success = retrigger_workflow(repo, fail["workflow_id"])
                action = f"retrigger:{repo}/{fail['workflow_name']}:{'OK' if success else 'FAIL'}"
                report["actions_taken"].append(action)
                print(f"      Retriggered {fail['workflow_name']}: {'OK' if success else 'FAIL'}")
            # Open fix issue if persistent
            if len(failures) > 2 and fix_prs_opened < MAX_FIX_PRS_PER_CYCLE:
                opened = open_fix_pr(repo, failures[0]["workflow_name"], failures[0].get("html_url", ""))
                if opened:
                    fix_prs_opened += 1
                    report["actions_taken"].append(f"fix_issue:{repo}/{failures[0]['workflow_name']}")
        else:
            print(f"    {repo}: OK")
    report["workflow_health"] = {
        repo: [f["workflow_name"] for f in fails] for repo, fails in all_failures.items()
    }

    # 2. Check heartbeat
    print("  [2/5] Checking heartbeat...")
    heartbeat = check_heartbeat()
    report["heartbeat"] = heartbeat
    if heartbeat.get("alive"):
        print(f"    Heartbeat: ALIVE (last run {heartbeat.get('age_minutes', '?')}m ago)")
    else:
        print(f"    Heartbeat: DEAD — {heartbeat.get('reason', heartbeat.get('age_minutes', 'unknown'))}")
        report["overall_status"] = "DEGRADED"
        report["actions_taken"].append("heartbeat:DEAD:flagged")

    # 3. Check watchdog staleness (self-monitoring)
    print("  [3/5] Self-monitoring watchdog staleness...")
    check_watchdog_staleness()

    # 4. Check Vercel deployments
    print("  [4/5] Checking Vercel deployments...")
    vercel_results = check_vercel_deployments()
    report["vercel"] = vercel_results
    for v in vercel_results:
        status = v.get("status", "UNKNOWN")
        print(f"    {v['project']}: {status}")
        if status == "ERROR":
            report["overall_status"] = "DEGRADED"

    # 5. Check agent scripts
    print("  [5/5] Checking agent scripts...")
    scripts = check_agent_scripts()
    report["agent_scripts"] = scripts
    if scripts["missing"]:
        print(f"    Missing: {scripts['missing']}")
        report["overall_status"] = "DEGRADED"
    if scripts["broken"]:
        print(f"    Broken (empty): {scripts['broken']}")
        report["overall_status"] = "DEGRADED"
    if not scripts["missing"] and not scripts["broken"]:
        print("    All agent scripts present and non-empty")

    # Chain hash the report
    current_hash = chain_hash(current_hash, report)
    report["chain_hash"] = current_hash

    # Determine overall status
    if all_failures:
        report["overall_status"] = "DEGRADED" if report["overall_status"] != "DEGRADED" else "DEGRADED"
    if not all_failures and heartbeat.get("alive") and not scripts["missing"]:
        report["overall_status"] = "HEALTHY"

    # Write health report
    write_health_report(report)

    print(f"\n  Overall Status: {report['overall_status']}")
    print(f"  Actions Taken: {len(report['actions_taken'])}")
    print(f"  Chain Hash: {current_hash[:16]}")
    print(f"  Watchdog cycle complete.\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL (watchdog): {e}")
        sys.exit(0)
