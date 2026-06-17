"""Revenue Orchestrator — Central coordinator for all income streams.

Monitors active revenue channels (GitHub Sponsors, Ko-fi, Stripe),
tracks revenue events, computes metrics, and generates reports.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

GITHUB_USER = "EvezArt"
KOFI_USER = "evez666"

# Revenue channel registry
CHANNELS = {
    "github_sponsors": {
        "name": "GitHub Sponsors",
        "url": f"https://github.com/sponsors/{GITHUB_USER}",
        "type": "recurring",
    },
    "ko_fi": {
        "name": "Ko-fi",
        "url": f"https://ko-fi.com/{KOFI_USER}",
        "type": "tips_and_recurring",
    },
    "paypal": {
        "name": "PayPal",
        "url": "https://www.paypal.me/rubikspubes70",
        "type": "tips",
    },
}


def _gh_api(endpoint: str) -> dict | list | None:
    """Call GitHub API with optional token auth."""
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


def get_repo_metrics() -> dict:
    """Fetch aggregate repo metrics for the GitHub user."""
    repos = _gh_api(f"/users/{GITHUB_USER}/repos?per_page=100&sort=updated")
    if not repos:
        return {"total_repos": 0, "total_stars": 0, "total_forks": 0}
    return {
        "total_repos": len(repos),
        "total_stars": sum(r.get("stargazers_count", 0) for r in repos),
        "total_forks": sum(r.get("forks_count", 0) for r in repos),
        "top_repos": sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:5],
    }


def load_revenue_log() -> list[dict]:
    """Load persisted revenue events."""
    log_path = REPORTS_DIR / "revenue_log.json"
    if log_path.exists():
        return json.loads(log_path.read_text())
    return []


def record_event(channel: str, amount: float, currency: str = "USD", note: str = "") -> dict:
    """Record a revenue event from any channel."""
    log = load_revenue_log()
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "channel": channel,
        "amount": amount,
        "currency": currency,
        "note": note,
    }
    log.append(event)
    (REPORTS_DIR / "revenue_log.json").write_text(json.dumps(log, indent=2))
    return event


def compute_metrics(log: list[dict] | None = None) -> dict:
    """Compute daily/weekly/monthly revenue metrics."""
    if log is None:
        log = load_revenue_log()
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    def _sum_since(cutoff: datetime) -> float:
        total = 0.0
        for e in log:
            ts = datetime.fromisoformat(e["timestamp"])
            if ts >= cutoff:
                total += e.get("amount", 0)
        return total

    by_channel: dict[str, float] = {}
    for e in log:
        ch = e.get("channel", "unknown")
        by_channel[ch] = by_channel.get(ch, 0) + e.get("amount", 0)

    return {
        "total_all_time": sum(e.get("amount", 0) for e in log),
        "daily": _sum_since(day_ago),
        "weekly": _sum_since(week_ago),
        "monthly": _sum_since(month_ago),
        "by_channel": by_channel,
        "event_count": len(log),
    }


def identify_underperformers(metrics: dict) -> list[str]:
    """Identify channels with no or low revenue and suggest optimizations."""
    suggestions = []
    by_channel = metrics.get("by_channel", {})

    for key, info in CHANNELS.items():
        revenue = by_channel.get(key, 0)
        if revenue == 0:
            suggestions.append(
                f"[{info['name']}] No revenue recorded. "
                f"Add prominent links and CTAs to README. URL: {info['url']}"
            )
        elif revenue < 10:
            suggestions.append(
                f"[{info['name']}] Low revenue (${revenue:.2f}). "
                f"Consider creating sponsor tiers or promotional content."
            )

    if not by_channel:
        suggestions.append(
            "No revenue events recorded yet. Set up webhook integrations "
            "to automatically log revenue from GitHub Sponsors, Ko-fi, and PayPal."
        )
    return suggestions


def generate_report() -> str:
    """Generate a full revenue report and write it to reports/."""
    repo_metrics = get_repo_metrics()
    revenue_metrics = compute_metrics()
    suggestions = identify_underperformers(revenue_metrics)
    now = datetime.now(timezone.utc)

    report = {
        "generated_at": now.isoformat(),
        "owner": f"@{GITHUB_USER}",
        "repo_metrics": {
            "total_repos": repo_metrics.get("total_repos", 0),
            "total_stars": repo_metrics.get("total_stars", 0),
            "total_forks": repo_metrics.get("total_forks", 0),
        },
        "revenue": revenue_metrics,
        "channels": {k: v["url"] for k, v in CHANNELS.items()},
        "optimization_suggestions": suggestions,
    }

    # Write JSON report
    report_path = REPORTS_DIR / f"report_{now.strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2))

    # Write latest symlink-style report
    latest_path = REPORTS_DIR / "latest_report.json"
    latest_path.write_text(json.dumps(report, indent=2))

    return str(report_path)


def run() -> None:
    """Main entry point for the orchestrator."""
    print("[Revenue Orchestrator] Generating report...")
    path = generate_report()
    print(f"[Revenue Orchestrator] Report written to {path}")

    metrics = compute_metrics()
    print(f"[Revenue Orchestrator] All-time revenue: ${metrics['total_all_time']:.2f}")
    print(f"[Revenue Orchestrator] Monthly revenue:  ${metrics['monthly']:.2f}")

    suggestions = identify_underperformers(metrics)
    if suggestions:
        print("[Revenue Orchestrator] Optimization suggestions:")
        for s in suggestions:
            print(f"  - {s}")


if __name__ == "__main__":
    run()
