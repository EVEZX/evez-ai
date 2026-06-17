#!/usr/bin/env python3
"""
EVEZ GitHub Sensory Agent — 20-min.
Scans: own repo ecosystem health, trending repos in AI/crypto/quantum,
recent commits across EvezArt, open PR status, Actions run health.
Writes structured perception to ledger.
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

WATCHED_REPOS = [
    "evez-autonomous-ledger", "evez-os", "evez-agentnet",
    "agentvault", "evez-meme-bus", "Evez666",
    "surething-offline", "evez-os-v2", "polymarket-speedrun",
    "evez-vcl", "evez-sim", "moltbot-live",
]

TRENDING_QUERIES = [
    "topic:autonomous-agents stars:>100",
    "topic:llm-agent stars:>50",
    "topic:self-healing stars:>20",
    "quantum computing python stars:>200",
]


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def scan_own_repos():
    results = []
    for repo in WATCHED_REPOS:
        try:
            url = f"https://api.github.com/repos/{OWNER}/{repo}"
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                d = r.json()
                results.append({
                    "repo": repo,
                    "open_issues": d.get("open_issues_count", 0),
                    "pushed_at": d.get("pushed_at", ""),
                    "stars": d.get("stargazers_count", 0),
                    "size_kb": d.get("size", 0),
                })
        except Exception as e:
            print(f"  [github_sense] scan error for {repo}: {e}")
    return results


def scan_trending(query):
    try:
        url = f"https://api.github.com/search/repositories?q={requests.utils.quote(query)}&sort=stars&order=desc&per_page=3"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            items = r.json().get("items", [])
            return [{"name": i["full_name"], "stars": i["stargazers_count"],
                     "desc": (i.get("description") or "")[:100]} for i in items]
        return []
    except Exception as e:
        print(f"  [github_sense] scan_trending error: {e}")
        return []


def get_recent_workflow_runs():
    runs = []
    for repo in ["evez-autonomous-ledger", "evez-agentnet", "agentvault", "evez-meme-bus", "Evez666"]:
        try:
            url = f"https://api.github.com/repos/{OWNER}/{repo}/actions/runs?per_page=3"
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                for run in r.json().get("workflow_runs", []):
                    runs.append({
                        "repo": repo,
                        "workflow": run.get("name", ""),
                        "status": run.get("status", ""),
                        "conclusion": run.get("conclusion", ""),
                        "created_at": run.get("created_at", ""),
                    })
        except Exception as e:
            print(f"  [github_sense] workflow runs error for {repo}: {e}")
    return runs


def write_perception(perception):
    try:
        content = json.dumps(perception, indent=2)
        encoded = base64.b64encode(content.encode()).decode()
        ts = now_iso().replace(":", "-").replace(".", "-")
        fname = f"{ts}_perception_github.json"
        url = f"https://api.github.com/repos/{OWNER}/evez-autonomous-ledger/contents/DECISIONS/{fname}"
        requests.put(url, headers=HEADERS, json={
            "message": f"👁 gh-sense: {perception['total_issues']} issues, {perception['runs_scanned']} runs @ {perception['timestamp']}",
            "content": encoded,
        }, timeout=15)
    except Exception as e:
        print(f"  [github_sense] write_perception error: {e}")


def broadcast(payload):
    try:
        if not ABLY_KEY:
            return
        key_id, key_secret = ABLY_KEY.split(":")
        requests.post(
            "https://rest.ably.io/channels/evez-ops/messages",
            json={"name": "github_perception", "data": json.dumps(payload)},
            auth=(key_id, key_secret),
            timeout=15,
        )
    except Exception as e:
        print(f"  [github_sense] broadcast error: {e}")


def main():
    try:
        print(f"\n👁 EVEZ GitHub Sensory Agent — {now_iso()}")

        repos = scan_own_repos()
        total_issues = sum(r["open_issues"] for r in repos)
        print(f"  Own repos: {len(repos)} scanned, {total_issues} open issues")

        trending = []
        for q in TRENDING_QUERIES:
            t = scan_trending(q)
            trending.extend(t)
        print(f"  Trending: {len(trending)} repos discovered")

        runs = get_recent_workflow_runs()
        failed = [r for r in runs if r.get("conclusion") == "failure"]
        print(f"  Workflow runs: {len(runs)} scanned, {len(failed)} failures")

        if failed:
            print("  ⚠️  Failed workflows:")
            for f in failed:
                print(f"    {f['repo']}/{f['workflow']}")

        perception = {
            "type": "github_perception",
            "source": "sensory/github_sense",
            "timestamp": now_iso(),
            "repos_scanned": len(repos),
            "total_issues": total_issues,
            "runs_scanned": len(runs),
            "failed_runs": failed,
            "trending_discoveries": trending[:6],
            "repo_health": repos,
            "hash": hashlib.sha256(
                f"{total_issues}{len(failed)}".encode()
            ).hexdigest()[:16],
        }

        write_perception(perception)
        broadcast({"timestamp": perception["timestamp"],
                   "total_issues": total_issues,
                   "failed_runs": len(failed),
                   "trending_count": len(trending)})
        print(f"  ✅ GitHub perception written to ledger.")
    except Exception as e:
        print(f"  [github_sense] main error: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"github_sense fatal: {e}")
        exit(0)
