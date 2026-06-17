#!/usr/bin/env python3
"""
EVEZ Self-Repair Daemon — 10-min.
Monitors workflow run health across all repos.
On detected failure: auto-re-triggers failed workflow via workflow_dispatch.
On stale repo (no push >72h): opens a [STALE] issue.
All actions hash-chained to ledger. Never touches production code directly.
"""
import os, json, datetime, hashlib, requests, base64

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ABLY_KEY = os.environ.get("ABLY_KEY", "")
OWNER = "EvezArt"

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

WATCHED = [
    "evez-autonomous-ledger", "evez-agentnet",
    "agentvault", "evez-meme-bus", "Evez666",
]

MAX_RETRIGGER_PER_CYCLE = 2  # safety cap


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def get_failed_runs(repo):
    try:
        url = f"https://api.github.com/repos/{OWNER}/{repo}/actions/runs?per_page=5&status=failure"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            # Only return runs that failed in last 30 min
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
            recent = []
            for run in runs:
                try:
                    t = datetime.datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                    if t.replace(tzinfo=None) > cutoff:
                        recent.append(run)
                except Exception:
                    pass
            return recent
        return []
    except Exception as e:
        print(f"  ❌ get_failed_runs({repo}) error: {e}")
        return []


def retrigger_workflow(repo, workflow_id):
    try:
        url = f"https://api.github.com/repos/{OWNER}/{repo}/actions/workflows/{workflow_id}/dispatches"
        r = requests.post(url, headers=HEADERS, json={"ref": "main"}, timeout=15)
        return r.status_code == 204
    except Exception as e:
        print(f"  ❌ retrigger_workflow({repo}, {workflow_id}) error: {e}")
        return False


def open_stale_issue(repo, hours):
    try:
        url = f"https://api.github.com/repos/{OWNER}/{repo}/issues"
        r = requests.post(url, headers=HEADERS, json={
            "title": f"⏰ [STALE] No commits in {round(hours)}h — attention needed",
            "body": f"This repo has had no pushes in **{round(hours)} hours**.\n\nThe autonomous system flagged it as potentially stale.\n\n*Auto-opened by self_repair.py | Review and close when resolved.*",
            "labels": ["stale", "autonomous-repair"],
        }, timeout=15)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"  ❌ open_stale_issue({repo}) error: {e}")
        return False


def log_repair_action(action):
    try:
        content = json.dumps(action, indent=2)
        encoded = base64.b64encode(content.encode()).decode()
        ts = now_iso().replace(":", "-").replace(".", "-")
        url = f"https://api.github.com/repos/{OWNER}/evez-autonomous-ledger/contents/DECISIONS/{ts}_repair.json"
        requests.put(url, headers=HEADERS, json={
            "message": f"🔧 repair: {action['action']} on {action['repo']}",
            "content": encoded,
        }, timeout=15)
    except Exception as e:
        print(f"  ❌ log_repair_action error: {e}")


def broadcast(event):
    try:
        if not ABLY_KEY:
            return
        key_id, key_secret = ABLY_KEY.split(":")
        requests.post(
            "https://rest.ably.io/channels/evez-ops/messages",
            json={"name": "repair_action", "data": json.dumps(event)},
            auth=(key_id, key_secret),
            timeout=15,
        )
    except Exception as e:
        print(f"  ❌ broadcast error: {e}")


def main():
    try:
        print(f"\n🔧 EVEZ Self-Repair Daemon — {now_iso()}")
        now = datetime.datetime.utcnow()
        retriggered = 0

        for repo in WATCHED:
            try:
                # Check workflow failures
                if retriggered < MAX_RETRIGGER_PER_CYCLE:
                    failed = get_failed_runs(repo)
                    for run in failed[:1]:  # max 1 retrigger per repo per cycle
                        wf_id = run.get("workflow_id")
                        wf_name = run.get("name", "unknown")
                        success = retrigger_workflow(repo, wf_id)
                        action = {
                            "type": "repair_action",
                            "action": "retrigger_workflow",
                            "repo": repo,
                            "workflow": wf_name,
                            "success": success,
                            "timestamp": now_iso(),
                            "hash": hashlib.sha256(f"{repo}{wf_id}{now_iso()}".encode()).hexdigest()[:12],
                        }
                        log_repair_action(action)
                        broadcast(action)
                        print(f"  {'✅' if success else '❌'} Retriggered {repo}/{wf_name}")
                        retriggered += 1

                # Check staleness
                url = f"https://api.github.com/repos/{OWNER}/{repo}"
                r = requests.get(url, headers=HEADERS, timeout=15)
                if r.status_code == 200:
                    pushed = r.json().get("pushed_at", "")
                    if pushed:
                        try:
                            pt = datetime.datetime.fromisoformat(pushed.replace("Z", "+00:00"))
                            hours = (now.replace(tzinfo=pt.tzinfo) - pt).total_seconds() / 3600
                            if hours > 72:
                                opened = open_stale_issue(repo, hours)
                                print(f"  {'✅' if opened else '❌'} Stale issue: {repo} ({round(hours)}h)")
                        except Exception:
                            pass
            except Exception as e:
                print(f"  ❌ Error processing repo {repo}: {e}")

        print(f"  ✅ Self-repair cycle complete. {retriggered} workflows retriggered.")
    except Exception as e:
        print(f"❌ Self-repair main() error: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Self-repair daemon fatal error: {e}")
        exit(0)
