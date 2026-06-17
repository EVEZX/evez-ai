"""Market Intelligence — Monitors market opportunities.

Tracks trending topics on GitHub, identifies gaps in the AI agent market,
suggests new products/features, and monitors competitor projects.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

INTEL_DIR = Path(__file__).parent / "intel"
INTEL_DIR.mkdir(exist_ok=True)

# AI/autonomous systems competitors and reference projects
COMPETITOR_REPOS = [
    "microsoft/autogen",
    "langchain-ai/langchain",
    "crewAIInc/crewAI",
    "joaomdmoura/crewAI",
    "geekan/MetaGPT",
    "Significant-Gravitas/AutoGPT",
    "AntonOsika/gpt-engineer",
]

# Market segments to track
MARKET_SEGMENTS = [
    "ai-agent",
    "autonomous-systems",
    "llm-orchestration",
    "ai-automation",
    "code-generation",
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


def search_trending(query: str, sort: str = "stars") -> list[dict]:
    """Search GitHub for trending repos in a topic."""
    data = _gh_api(
        f"/search/repositories?q={query}+created:>2025-01-01&sort={sort}"
        f"&order=desc&per_page=10"
    )
    if not data or "items" not in data:
        return []
    return [
        {
            "name": r["full_name"],
            "description": r.get("description", ""),
            "stars": r["stargazers_count"],
            "language": r.get("language"),
            "url": r["html_url"],
            "created": r["created_at"],
        }
        for r in data["items"]
    ]


def get_competitor_stats() -> list[dict]:
    """Fetch stats for known competitor projects."""
    results = []
    for repo_path in COMPETITOR_REPOS:
        data = _gh_api(f"/repos/{repo_path}")
        if data:
            results.append({
                "repo": repo_path,
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "language": data.get("language"),
                "description": data.get("description", ""),
                "last_push": data.get("pushed_at", ""),
                "url": data.get("html_url", ""),
            })
    return results


def identify_market_gaps(trending: list[dict], competitors: list[dict]) -> list[dict]:
    """Identify gaps and opportunities in the market."""
    gaps = []

    # Check for underserved niches
    niches = {
        "autonomous-revenue": "Autonomous revenue generation systems — few projects automate monetization",
        "ai-agent-orchestration": "Multi-agent orchestration with built-in monetization hooks",
        "spectral-analysis": "Spectral/frequency-domain analysis for code and system optimization",
        "synaptic-networks": "Neural-inspired network protocols for distributed AI systems",
        "self-healing-ci": "CI/CD systems that autonomously fix failing builds",
    }

    for niche, description in niches.items():
        results = search_trending(niche)
        if len(results) < 3:
            gaps.append({
                "niche": niche,
                "description": description,
                "competition_level": "low" if len(results) == 0 else "medium",
                "existing_projects": len(results),
                "opportunity": "HIGH" if len(results) < 2 else "MEDIUM",
            })

    return gaps


def suggest_products(gaps: list[dict]) -> list[dict]:
    """Suggest new products/features based on market gaps."""
    suggestions = []
    for gap in gaps:
        if gap["opportunity"] == "HIGH":
            suggestions.append({
                "product": f"{gap['niche']}-toolkit",
                "description": (
                    f"Open-source toolkit for {gap['description'].lower()}. "
                    f"Low competition ({gap['existing_projects']} existing projects). "
                    f"Monetize via GitHub Sponsors, premium features, and consulting."
                ),
                "monetization": [
                    "GitHub Sponsors tier for premium support",
                    "Pro version with advanced features",
                    "Consulting/integration services",
                    "Tutorial content and courses",
                ],
                "effort": "medium",
                "potential": "high",
            })
    return suggestions


def generate_intel_report() -> str:
    """Generate a full market intelligence report."""
    now = datetime.now(timezone.utc)
    print("[Market Intel] Searching trending repos...")

    trending_by_segment: dict[str, list] = {}
    for segment in MARKET_SEGMENTS:
        trending_by_segment[segment] = search_trending(segment)

    print("[Market Intel] Fetching competitor stats...")
    competitors = get_competitor_stats()

    print("[Market Intel] Identifying market gaps...")
    all_trending = [r for repos in trending_by_segment.values() for r in repos]
    gaps = identify_market_gaps(all_trending, competitors)

    print("[Market Intel] Generating product suggestions...")
    suggestions = suggest_products(gaps)

    report = {
        "generated_at": now.isoformat(),
        "trending_by_segment": trending_by_segment,
        "competitor_analysis": competitors,
        "market_gaps": gaps,
        "product_suggestions": suggestions,
    }

    report_path = INTEL_DIR / f"intel_{now.strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2))

    latest_path = INTEL_DIR / "latest_intel.json"
    latest_path.write_text(json.dumps(report, indent=2))

    return str(report_path)


def run() -> None:
    """Main entry point for market intelligence."""
    print("[Market Intel] Starting market analysis...")
    path = generate_intel_report()
    print(f"[Market Intel] Report written to {path}")


if __name__ == "__main__":
    run()
