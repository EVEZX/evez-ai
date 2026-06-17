"""Content Engine — Automated content creation from the codebase.

Scans EvezArt repos for interesting code, architectures, and innovations,
then packages them as tutorials, docs, code examples, and social media drafts.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

CONTENT_DIR = Path(__file__).parent / "content"
CONTENT_DIR.mkdir(exist_ok=True)

GITHUB_USER = "EvezArt"


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


def scan_repos() -> list[dict]:
    """Scan all EvezArt repos for content opportunities."""
    repos = _gh_api(f"/users/{GITHUB_USER}/repos?per_page=100&sort=updated") or []
    opportunities = []
    for repo in repos:
        name = repo.get("name", "")
        desc = repo.get("description", "") or ""
        lang = repo.get("language", "Unknown")
        stars = repo.get("stargazers_count", 0)
        topics = repo.get("topics", [])

        # Identify content-worthy repos
        signals = []
        if stars >= 1:
            signals.append("has_stars")
        if any(t in topics for t in ["ai", "agent", "autonomous", "neural", "quantum"]):
            signals.append("trending_topic")
        if lang in ("Python", "TypeScript", "JavaScript"):
            signals.append("popular_language")
        if desc and len(desc) > 20:
            signals.append("has_description")

        if signals:
            opportunities.append({
                "repo": name,
                "description": desc,
                "language": lang,
                "stars": stars,
                "topics": topics,
                "signals": signals,
                "url": repo.get("html_url", ""),
            })
    return opportunities


def generate_tutorial(repo_info: dict) -> str:
    """Generate a tutorial blog post template for a repo."""
    name = repo_info["repo"]
    desc = repo_info.get("description", "An innovative project")
    lang = repo_info.get("language", "Python")
    url = repo_info.get("url", "")

    content = f"""# Building with {name}: A Technical Deep Dive

> {desc}

## Overview

[{name}]({url}) is a {lang}-based project that demonstrates cutting-edge
approaches to autonomous systems and AI agent architecture.

## Key Concepts

### Architecture
The project uses a modular architecture designed for extensibility
and autonomous operation.

### Core Components
- **Runtime Engine**: Handles execution flow and state management
- **Protocol Layer**: Manages inter-component communication
- **Intelligence Module**: Drives decision-making and optimization

## Getting Started

```bash
git clone {url}.git
cd {name}
# Follow repo-specific setup instructions
```

## What Makes This Interesting

This project stands out because of its approach to:
1. Autonomous operation without human intervention
2. Self-optimizing performance characteristics
3. Modular, extensible architecture

## About the Author

Built by [@EVEZ666](https://github.com/{GITHUB_USER}) — building the future
of autonomous AI systems.

---
*Support this work: [GitHub Sponsors](https://github.com/sponsors/{GITHUB_USER})
| [Ko-fi](https://ko-fi.com/evez666)*
"""
    return content


def generate_social_post(repo_info: dict) -> str:
    """Generate a social media content draft."""
    name = repo_info["repo"]
    desc = repo_info.get("description", "")
    lang = repo_info.get("language", "")
    url = repo_info.get("url", "")

    post = (
        f"Just shipped updates to {name} "
        f"— {desc[:100] if desc else 'autonomous AI systems'}.\n\n"
        f"Built with #{lang} | Open source\n"
        f"{url}\n\n"
        f"#AI #Autonomous #OpenSource #Developer"
    )
    return post


def generate_readme_improvements(repo_info: dict) -> str:
    """Generate README improvement suggestions to drive traffic."""
    name = repo_info["repo"]
    return f"""# README Improvements for {name}

## Suggested Additions

### Badges
Add these badges to the top of your README:
```markdown
[![GitHub Sponsors](https://img.shields.io/github/sponsors/{GITHUB_USER}?style=for-the-badge)](https://github.com/sponsors/{GITHUB_USER})
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-ff5f5f?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/evez666)
[![Stars](https://img.shields.io/github/stars/{GITHUB_USER}/{name}?style=for-the-badge)](https://github.com/{GITHUB_USER}/{name})
```

### Call to Action
Add a "Support" section at the bottom:
```markdown
## Support This Project
If you find this useful, consider:
- Starring the repo
- [Sponsoring on GitHub](https://github.com/sponsors/{GITHUB_USER})
- [Buying me a coffee on Ko-fi](https://ko-fi.com/evez666)
```

### SEO Keywords
Add relevant topics to the repo: `ai`, `autonomous`, `agent`, `python`, `open-source`
"""


def run() -> None:
    """Main entry point for the content engine."""
    print("[Content Engine] Scanning repos for content opportunities...")
    opportunities = scan_repos()
    print(f"[Content Engine] Found {len(opportunities)} content-worthy repos")

    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Generate content for top opportunities
    for repo_info in opportunities[:10]:
        name = repo_info["repo"]

        # Tutorial
        tutorial = generate_tutorial(repo_info)
        tutorial_path = CONTENT_DIR / f"tutorial_{name}.md"
        tutorial_path.write_text(tutorial)

        # Social post
        social = generate_social_post(repo_info)
        social_path = CONTENT_DIR / f"social_{name}.md"
        social_path.write_text(social)

        # README improvements
        readme_tips = generate_readme_improvements(repo_info)
        readme_path = CONTENT_DIR / f"readme_improvements_{name}.md"
        readme_path.write_text(readme_tips)

        print(f"  - Generated content for {name}")

    # Write manifest
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "opportunities": opportunities,
        "content_generated": min(len(opportunities), 10),
    }
    (CONTENT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[Content Engine] Content written to {CONTENT_DIR}")


if __name__ == "__main__":
    run()
