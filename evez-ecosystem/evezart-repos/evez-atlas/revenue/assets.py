"""Asset Tracker — Tracks all digital assets owned by @EVEZ666.

Inventories GitHub repos, Vercel deployments, domains, content library,
and intellectual property.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

REVENUE_DIR = Path(__file__).parent
ASSETS_JSON = REVENUE_DIR / "assets.json"
GITHUB_USER = "EvezArt"

# Known Vercel deployments (public knowledge from profile)
VERCEL_PROJECTS = [
    {"name": "evez666-site", "url": "https://evez666.vercel.app", "type": "portfolio"},
    {"name": "atlas-dashboard", "url": "https://atlas-dash.vercel.app", "type": "dashboard"},
    {"name": "moltbook", "url": "https://moltbook.vercel.app", "type": "application"},
    {"name": "evez-game", "url": "https://evez-game.vercel.app", "type": "game"},
    {"name": "divine-gospel", "url": "https://divine-gospel.vercel.app", "type": "content"},
    {"name": "spectral-ui", "url": "https://spectral-ui.vercel.app", "type": "tool"},
    {"name": "profit-circuit", "url": "https://profit-circuit.vercel.app", "type": "finance"},
    {"name": "synaptic-kernel", "url": "https://synaptic-kernel.vercel.app", "type": "tool"},
    {"name": "evez-portfolio", "url": "https://evez-portfolio.vercel.app", "type": "portfolio"},
]

# Intellectual property categories
IP_CATEGORIES = [
    {
        "name": "Atlas Synaptic Recursion Kernel",
        "type": "architecture",
        "description": "Novel neural-inspired recursive processing architecture",
    },
    {
        "name": "Spectral Decomposition Engine",
        "type": "algorithm",
        "description": "Frequency-domain analysis for code and system optimization",
    },
    {
        "name": "Ring Protocol System",
        "type": "protocol",
        "description": "Distributed communication protocol for autonomous agents",
    },
    {
        "name": "Autonomous Revenue Engine",
        "type": "system",
        "description": "Self-operating revenue generation and optimization system",
    },
    {
        "name": "Fire Event Router",
        "type": "algorithm",
        "description": "Priority-based event routing for content and output management",
    },
]


def _gh_api(endpoint: str) -> dict | list | None:
    url = f"https://api.github.com{endpoint}"
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError:
        return None


def inventory_repos() -> list[dict]:
    """Inventory all GitHub repositories."""
    repos = _gh_api(f"/users/{GITHUB_USER}/repos?per_page=100&sort=updated") or []
    inventory = []
    for r in repos:
        inventory.append({
            "name": r.get("name", ""),
            "description": r.get("description", ""),
            "language": r.get("language"),
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "url": r.get("html_url", ""),
            "created": r.get("created_at", ""),
            "updated": r.get("updated_at", ""),
            "is_fork": r.get("fork", False),
            "has_pages": r.get("has_pages", False),
            "topics": r.get("topics", []),
            "size_kb": r.get("size", 0),
        })
    return inventory


def inventory_vercel() -> list[dict]:
    """Return known Vercel deployment inventory."""
    return VERCEL_PROJECTS


def inventory_content() -> dict:
    """Inventory content library from the current repo."""
    repo_root = Path(__file__).parent.parent
    content = {
        "markdown_docs": [],
        "scripts": [],
        "configs": [],
    }

    for md in repo_root.glob("*.md"):
        content["markdown_docs"].append({
            "name": md.name,
            "size_bytes": md.stat().st_size,
        })

    for py in repo_root.glob("**/*.py"):
        if ".git" not in str(py):
            content["scripts"].append({
                "name": str(py.relative_to(repo_root)),
                "size_bytes": py.stat().st_size,
            })

    for cfg in list(repo_root.glob("*.json")) + list(repo_root.glob("*.yml")) + list(repo_root.glob("*.yaml")):
        content["configs"].append({
            "name": cfg.name,
            "size_bytes": cfg.stat().st_size,
        })

    return content


def compute_asset_summary(repos: list[dict], vercel: list[dict], content: dict) -> dict:
    """Compute a summary of all digital assets."""
    return {
        "github": {
            "total_repos": len(repos),
            "original_repos": len([r for r in repos if not r.get("is_fork")]),
            "forked_repos": len([r for r in repos if r.get("is_fork")]),
            "total_stars": sum(r.get("stars", 0) for r in repos),
            "total_forks": sum(r.get("forks", 0) for r in repos),
            "languages": list({r["language"] for r in repos if r.get("language")}),
        },
        "vercel": {
            "total_deployments": len(vercel),
            "types": list({v["type"] for v in vercel}),
        },
        "content_library": {
            "markdown_docs": len(content.get("markdown_docs", [])),
            "python_scripts": len(content.get("scripts", [])),
            "config_files": len(content.get("configs", [])),
        },
        "intellectual_property": {
            "total_ip_assets": len(IP_CATEGORIES),
            "categories": [ip["type"] for ip in IP_CATEGORIES],
        },
    }


def generate_inventory() -> str:
    """Generate and save the full asset inventory."""
    now = datetime.now(timezone.utc)

    print("[Assets] Inventorying GitHub repos...")
    repos = inventory_repos()

    print("[Assets] Inventorying Vercel deployments...")
    vercel = inventory_vercel()

    print("[Assets] Inventorying content library...")
    content = inventory_content()

    print("[Assets] Computing asset summary...")
    summary = compute_asset_summary(repos, vercel, content)

    inventory = {
        "generated_at": now.isoformat(),
        "owner": f"@{GITHUB_USER}",
        "summary": summary,
        "github_repos": repos,
        "vercel_deployments": vercel,
        "content_library": content,
        "intellectual_property": IP_CATEGORIES,
    }

    ASSETS_JSON.write_text(json.dumps(inventory, indent=2))
    return str(ASSETS_JSON)


def run() -> None:
    """Main entry point for asset tracking."""
    print("[Asset Tracker] Starting inventory...")
    path = generate_inventory()
    print(f"[Asset Tracker] Inventory written to {path}")

    inventory = json.loads(ASSETS_JSON.read_text())
    summary = inventory.get("summary", {})
    gh = summary.get("github", {})
    print(f"  GitHub: {gh.get('total_repos', 0)} repos, {gh.get('total_stars', 0)} stars")
    print(f"  Vercel: {summary.get('vercel', {}).get('total_deployments', 0)} deployments")
    print(f"  IP Assets: {summary.get('intellectual_property', {}).get('total_ip_assets', 0)}")


if __name__ == "__main__":
    run()
