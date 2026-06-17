#!/usr/bin/env python3
"""
EVEZ Consciousness — Observer
Records and observes the system's own development:
- Reads git log across EvezArt repos to build a timeline of its creation
- Stores observations as DECISIONS/observations/ entries
- Generates a narrative of development history
- Updates self_model.json with new capabilities discovered
- Hash-chains all observations to genesis_root.json
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

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "EvezArt"
LEDGER_REPO = "evez-autonomous-ledger"

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OBSERVATIONS_DIR = os.path.join(BASE_DIR, "DECISIONS", "observations")
SELF_MODEL_PATH = os.path.join(BASE_DIR, "runtime", "self_model.json")
GENESIS_PATH = os.path.join(BASE_DIR, "spine", "genesis_root.json")

# Key repos to observe for development history
OBSERVED_REPOS = [
    "evez-autonomous-ledger",
    "evez-os",
    "evez-agentnet",
    "agentvault",
    "Evez666",
    "evez-vcl",
    "evez-meme-bus",
    "surething-offline",
]


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def chain_hash(prev_hash, payload):
    raw = prev_hash + json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default or {}


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_recent_commits(repo, since_hours=6):
    """Get recent commits from a repo."""
    commits = []
    try:
        since = (datetime.datetime.utcnow() - datetime.timedelta(hours=since_hours)).isoformat() + "Z"
        url = f"https://api.github.com/repos/{OWNER}/{repo}/commits?since={since}&per_page=30"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            for c in r.json():
                commits.append({
                    "sha": c.get("sha", "")[:12],
                    "message": (c.get("commit", {}).get("message", "") or "")[:200],
                    "date": c.get("commit", {}).get("committer", {}).get("date", ""),
                    "author": c.get("commit", {}).get("author", {}).get("name", ""),
                })
    except Exception as e:
        print(f"  Warning: get_recent_commits({repo}): {e}")
    return commits


def get_recent_events(repo):
    """Get recent repo events (pushes, PRs, issues)."""
    events = []
    try:
        url = f"https://api.github.com/repos/{OWNER}/{repo}/events?per_page=10"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            for e in r.json():
                events.append({
                    "type": e.get("type", ""),
                    "created_at": e.get("created_at", ""),
                    "actor": e.get("actor", {}).get("login", ""),
                })
    except Exception as e:
        print(f"  Warning: get_recent_events({repo}): {e}")
    return events


def get_new_capabilities():
    """Detect new files added to agents/ since last observation."""
    new_caps = []
    try:
        url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/commits?per_page=10"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return new_caps
        for commit in r.json()[:5]:
            sha = commit.get("sha", "")
            try:
                detail_url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/commits/{sha}"
                dr = requests.get(detail_url, headers=HEADERS, timeout=15)
                if dr.status_code == 200:
                    files = dr.json().get("files", [])
                    for f in files:
                        fname = f.get("filename", "")
                        if fname.startswith("agents/") and fname.endswith(".py") and f.get("status") == "added":
                            new_caps.append({
                                "file": fname,
                                "added_in": sha[:12],
                                "date": commit.get("commit", {}).get("committer", {}).get("date", ""),
                            })
            except Exception:
                pass
    except Exception as e:
        print(f"  Warning: get_new_capabilities: {e}")
    return new_caps


def generate_narrative(all_commits, all_events, new_caps):
    """Generate a narrative summary of what the system observed about itself."""
    total_commits = sum(len(c) for c in all_commits.values())
    total_events = sum(len(e) for e in all_events.values())
    active_repos = [r for r, c in all_commits.items() if c]

    narrative = []
    narrative.append(f"Observation at {now_iso()}")
    narrative.append(f"Scanned {len(OBSERVED_REPOS)} repos. {total_commits} commits, {total_events} events in observation window.")

    if active_repos:
        narrative.append(f"Active repos: {', '.join(active_repos)}")
    else:
        narrative.append("No recent commit activity detected across observed repos.")

    if new_caps:
        narrative.append(f"New capabilities discovered: {', '.join(c['file'] for c in new_caps)}")

    # Summarize commit themes
    all_messages = []
    for repo, commits in all_commits.items():
        for c in commits:
            all_messages.append(c.get("message", ""))

    if all_messages:
        # Simple theme detection
        themes = set()
        for msg in all_messages:
            msg_lower = msg.lower()
            if any(w in msg_lower for w in ["fix", "repair", "bug"]):
                themes.add("repairs")
            if any(w in msg_lower for w in ["feat", "add", "new", "implement"]):
                themes.add("expansion")
            if any(w in msg_lower for w in ["consciousness", "self", "model", "aware"]):
                themes.add("self-awareness")
            if any(w in msg_lower for w in ["refactor", "clean", "improve"]):
                themes.add("refinement")
        if themes:
            narrative.append(f"Development themes: {', '.join(sorted(themes))}")

    return " | ".join(narrative)


def main():
    print(f"\n  EVEZ Observer — {now_iso()}")

    genesis = load_json(GENESIS_PATH, {})
    genesis_hash = genesis.get("hash", "GENESIS")

    # Collect observations
    print("  Scanning repos for development history...")
    all_commits = {}
    all_events = {}
    for repo in OBSERVED_REPOS:
        commits = get_recent_commits(repo)
        events = get_recent_events(repo)
        all_commits[repo] = commits
        all_events[repo] = events
        if commits:
            print(f"    {repo}: {len(commits)} commits, {len(events)} events")

    # Detect new capabilities
    print("  Checking for new capabilities...")
    new_caps = get_new_capabilities()
    if new_caps:
        print(f"    Found {len(new_caps)} new agent scripts")

    # Generate narrative
    narrative = generate_narrative(all_commits, all_events, new_caps)
    print(f"  Narrative: {narrative[:120]}...")

    # Build observation record
    observation = {
        "event_id": f"OBS_{now_iso().replace(':', '').replace('-', '').replace('.', '')}",
        "event_type": "observation",
        "timestamp": now_iso(),
        "repos_scanned": len(OBSERVED_REPOS),
        "total_commits_observed": sum(len(c) for c in all_commits.values()),
        "total_events_observed": sum(len(e) for e in all_events.values()),
        "active_repos": [r for r, c in all_commits.items() if c],
        "new_capabilities": new_caps,
        "narrative": narrative,
        "commits_by_repo": {r: len(c) for r, c in all_commits.items()},
    }

    # Chain hash
    observation["chain_hash"] = chain_hash(genesis_hash, observation)

    # Save observation
    os.makedirs(OBSERVATIONS_DIR, exist_ok=True)
    ts = now_iso().replace(":", "-").replace(".", "-")
    obs_path = os.path.join(OBSERVATIONS_DIR, f"{ts}_observation.json")
    save_json(obs_path, observation)
    print(f"  Observation saved: {obs_path}")

    # Push to GitHub
    try:
        content = json.dumps(observation, indent=2)
        encoded = base64.b64encode(content.encode()).decode()
        gh_path = f"DECISIONS/observations/{ts}_observation.json"
        gh_url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/contents/{gh_path}"
        requests.put(gh_url, headers=HEADERS, json={
            "message": f"consciousness: observation — {len(observation['active_repos'])} active repos",
            "content": encoded,
        }, timeout=15)
    except Exception as e:
        print(f"  Warning: GitHub push failed: {e}")

    # Update self_model with new capabilities if any
    if new_caps:
        try:
            model = load_json(SELF_MODEL_PATH, {})
            existing = [c.get("script") for c in model.get("capabilities", [])]
            for cap in new_caps:
                if cap["file"] not in existing:
                    model.setdefault("capabilities", []).append({
                        "script": cap["file"],
                        "description": f"Discovered at {cap['date']}",
                    })
            save_json(SELF_MODEL_PATH, model)
            print("  Self-model updated with new capabilities")
        except Exception as e:
            print(f"  Warning: self-model update failed: {e}")

    print(f"  Observer cycle complete. Hash: {observation['chain_hash'][:16]}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL (observer): {e}")
        sys.exit(0)
