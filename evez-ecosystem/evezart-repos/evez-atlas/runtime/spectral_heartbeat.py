#!/usr/bin/env python3
"""
Atlas v3 Spectral Heartbeat — 15-min cycle.
Runs simplified spectral analysis of agent network,
computes Fiedler proxy, broadcasts health to ledger + Ably.
"""
import os, json, datetime, hashlib, requests, base64, math

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ABLY_KEY = os.environ.get("ABLY_KEY", "")
OWNER = "EvezArt"

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

NODES = [
    "evez-autonomous-ledger", "evez-os", "evez-agentnet",
    "agentvault", "evez-meme-bus", "Evez666",
]

# Adjacency: which repos are directly connected (share data/events)
EDGES = [
    ("evez-autonomous-ledger", "evez-agentnet"),
    ("evez-autonomous-ledger", "evez-os"),
    ("evez-autonomous-ledger", "agentvault"),
    ("evez-autonomous-ledger", "evez-meme-bus"),
    ("evez-autonomous-ledger", "Evez666"),
    ("evez-agentnet", "evez-os"),
    ("evez-agentnet", "evez-meme-bus"),
    ("evez-os", "evez-meme-bus"),
    ("Evez666", "evez-agentnet"),
]


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def degree(node):
    return sum(1 for e in EDGES if node in e)


def fiedler_proxy():
    """Approximate Fiedler value without scipy: min degree / max degree."""
    degrees = {n: degree(n) for n in NODES}
    min_d = min(degrees.values())
    max_d = max(degrees.values())
    return round(min_d / max_d, 4) if max_d > 0 else 0.0


def get_repo_health(repo):
    url = f"https://api.github.com/repos/{OWNER}/{repo}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        d = r.json()
        return {"open_issues": d.get("open_issues_count", 0),
                "pushed_at": d.get("pushed_at", "")}
    return {"error": r.status_code}


def bottleneck_nodes():
    """Nodes that appear in most edges — single points of failure."""
    counts = {n: degree(n) for n in NODES}
    max_d = max(counts.values())
    return [n for n, d in counts.items() if d == max_d]


def post_to_ledger(event):
    content = json.dumps(event, indent=2)
    encoded = base64.b64encode(content.encode()).decode()
    ts = now_iso().replace(":", "-").replace(".", "-")
    url = f"https://api.github.com/repos/{OWNER}/evez-autonomous-ledger/contents/DECISIONS/{ts}_spectral_atlas.json"
    requests.put(url, headers=HEADERS, json={
        "message": f"🔮 spectral: fiedler={event.get('fiedler_proxy')} @ {event['timestamp']}",
        "content": encoded,
    })


def broadcast(event):
    if not ABLY_KEY:
        return
    key_id, key_secret = ABLY_KEY.split(":")
    requests.post(
        "https://rest.ably.io/channels/evez-ops/messages",
        json={"name": "spectral_heartbeat", "data": json.dumps(event)},
        auth=(key_id, key_secret)
    )


def main():
    print(f"\n🔮 Atlas v3 Spectral Heartbeat — {now_iso()}")

    fiedler = fiedler_proxy()
    bottlenecks = bottleneck_nodes()
    health = {n: get_repo_health(n) for n in NODES}
    total_issues = sum(v.get("open_issues", 0) for v in health.values())

    print(f"  Fiedler proxy: {fiedler} (1.0=fully connected, <0.3=fragile)")
    print(f"  Bottleneck nodes: {bottlenecks}")
    print(f"  Total open issues: {total_issues}")

    status = "healthy" if fiedler >= 0.5 else "fragile"
    print(f"  Network status: {status.upper()}")

    event = {
        "type": "spectral_heartbeat",
        "source": "Evez666/Atlas-v3",
        "timestamp": now_iso(),
        "fiedler_proxy": fiedler,
        "bottleneck_nodes": bottlenecks,
        "total_open_issues": total_issues,
        "network_status": status,
        "node_health": health,
        "chain_hash": hashlib.sha256(
            f"{fiedler}{bottlenecks}{total_issues}".encode()
        ).hexdigest()[:16],
    }

    post_to_ledger(event)
    broadcast(event)
    print("  ✅ Spectral heartbeat complete.")


if __name__ == "__main__":
    main()
