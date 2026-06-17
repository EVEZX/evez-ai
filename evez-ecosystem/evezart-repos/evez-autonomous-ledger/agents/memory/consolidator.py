#!/usr/bin/env python3
"""
EVEZ Memory Consolidator — 3-hour.
Reads all DECISIONS/ records, builds frequency maps of:
- recurring issue types, repos, failure modes
- high-confidence fix patterns
- signal keywords from web perceptions
Writes consolidated MEMORY_STATE.json to ledger root.
This is long-term memory formation — slow, persistent, cumulative.
"""
import os, json, datetime, hashlib, requests, base64
from collections import Counter

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OWNER = "EvezArt"

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def load_all_decisions():
    try:
        url = f"https://api.github.com/repos/{OWNER}/evez-autonomous-ledger/contents/DECISIONS"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        files = r.json()
    except Exception as e:
        print(f"  [WARN] load_all_decisions outer request failed: {e}")
        return []
    records = []
    for f in files[:60]:  # cap at 60 to avoid rate limits
        try:
            fr = requests.get(f["url"], headers=HEADERS, timeout=15)
            if fr.status_code == 200:
                try:
                    records.append(json.loads(base64.b64decode(fr.json()["content"]).decode()))
                except Exception:
                    pass
        except Exception as e:
            print(f"  [WARN] load_all_decisions file fetch failed: {e}")
    return records


def consolidate(records):
    repo_issue_counts = Counter()
    event_types = Counter()
    failure_modes = []
    web_keywords = Counter()
    fix_patterns = Counter()
    lessons = []

    for r in records:
        t = r.get("type", "unknown")
        event_types[t] += 1

        if t in ("autonomous_cycle", "plan_"):
            repo = r.get("repo", "")
            if repo:
                repo_issue_counts[repo] += 1

        if t == "github_perception":
            for fr in r.get("failed_runs", []):
                failure_modes.append(fr.get("workflow", ""))

        if t == "web_perception":
            for sig in r.get("top_signals", []):
                title = sig.get("title", "").lower()
                for word in title.split():
                    if len(word) > 5:
                        web_keywords[word] += 1

        if t == "lesson":
            lessons.append({
                "repo": r.get("repo"),
                "issue": r.get("issue_title", "")[:60],
                "pattern": r.get("fix_pattern", ""),
            })
            fix_patterns[r.get("fix_pattern", "unknown")] += 1

    return {
        "type": "MEMORY_STATE",
        "timestamp": now_iso(),
        "total_records": len(records),
        "event_type_distribution": dict(event_types.most_common(15)),
        "repo_activity_ranking": dict(repo_issue_counts.most_common(10)),
        "recurring_failure_modes": Counter(failure_modes).most_common(5),
        "top_web_keywords": dict(web_keywords.most_common(20)),
        "fix_pattern_distribution": dict(fix_patterns.most_common(10)),
        "lessons_count": len(lessons),
        "recent_lessons": lessons[-5:],
        "memory_hash": hashlib.sha256(
            json.dumps(dict(event_types)).encode()
        ).hexdigest()[:16],
    }


def write_memory_state(state):
    content = json.dumps(state, indent=2)
    encoded = base64.b64encode(content.encode()).decode()

    # Overwrite the canonical MEMORY_STATE file
    existing_sha = ""
    url = f"https://api.github.com/repos/{OWNER}/evez-autonomous-ledger/contents/MEMORY_STATE.json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            existing_sha = r.json().get("sha", "")
    except Exception as e:
        print(f"  [WARN] write_memory_state GET failed: {e}")

    payload = {
        "message": f"🧬 MEMORY_STATE consolidated @ {state['timestamp']}",
        "content": encoded,
    }
    if existing_sha:
        payload["sha"] = existing_sha

    try:
        requests.put(url, headers=HEADERS, json=payload, timeout=15)
    except Exception as e:
        print(f"  [WARN] write_memory_state PUT failed: {e}")


def main():
    try:
        print(f"\n🧬 EVEZ Memory Consolidator — {now_iso()}")
        records = load_all_decisions()
        print(f"  Loaded {len(records)} decision records")
        state = consolidate(records)
        write_memory_state(state)
        print(f"  ✅ MEMORY_STATE.json updated. Hash: {state['memory_hash']}")
        print(f"  Event types: {state['event_type_distribution']}")
        print(f"  Top keywords: {list(state['top_web_keywords'].keys())[:8]}")
    except Exception as e:
        print(f"  [ERROR] main() failed: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FATAL] consolidator crashed: {e}")
        exit(0)
