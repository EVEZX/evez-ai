#!/usr/bin/env python3
"""
EVEZ Synapse Engine Audit — 6-hour.
Audits the entire EvezArt ecosystem: GitHub repos, Vercel deployments,
GitHub Actions health. Writes structured audit reports to AUDIT_REPORTS/.
"""
import os
import json
import datetime
import hashlib
import sys

try:
    import requests
except ImportError:
    print("ERROR: requests not installed")
    sys.exit(1)

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
OWNER = "EvezArt"

GH_HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def audit_github_repos():
    """List and audit all EvezArt repos."""
    if not GH_TOKEN:
        print("  WARN: GITHUB_TOKEN not set — skipping GitHub audit")
        return {"repos": [], "error": "GITHUB_TOKEN not set"}
    try:
        r = requests.get(
            f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=pushed",
            headers=GH_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        repos = r.json()
        summary = []
        for repo in repos:
            summary.append({
                "name": repo.get("name", ""),
                "pushed_at": repo.get("pushed_at", ""),
                "open_issues": repo.get("open_issues_count", 0),
                "stars": repo.get("stargazers_count", 0),
                "size_kb": repo.get("size", 0),
                "language": repo.get("language", ""),
                "archived": repo.get("archived", False),
            })
        print(f"  GitHub: {len(summary)} repos audited")
        for s in summary[:5]:
            print(f"    {s['name']} — pushed: {s['pushed_at']}")
        return {"repos": summary, "count": len(summary)}
    except Exception as e:
        print(f"  ERROR: GitHub audit failed: {e}")
        return {"repos": [], "error": str(e)}


def audit_vercel_deployments():
    """Check recent Vercel deployments."""
    if not VERCEL_TOKEN:
        print("  WARN: VERCEL_TOKEN not set — skipping Vercel audit")
        return {"deployments": [], "error": "VERCEL_TOKEN not set"}
    try:
        r = requests.get(
            "https://api.vercel.com/v9/deployments?limit=10",
            headers={"Authorization": f"Bearer {VERCEL_TOKEN}"},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        depls = data.get("deployments", [])
        summary = []
        for dp in depls:
            summary.append({
                "name": dp.get("name", ""),
                "state": dp.get("state", ""),
                "created": dp.get("created", ""),
                "url": dp.get("url", ""),
            })
        print(f"  Vercel: {len(summary)} deployments checked")
        for s in summary[:5]:
            print(f"    {s['name']} — {s['state']}")
        return {"deployments": summary, "count": len(summary)}
    except Exception as e:
        print(f"  ERROR: Vercel audit failed: {e}")
        return {"deployments": [], "error": str(e)}


def audit_actions_health():
    """Check GitHub Actions run health across key repos."""
    if not GH_TOKEN:
        return {"runs": [], "error": "GITHUB_TOKEN not set"}
    key_repos = [
        "evez-autonomous-ledger", "evez-agentnet",
        "agentvault", "evez-meme-bus", "Evez666",
    ]
    all_runs = []
    failed = []
    for repo in key_repos:
        try:
            r = requests.get(
                f"https://api.github.com/repos/{OWNER}/{repo}/actions/runs?per_page=5",
                headers=GH_HEADERS,
                timeout=15,
            )
            if r.status_code != 200:
                continue
            for run in r.json().get("workflow_runs", []):
                entry = {
                    "repo": repo,
                    "workflow": run.get("name", ""),
                    "status": run.get("status", ""),
                    "conclusion": run.get("conclusion", ""),
                    "created_at": run.get("created_at", ""),
                }
                all_runs.append(entry)
                if entry["conclusion"] == "failure":
                    failed.append(entry)
        except Exception as e:
            print(f"  WARN: Actions check for {repo} failed: {e}")
    print(f"  Actions: {len(all_runs)} runs scanned, {len(failed)} failures")
    if failed:
        for f in failed:
            print(f"    FAIL: {f['repo']}/{f['workflow']}")
    return {"runs_total": len(all_runs), "failed": failed}


def notify_slack(report):
    """Send summary to Slack if webhook configured."""
    if not SLACK_WEBHOOK_URL:
        return
    try:
        gh = report.get("github", {})
        vercel = report.get("vercel", {})
        actions = report.get("actions", {})
        text = (
            f"*Synapse Engine Audit — {report['timestamp']}*\n"
            f"GitHub: {gh.get('count', 0)} repos | "
            f"Vercel: {vercel.get('count', 0)} deployments | "
            f"Actions: {actions.get('runs_total', 0)} runs, "
            f"{len(actions.get('failed', []))} failures"
        )
        requests.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
    except Exception as e:
        print(f"  WARN: Slack notification failed: {e}")


def write_report(report):
    """Write audit report to AUDIT_REPORTS/ directory."""
    os.makedirs("AUDIT_REPORTS", exist_ok=True)
    # Write timestamped report
    ts = now_iso().replace(":", "-").replace(".", "-")
    filename = f"AUDIT_REPORTS/audit_{ts}.json"
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Report written: {filename}")
    # Write latest pointer
    with open("AUDIT_REPORTS/last_run.txt", "w") as f:
        f.write(f"Last Synapse Engine run: {report['timestamp']}\n")
    return filename


def main():
    print(f"\n== SYNAPSE ENGINE AUDIT — {now_iso()} ==")

    report = {
        "type": "synapse_audit",
        "timestamp": now_iso(),
        "github": audit_github_repos(),
        "vercel": audit_vercel_deployments(),
        "actions": audit_actions_health(),
    }
    report["hash"] = hashlib.sha256(
        json.dumps(report, sort_keys=True).encode()
    ).hexdigest()[:16]

    write_report(report)
    notify_slack(report)
    print("  Synapse Engine audit complete.")


if __name__ == "__main__":
    main()
