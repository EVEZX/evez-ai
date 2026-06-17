#!/usr/bin/env python3
"""
EVEZ Learn Agent — nightly. Reads closed issues + merged PRs as lessons.
Extracts (context, decision, outcome) triplets and writes to ledger/DECISIONS.
Runs at 02:00 UTC via learn_loop.yml.
"""
import os, json, base64, datetime, hashlib, requests

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "EvezArt"

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

REPOS = ["evez-autonomous-ledger", "evez-os", "evez-agentnet",
         "agentvault", "evez-meme-bus", "Evez666"]


def get_recently_closed(repo: str, days: int = 1) -> list:
    try:
        since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat() + "Z"
        url = f"https://api.github.com/repos/{OWNER}/{repo}/issues?state=closed&since={since}&per_page=20"
        r = requests.get(url, headers=HEADERS, timeout=15)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        print(f"  ⚠ get_recently_closed failed for {repo}: {e}")
        return []


def extract_lesson(issue: dict, repo: str) -> dict:
    return {
        "type": "lesson",
        "repo": repo,
        "issue_number": issue["number"],
        "issue_title": issue["title"],
        "root_cause": "inferred_from_closure",
        "fix_pattern": issue.get("state_reason", "completed"),
        "confidence_delta": 0.01,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "hash": hashlib.sha256(
            (repo + str(issue["number"]) + issue["title"]).encode()
        ).hexdigest()[:16],
    }


def write_lesson(lesson: dict):
    import base64
    content = json.dumps(lesson, indent=2)
    encoded = base64.b64encode(content.encode()).decode()
    ts = lesson["timestamp"].replace(":", "-").replace(".", "-")
    filename = f"{ts}_lesson_{lesson['repo']}_{lesson['issue_number']}.json"
    url = f"https://api.github.com/repos/{OWNER}/evez-autonomous-ledger/contents/DECISIONS/{filename}"
    try:
        requests.put(url, headers=HEADERS, json={
            "message": f"📚 lesson: {lesson['repo']}#{lesson['issue_number']}",
            "content": encoded,
        }, timeout=15)
    except Exception as e:
        print(f"  ⚠ write_lesson failed for {lesson['repo']}#{lesson['issue_number']}: {e}")


def main():
    try:
        print(f"\n📚 EVEZ Learn Agent — {datetime.datetime.utcnow().isoformat()}Z")
        total = 0
        for repo in REPOS:
            try:
                closed = get_recently_closed(repo)
                for issue in closed:
                    lesson = extract_lesson(issue, repo)
                    write_lesson(lesson)
                    print(f"  → Lesson from {repo}#{issue['number']}: {issue['title'][:50]}")
                    total += 1
            except Exception as e:
                print(f"  ⚠ Repo {repo} failed, skipping: {e}")
                continue
        print(f"  ✅ {total} lessons written to ledger.")
    except Exception as e:
        print(f"  ❌ main() failed: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ learn_agent crashed: {e}")
        exit(0)
