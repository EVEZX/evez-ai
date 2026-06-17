"""Sponsor Optimization — Maximizes sponsorship revenue.

Generates optimized FUNDING.yml, creates sponsor tier descriptions,
tracks leading metrics, and maintains a sponsor CRM.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

REVENUE_DIR = Path(__file__).parent
SPONSORS_JSON = REVENUE_DIR / "sponsors.json"
GITHUB_USER = "EvezArt"
KOFI_USER = "evez666"


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


# Sponsor tier definitions
SPONSOR_TIERS = [
    {
        "name": "Supporter",
        "amount": 3,
        "currency": "USD",
        "frequency": "monthly",
        "perks": [
            "Shoutout in README",
            "Sponsor badge on profile",
            "Access to sponsor-only updates",
        ],
    },
    {
        "name": "Backer",
        "amount": 7,
        "currency": "USD",
        "frequency": "monthly",
        "perks": [
            "All Supporter perks",
            "Early access to new projects",
            "Name in SPONSORS.md",
        ],
    },
    {
        "name": "Champion",
        "amount": 15,
        "currency": "USD",
        "frequency": "monthly",
        "perks": [
            "All Backer perks",
            "Priority feature requests",
            "Logo in README (if org)",
            "Monthly progress report",
        ],
    },
    {
        "name": "Patron",
        "amount": 30,
        "currency": "USD",
        "frequency": "monthly",
        "perks": [
            "All Champion perks",
            "1-on-1 monthly call",
            "Custom integration support",
            "Top billing in all repos",
        ],
    },
]


def generate_funding_yml() -> str:
    """Generate optimized FUNDING.yml content."""
    return """# Funding links for @EVEZ666 / Steven Crawford-Maggard
# These are supported funding model platforms

github: EvezArt
ko_fi: evez666
custom:
  - https://www.paypal.me/rubikspubes70
"""


def get_traffic_metrics() -> dict:
    """Fetch repo traffic as leading indicators for sponsorship."""
    repos = _gh_api(f"/users/{GITHUB_USER}/repos?per_page=100&sort=stars") or []
    metrics = {
        "total_repos": len(repos),
        "total_stars": 0,
        "total_forks": 0,
        "total_watchers": 0,
        "repos_with_stars": 0,
    }
    for r in repos:
        stars = r.get("stargazers_count", 0)
        metrics["total_stars"] += stars
        metrics["total_forks"] += r.get("forks_count", 0)
        metrics["total_watchers"] += r.get("watchers_count", 0)
        if stars > 0:
            metrics["repos_with_stars"] += 1
    return metrics


def generate_readme_badges() -> str:
    """Generate README badge markdown for sponsor CTAs."""
    return f"""<!-- Sponsor Badges -->
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-%E2%9D%A4-ff69b4?style=for-the-badge&logo=github)](https://github.com/sponsors/{GITHUB_USER})
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20coffee-ff5f5f?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/{KOFI_USER})
[![PayPal](https://img.shields.io/badge/PayPal-Tip-00457C?style=for-the-badge&logo=paypal)](https://www.paypal.me/rubikspubes70)
"""


def load_sponsor_crm() -> dict:
    """Load the sponsor CRM data."""
    if SPONSORS_JSON.exists():
        return json.loads(SPONSORS_JSON.read_text())
    return {"sponsors": [], "leads": [], "updated_at": None}


def save_sponsor_crm(crm: dict) -> None:
    """Save sponsor CRM data."""
    crm["updated_at"] = datetime.now(timezone.utc).isoformat()
    SPONSORS_JSON.write_text(json.dumps(crm, indent=2))


def add_sponsor(name: str, tier: str, platform: str, amount: float, note: str = "") -> dict:
    """Add a sponsor to the CRM."""
    crm = load_sponsor_crm()
    sponsor = {
        "name": name,
        "tier": tier,
        "platform": platform,
        "amount": amount,
        "note": note,
        "added_at": datetime.now(timezone.utc).isoformat(),
        "active": True,
    }
    crm["sponsors"].append(sponsor)
    save_sponsor_crm(crm)
    return sponsor


def get_conversion_suggestions(metrics: dict) -> list[str]:
    """Suggest actions to convert traffic into sponsorships."""
    suggestions = []
    stars = metrics.get("total_stars", 0)
    repos = metrics.get("total_repos", 0)

    if stars < 50:
        suggestions.append(
            "Star count is low. Focus on creating high-quality READMEs with "
            "demos, screenshots, and clear value propositions to attract stars."
        )
    if repos > 10:
        suggestions.append(
            f"You have {repos} repos — pin your best 6 on your GitHub profile "
            f"and add sponsor badges to all of them."
        )
    suggestions.append(
        "Add a 'Sponsor' section to your top 5 repos' READMEs with the "
        "badge markdown from generate_readme_badges()."
    )
    suggestions.append(
        "Create a SPONSORS.md file listing current sponsors to create social proof."
    )
    suggestions.append(
        "Post about your work on social media weekly — consistent visibility "
        "converts followers into sponsors."
    )
    return suggestions


def run() -> None:
    """Main entry point for sponsor optimization."""
    print("[Sponsors] Generating optimized FUNDING.yml...")
    funding = generate_funding_yml()
    print(funding)

    print("[Sponsors] Fetching traffic metrics...")
    metrics = get_traffic_metrics()
    print(f"  Stars: {metrics['total_stars']} | Forks: {metrics['total_forks']} | Repos: {metrics['total_repos']}")

    print("[Sponsors] Generating badge markdown...")
    badges = generate_readme_badges()
    print(badges)

    print("[Sponsors] Conversion suggestions:")
    for s in get_conversion_suggestions(metrics):
        print(f"  - {s}")

    # Initialize CRM if needed
    crm = load_sponsor_crm()
    crm["tiers"] = SPONSOR_TIERS
    crm["metrics_snapshot"] = {**metrics, "captured_at": datetime.now(timezone.utc).isoformat()}
    save_sponsor_crm(crm)
    print(f"[Sponsors] CRM updated at {SPONSORS_JSON}")


if __name__ == "__main__":
    run()
