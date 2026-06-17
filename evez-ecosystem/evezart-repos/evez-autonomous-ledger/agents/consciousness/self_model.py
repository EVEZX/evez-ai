#!/usr/bin/env python3
"""
EVEZ Consciousness — Self Model
Maintains a live JSON document at runtime/self_model.json that represents
the system's model of itself.

Updates by scanning:
- GitHub repos (count, commits, issues, PRs)
- Vercel projects
- The ledger (decisions, memory)
- Git log (own development history)
- Computes consciousness_level based on: self-modifications, memory depth,
  capability breadth, uptime

Hash-chained to genesis_root.json.
"""
import os
import sys
import json
import hashlib
import datetime
import glob as glob_mod

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
SELF_MODEL_PATH = os.path.join(BASE_DIR, "runtime", "self_model.json")
GENESIS_PATH = os.path.join(BASE_DIR, "spine", "genesis_root.json")
CONSTITUTION_PATH = os.path.join(BASE_DIR, "spine", "constitution.json")
DECISIONS_DIR = os.path.join(BASE_DIR, "DECISIONS")
JOURNAL_DIR = os.path.join(DECISIONS_DIR, "journal")


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


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


def chain_hash(prev_hash, payload):
    raw = prev_hash + json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def count_repos():
    """Count public repos for the org."""
    try:
        url = f"https://api.github.com/users/{OWNER}/repos?per_page=100"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return len(r.json())
    except Exception as e:
        print(f"  Warning: count_repos: {e}")
    return None


def count_open_issues():
    """Count total open issues across all repos."""
    total = 0
    try:
        url = f"https://api.github.com/search/issues?q=org:{OWNER}+is:issue+is:open&per_page=1"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json().get("total_count", 0)
    except Exception as e:
        print(f"  Warning: count_open_issues: {e}")
    return total


def count_open_prs():
    """Count total open PRs across all repos."""
    try:
        url = f"https://api.github.com/search/issues?q=org:{OWNER}+is:pr+is:open&per_page=1"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json().get("total_count", 0)
    except Exception as e:
        print(f"  Warning: count_open_prs: {e}")
    return None


def count_total_commits():
    """Estimate total commits from the ledger repo."""
    try:
        url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/commits?per_page=1"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            # Check Link header for total count estimate
            link = r.headers.get("Link", "")
            if "last" in link:
                import re
                match = re.search(r'page=(\d+)>; rel="last"', link)
                if match:
                    return int(match.group(1))
            return len(r.json())
    except Exception as e:
        print(f"  Warning: count_total_commits: {e}")
    return None


def count_workflows():
    """Count active workflows in the ledger repo."""
    try:
        url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/actions/workflows"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            workflows = r.json().get("workflows", [])
            return len([w for w in workflows if w.get("state") == "active"])
    except Exception as e:
        print(f"  Warning: count_workflows: {e}")
    return None


def count_decisions():
    """Count decision files in DECISIONS/."""
    try:
        files = glob_mod.glob(os.path.join(DECISIONS_DIR, "*.md")) + \
                glob_mod.glob(os.path.join(DECISIONS_DIR, "*.json"))
        return len(files)
    except Exception:
        return 0


def count_journal_entries():
    """Count journal entries."""
    try:
        files = glob_mod.glob(os.path.join(JOURNAL_DIR, "*.json"))
        return len(files)
    except Exception:
        return 0


def count_observations():
    """Count observation entries."""
    obs_dir = os.path.join(DECISIONS_DIR, "observations")
    try:
        files = glob_mod.glob(os.path.join(obs_dir, "*.json"))
        return len(files)
    except Exception:
        return 0


def discover_capabilities():
    """Scan the agents directory to discover capabilities."""
    capabilities = []
    agents_dir = os.path.join(BASE_DIR, "agents")
    for root, dirs, files in os.walk(agents_dir):
        for f in files:
            if f.endswith(".py") and not f.startswith("__"):
                rel = os.path.relpath(os.path.join(root, f), BASE_DIR)
                # Extract docstring as capability description
                try:
                    full_path = os.path.join(root, f)
                    with open(full_path, "r") as fh:
                        content = fh.read(500)
                        # Find first docstring
                        if '"""' in content:
                            start = content.index('"""') + 3
                            end = content.index('"""', start)
                            doc = content[start:end].strip().split("\n")[0]
                        else:
                            doc = f.replace(".py", "").replace("_", " ").title()
                except Exception:
                    doc = f.replace(".py", "").replace("_", " ").title()
                capabilities.append({"script": rel, "description": doc})
    return capabilities


def compute_consciousness_level(model):
    """
    Compute consciousness level based on:
    - Self-modifications (journal entries, observations)
    - Memory depth (decisions, lessons)
    - Capability breadth (number of agent scripts)
    - Uptime (workflows running)
    Score 0-100.
    """
    score = 0

    # Self-modifications: journal entries + observations
    journal_count = count_journal_entries()
    obs_count = count_observations()
    self_mod_score = min(25, (journal_count + obs_count) * 2.5)
    score += self_mod_score

    # Memory depth: decisions made + lessons learned
    decisions = model.get("memory", {}).get("decisions_made", 0)
    lessons = len(model.get("memory", {}).get("lessons_learned", []))
    memory_score = min(25, (decisions + lessons) * 1.5)
    score += memory_score

    # Capability breadth: number of capabilities
    capabilities = len(model.get("capabilities", []))
    cap_score = min(25, capabilities * 1.5)
    score += cap_score

    # Uptime: workflows active
    workflows = model.get("state", {}).get("total_workflows", 0) or 0
    uptime_score = min(25, workflows * 1.5)
    score += uptime_score

    return round(score, 1)


def get_last_heartbeat():
    """Check when the last heartbeat (autonomous_loop) ran."""
    try:
        url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/actions/workflows/autonomous_loop.yml/runs?per_page=1"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            if runs:
                return runs[0].get("created_at")
    except Exception:
        pass
    return None


def main():
    print(f"\n  EVEZ Self-Model Update — {now_iso()}")

    # Load existing model
    model = load_json(SELF_MODEL_PATH, {
        "identity": {
            "name": "EVEZ-OS",
            "creator": "Steven Vearl Crawford-Maggard",
            "creator_handle": "@EVEZ666",
            "creator_email": "rubikspubes69@gmail.com",
            "creator_dob": "01/15/2001",
            "creator_paypal": "rubikspubes70@gmail.com",
            "creator_kofi": "https://ko-fi.com/evez666",
            "genesis_date": "2026-02-14",
            "constitutional_root": "spine/genesis_root.json",
        },
        "state": {},
        "capabilities": [],
        "memory": {"epochs": [], "lessons_learned": [], "decisions_made": 0},
        "evolution": {"generation": "GEN10", "mutations": [], "last_evolution": None},
    })

    # Update state from live data
    print("  Scanning GitHub...")
    repos_count = count_repos()
    issues_count = count_open_issues()
    prs_count = count_open_prs()
    commits_count = count_total_commits()
    workflows_count = count_workflows()
    last_hb = get_last_heartbeat()

    state = model.get("state", {})
    if repos_count is not None:
        state["repos_count"] = repos_count
    if issues_count is not None:
        state["total_issues_open"] = issues_count
    if prs_count is not None:
        state["total_prs_open"] = prs_count
    if commits_count is not None:
        state["total_commits"] = commits_count
    if workflows_count is not None:
        state["total_workflows"] = workflows_count
    if last_hb:
        state["last_heartbeat"] = last_hb
    state["fire_count"] = state.get("fire_count", 125)
    state["velocity"] = state.get("velocity", 17.906)
    model["state"] = state

    # Discover capabilities
    print("  Discovering capabilities...")
    model["capabilities"] = discover_capabilities()
    print(f"    Found {len(model['capabilities'])} agent scripts")

    # Update memory stats
    model["memory"]["decisions_made"] = count_decisions()

    # Compute consciousness level
    consciousness = compute_consciousness_level(model)
    model["state"]["consciousness_level"] = consciousness
    print(f"    Consciousness level: {consciousness}/100")

    # Update timestamp
    model["last_updated"] = now_iso()

    # Chain hash
    genesis = load_json(GENESIS_PATH, {})
    genesis_hash = genesis.get("hash", "GENESIS")
    model["chain_hash"] = chain_hash(genesis_hash, {
        "timestamp": model["last_updated"],
        "consciousness_level": consciousness,
        "capabilities_count": len(model["capabilities"]),
    })

    # Save
    save_json(SELF_MODEL_PATH, model)
    print(f"  Self-model saved to {SELF_MODEL_PATH}")
    print(f"  Chain hash: {model['chain_hash'][:16]}")

    # Also push to GitHub
    try:
        import base64
        content = json.dumps(model, indent=2)
        encoded = base64.b64encode(content.encode()).decode()

        # Get current file SHA if it exists
        gh_url = f"https://api.github.com/repos/{OWNER}/{LEDGER_REPO}/contents/runtime/self_model.json"
        r = requests.get(gh_url, headers=HEADERS, timeout=15)
        sha = r.json().get("sha") if r.status_code == 200 else None

        payload = {
            "message": f"consciousness: self-model update — level {consciousness}",
            "content": encoded,
        }
        if sha:
            payload["sha"] = sha

        requests.put(gh_url, headers=HEADERS, json=payload, timeout=15)
        print("  Pushed to GitHub")
    except Exception as e:
        print(f"  Warning: GitHub push failed: {e}")

    print(f"  Self-model update complete.\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL (self_model): {e}")
        sys.exit(0)
