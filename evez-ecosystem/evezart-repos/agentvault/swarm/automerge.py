"""
swarm/automerge.py — agentvault
CLI swarm auto-merger: merges all open, mergeable PRs from EvezArt
across specified repos using the GitHub API.
Resolves: agentvault#1

Usage:
  python -m swarm.automerge                  # dry-run
  python -m swarm.automerge --merge          # actually merge
  python -m swarm.automerge --merge --repo evez-os  # single repo

Env:
  GITHUB_TOKEN  (required)
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone

TOKEN = os.environ.get("GITHUB_TOKEN", "")
ORG   = "EvezArt"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

DEFAULT_REPOS = [
    "agentvault", "evez-os", "evez-agentnet", "evez-meme-bus",
    "polymarket-speedrun", "moltbot-live", "maes", "evez-sim",
    "metarom", "evez-vcl", "surething-offline",
]


def gh(method: str, path: str, body: dict = None):
    url  = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "msg": e.read().decode()}


def get_open_prs(repo: str) -> list:
    data = gh("GET", f"/repos/{ORG}/{repo}/pulls?state=open&per_page=50")
    if isinstance(data, list):
        return data
    return []


def is_mergeable(pr: dict) -> bool:
    """Re-fetch single PR for mergeable status (lazy-computed by GitHub)."""
    detail = gh("GET", f"/repos/{ORG}/{pr['base']['repo']['name']}/pulls/{pr['number']}")
    return detail.get("mergeable") is True and detail.get("draft") is False


def merge_pr(repo: str, number: int, title: str) -> dict:
    return gh("PUT", f"/repos/{ORG}/{repo}/pulls/{number}/merge", {
        "merge_method": "squash",
        "commit_title": title,
        "commit_message": "",
    })


def run(repos: list, do_merge: bool = False):
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[swarm] {'MERGE' if do_merge else 'DRY-RUN'} @ {ts}")
    if not TOKEN:
        print("[swarm] ERROR: GITHUB_TOKEN not set.")
        sys.exit(1)

    total_merged = 0
    for repo in repos:
        prs = get_open_prs(repo)
        for pr in prs:
            num   = pr["number"]
            title = pr["title"]
            author = pr["user"]["login"]
            if author != ORG:
                print(f"  [{repo}#{num}] SKIP (author={author})")
                continue
            if pr.get("draft"):
                print(f"  [{repo}#{num}] SKIP (draft)")
                continue
            ok = is_mergeable(pr)
            if not ok:
                print(f"  [{repo}#{num}] NOT MERGEABLE: {title}")
                continue
            if do_merge:
                result = merge_pr(repo, num, title)
                if result.get("merged"):
                    print(f"  [{repo}#{num}] MERGED: {title}")
                    total_merged += 1
                else:
                    print(f"  [{repo}#{num}] MERGE FAILED: {result}")
            else:
                print(f"  [{repo}#{num}] WOULD MERGE: {title}")
                total_merged += 1

    print(f"[swarm] Done. {'Merged' if do_merge else 'Would merge'}: {total_merged}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--merge", action="store_true", help="Actually merge (default: dry-run)")
    parser.add_argument("--repo",  type=str, default=None, help="Single repo to target")
    args = parser.parse_args()
    repos = [args.repo] if args.repo else DEFAULT_REPOS
    run(repos, do_merge=args.merge)
