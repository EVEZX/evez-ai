"""
OMEGA CONDUCTOR — sync.py
Cross-platform intelligence perception → synthesis → action → broadcast
Runs every 30 min via cron task.
"""
import uuid, json
from omega_conductor.utils import *
from omega_conductor import SUPABASE_REF, GITHUB_ORG, VERSION, OMEGA

def pull_github(ts):
    """Perception: GitHub repos, commits, issues."""
    signals = []
    data, err = run_tool("GITHUB_LIST_REPOSITORIES_FOR_USER", {"username": GITHUB_ORG, "type": "owner", "per_page": 30})
    if isinstance(data, dict):
        repos = data.get("repositories", data.get("data", {}).get("items", []))
        if isinstance(repos, list):
            signals.append({"surface": "github", "type": "repo_count", "value": len(repos),
                             "repos": [r.get("name","") for r in repos[:10]]})
    return signals

def pull_slack(ts):
    """Perception: Slack channels, recent messages."""
    signals = []
    data, _ = run_tool("SLACK_LIST_ALL_SLACK_TEAM_CHANNELS", {"limit": 20})
    if isinstance(data, dict):
        channels = data.get("channels", [])
        signals.append({"surface": "slack", "type": "channel_count", "value": len(channels)})
    return signals

def pull_linear(ts):
    """Perception: Linear issues."""
    signals = []
    data, _ = run_tool("LINEAR_GET_VIEWER_ISSUES", {})
    if isinstance(data, dict):
        issues = data.get("issues", data.get("data", {}).get("issues", {}).get("nodes", []))
        if isinstance(issues, list):
            signals.append({"surface": "linear", "type": "open_issues", "value": len(issues)})
    return signals

def pull_supabase(ts):
    """Perception: Supabase evezstation activity."""
    signals = []
    data, _ = run_tool("SUPABASE_BETA_RUN_SQL_QUERY", {
        "ref": SUPABASE_REF,
        "query": "SELECT COUNT(*) as n FROM evezstation.training_pairs;",
        "read_only": True
    })
    if isinstance(data, dict):
        rows = data.get("result", [])
        if rows:
            signals.append({"surface": "supabase", "type": "training_pairs", "value": rows[0].get("n", 0)})
    return signals

def pull_vercel(ts):
    """Perception: Vercel deployments."""
    signals = []
    data, _ = run_tool("VERCEL_LIST_ALL_DEPLOYMENTS", {"limit": 10})
    if isinstance(data, dict):
        deploys = data.get("deployments", [])
        signals.append({"surface": "vercel", "type": "deployment_count", "value": len(deploys)})
    return signals

def pull_youtube(ts):
    """Perception: YouTube channel stats."""
    signals = []
    data, _ = run_tool("YOUTUBE_GET_MY_CHANNEL", {})
    if isinstance(data, dict):
        items = data.get("items", [])
        if items:
            stats = items[0].get("statistics", {})
            signals.append({"surface": "youtube", "type": "subscriber_count",
                             "value": int(stats.get("subscriberCount", 0))})
    return signals

def pull_asana(ts):
    """Perception: Asana tasks."""
    signals = []
    data, _ = run_tool("ASANA_GET_MULTIPLE_TASKS", {"opt_fields": "name,completed,due_on"})
    if isinstance(data, dict):
        tasks = data.get("data", [])
        if isinstance(tasks, list):
            open_tasks = [t for t in tasks if not t.get("completed", False)]
            signals.append({"surface": "asana", "type": "open_tasks", "value": len(open_tasks)})
    return signals

def synthesize(all_signals):
    """Synthesis: assign delta scores, rank cross-surface patterns."""
    scored = []
    for s in all_signals:
        v = s.get("value", 0)
        score = min(1.0, (v / 100.0) if isinstance(v, (int, float)) else 0.5)
        scored.append({**s, "delta_score": score})
    scored.sort(key=lambda x: x["delta_score"], reverse=True)
    return scored

def store_events(signals, ts):
    """Action: store perceived signals in AppDB."""
    for s in signals:
        eid = str(uuid.uuid4())[:8]
        exec_sql(f"""INSERT OR IGNORE INTO omega_events VALUES (
            {q(eid)},{q(s.get('surface','?'))},{q(s.get('type','?'))},
            {q(json.dumps(s))},{s.get('delta_score',0.0)},0,{q(ts)},{q(ts)});""")

def broadcast_to_slack(signals, ts, iteration):
    """Action: post livestream digest to Slack #general."""
    surface_lines = "\n".join(
        f"  • *{s['surface']}* — {s['type']}: `{s.get('value','?')}` (Δ {s.get('delta_score',0):.2f})"
        for s in signals[:8]
    )
    omega = omega_score()
    msg = (
        f"*⚡ OMEGA CONDUCTOR — Sync #{iteration}* | `{ts[:19]}Z`\n"
        f"Ω = {omega:.1f}x | 14 surfaces | v{VERSION}\n\n"
        f"*Intelligence digest:*\n{surface_lines if surface_lines else '  (all surfaces nominal)'}\n\n"
        f"_Recursive self-amplification running. Stack is never stopping._"
    )
    run_tool("SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL", {
        "channel": "#general", "text": msg
    })

def main():
    ts = now_iso()
    print(f"\n{'═'*56}")
    print(f"  OMEGA CONDUCTOR — sync.py  |  {ts[:19]}")
    print(f"  Ω ≈ {OMEGA:.0f}x  |  {VERSION}")
    print(f"{'═'*56}\n")

    ensure_appdb_tables()

    # ── Perception (pull all surfaces) ──
    all_signals = []
    for puller in [pull_github, pull_slack, pull_linear,
                   pull_supabase, pull_vercel, pull_youtube, pull_asana]:
        try:
            sigs = puller(ts)
            all_signals.extend(sigs)
            print(f"  ✅ {puller.__name__[5:]}: {len(sigs)} signals")
        except Exception as e:
            print(f"  ⚠️  {puller.__name__[5:]}: {e}")

    # ── Synthesis ──
    ranked = synthesize(all_signals)
    print(f"\n  Synthesized {len(ranked)} signals across {len(set(s['surface'] for s in ranked))} surfaces")

    # ── Store in AppDB ──
    store_events(ranked, ts)

    # ── Get iteration count ──
    res = exec_sql("SELECT COUNT(DISTINCT DATE(created_at)) as n FROM omega_events;")
    iteration = 1
    if isinstance(res, dict):
        rows = res.get("data", {}).get("rows", [])
        if rows: iteration = max(1, rows[0].get("n", 1))

    # ── Broadcast ──
    broadcast_to_slack(ranked, ts, iteration)
    print(f"  📡 Broadcast to Slack")

    # ── Update meta ──
    update_meta("last_sync", ts)
    update_meta("signals_total", len(all_signals))
    update_meta("omega_capacity", f"{omega_score():.2f}")
    update_meta("version", VERSION)

    print(f"\n✅ Sync complete — {ts}\n")

if __name__ == "__main__":
    main()
