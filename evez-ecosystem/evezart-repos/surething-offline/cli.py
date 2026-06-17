#!/usr/bin/env python3
"""
SureThing Offline — CLI
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
import typer, httpx, json

app = typer.Typer(help="SureThing Offline CLI")
BASE = f"http://localhost:{os.getenv('PORT', '8420')}"

@app.command()
def health():
    """Check system health."""
    try:
        typer.echo(json.dumps(httpx.get(f"{BASE}/health", timeout=5).json(), indent=2))
    except Exception as e:
        typer.echo(f"Error: {e}")

@app.command()
def chat(message: str):
    """Send a chat message."""
    try:
        r = httpx.post(f"{BASE}/chat", json={"message": message}, timeout=60)
        typer.echo(f"\n{r.json()['response']}\n")
    except Exception as e:
        typer.echo(f"Error: {e}")

@app.command()
def tasks(status: str = "pending"):
    """List tasks."""
    try:
        for t in httpx.get(f"{BASE}/tasks", params={"status": status}, timeout=5).json()["tasks"]:
            typer.echo(f"[{t['status']}] {t['title']} ({t['executor']})")
    except Exception as e:
        typer.echo(f"Error: {e}")

@app.command()
def spine(limit: int = 20):
    """Show recent spine events."""
    try:
        for ev in httpx.get(f"{BASE}/spine", params={"limit": limit}, timeout=5).json()["events"]:
            typer.echo(f"[{ev['type']}] {ev['timestamp']} — {ev.get('subject', '-')}")
    except Exception as e:
        typer.echo(f"Error: {e}")

@app.command()
def verify():
    """Verify spine hash chain."""
    try:
        d = httpx.get(f"{BASE}/spine/verify", timeout=5).json()
        if d["chain_valid"]:
            typer.echo(f"\u2713 Chain valid \u2014 {d['total_events']} events")
        else:
            typer.echo(f"\u2717 Chain has {len(d['issues'])} issues")
    except Exception as e:
        typer.echo(f"Error: {e}")

@app.command()
def remember(content: str, category: str = "general"):
    """Save a memory."""
    try:
        d = httpx.post(f"{BASE}/memory", json={"content": content, "category": category}, timeout=10).json()
        typer.echo(f"\u2713 Saved: {d['id']}")
    except Exception as e:
        typer.echo(f"Error: {e}")

if __name__ == "__main__":
    app()
