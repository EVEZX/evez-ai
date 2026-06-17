#!/usr/bin/env python3
"""
EVEZ Web Intelligence — Researcher Module

Lightweight web research using GitHub API only (no browser).
Scans trending repos, topics, and checks ecosystem visibility.
Saves findings as dated markdown files in intelligence/research/.
"""

import os
import json
import time
import datetime
import sys

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not available.")
    sys.exit(0)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ORG = os.environ.get("REPO_OWNER", "EvezArt")
API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
API_DELAY = 0.5
RESEARCH_DIR = "intelligence/research"


def utcnow():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def today_str():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


def _api(method, url, **kwargs):
    time.sleep(API_DELAY)
    try:
        resp = getattr(requests, method)(url, headers=HEADERS, timeout=30, **kwargs)
        return resp
    except Exception as exc:
        print(f"  ⚠ API {method.upper()} {url}: {exc}")
        return None


def search_trending_repos(topics=None, min_stars=50, created_after_days=30):
    """Search GitHub for recently created repos in relevant topics."""
    if topics is None:
        topics = ["ai-agents", "autonomous-agents", "llm-agents", "ai-tools", "agent-framework"]

    results = []
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=created_after_days)).strftime("%Y-%m-%d")

    for topic in topics[:5]:  # cap to avoid rate limits
        query = f"topic:{topic} created:>{since} stars:>={min_stars}"
        resp = _api("get", f"{API}/search/repositories",
                     params={"q": query, "sort": "stars", "order": "desc", "per_page": 10})
        if resp and resp.status_code == 200:
            for repo in resp.json().get("items", []):
                results.append({
                    "name": repo["full_name"],
                    "description": (repo.get("description") or "")[:200],
                    "stars": repo.get("stargazers_count", 0),
                    "url": repo.get("html_url", ""),
                    "topic": topic,
                    "created_at": repo.get("created_at", ""),
                    "language": repo.get("language", ""),
                })

    # Deduplicate by name
    seen = set()
    unique = []
    for r in results:
        if r["name"] not in seen:
            seen.add(r["name"])
            unique.append(r)
    return sorted(unique, key=lambda x: x["stars"], reverse=True)


def check_org_visibility():
    """Check if any EvezArt repos appear in search results."""
    findings = []
    resp = _api("get", f"{API}/search/repositories",
                params={"q": f"org:{ORG}", "sort": "stars", "order": "desc", "per_page": 10})
    if resp and resp.status_code == 200:
        for repo in resp.json().get("items", []):
            findings.append({
                "name": repo["full_name"],
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "watchers": repo.get("watchers_count", 0),
                "description": (repo.get("description") or "")[:200],
            })
    return findings


def scan_topics():
    """Discover relevant GitHub topics and their repo counts."""
    topics_to_scan = [
        "autonomous-agents", "ai-agents", "llm-agents",
        "agent-framework", "ai-tools", "multi-agent",
        "self-improving-ai", "ai-automation",
    ]
    topic_data = []
    for t in topics_to_scan:
        resp = _api("get", f"{API}/search/repositories",
                     params={"q": f"topic:{t}", "per_page": 1})
        if resp and resp.status_code == 200:
            count = resp.json().get("total_count", 0)
            topic_data.append({"topic": t, "repo_count": count})
    return sorted(topic_data, key=lambda x: x["repo_count"], reverse=True)


def generate_research_report():
    """Run all research tasks and save a dated markdown report."""
    print("  🔍 RESEARCH — gathering web intelligence")

    trending = search_trending_repos()
    print(f"    Found {len(trending)} trending repos")

    visibility = check_org_visibility()
    print(f"    {ORG} visibility: {len(visibility)} repos in search")

    topics = scan_topics()
    print(f"    Scanned {len(topics)} topics")

    # Build report
    lines = [
        f"# Web Intelligence Report — {today_str()}",
        f"",
        f"**Generated:** {utcnow()}",
        f"",
        f"## Trending AI/Agent Repos (last 30 days)",
        f"",
    ]
    for r in trending[:15]:
        lines.append(f"- **[{r['name']}]({r['url']})** — ⭐ {r['stars']} | {r['language'] or 'N/A'}")
        if r["description"]:
            lines.append(f"  {r['description']}")

    lines.extend([
        "",
        f"## {ORG} Ecosystem Visibility",
        "",
    ])
    if visibility:
        for v in visibility:
            lines.append(f"- **{v['name']}** — ⭐ {v['stars']} | 🍴 {v['forks']} | 👀 {v['watchers']}")
            if v["description"]:
                lines.append(f"  {v['description']}")
    else:
        lines.append("No public repos found in search results.")

    lines.extend([
        "",
        "## Topic Landscape",
        "",
    ])
    for t in topics:
        lines.append(f"- `{t['topic']}`: {t['repo_count']:,} repos")

    lines.extend(["", "---", "*Generated by EVEZ Intelligence Researcher*"])

    # Save
    os.makedirs(RESEARCH_DIR, exist_ok=True)
    filepath = os.path.join(RESEARCH_DIR, f"{today_str()}.md")
    try:
        with open(filepath, "w") as f:
            f.write("\n".join(lines) + "\n")
        print(f"    Saved research report: {filepath}")
    except Exception as exc:
        print(f"  ⚠ Failed to save research: {exc}")

    return {
        "trending_count": len(trending),
        "visibility_count": len(visibility),
        "topics_scanned": len(topics),
        "report_path": filepath,
    }


if __name__ == "__main__":
    generate_research_report()
