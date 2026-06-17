#!/usr/bin/env python3
"""
evez-meme-bus Heartbeat — 15-min pulse.
Emits BUS_ALIVE event to Ably evez-ops + ledger.
Actuates ably_publisher if ABLY_KEY present.
"""
import os, json, datetime, hashlib, requests, base64

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ABLY_KEY = os.environ.get("ABLY_KEY", "")
OWNER = "EvezArt"

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def emit_bus_alive():
    event = {
        "type": "BUS_ALIVE",
        "source": "evez-meme-bus",
        "timestamp": now_iso(),
        "status": "nominal",
        "signal": hashlib.sha256(f"bus_{now_iso()}".encode()).hexdigest()[:16],
    }

    # Ledger
    content = json.dumps(event, indent=2)
    encoded = base64.b64encode(content.encode()).decode()
    ts = now_iso().replace(":", "-").replace(".", "-")
    url = f"https://api.github.com/repos/{OWNER}/evez-autonomous-ledger/contents/DECISIONS/{ts}_BUS_ALIVE.json"
    requests.put(url, headers=HEADERS, json={
        "message": f"📡 BUS_ALIVE @ {event['timestamp']}",
        "content": encoded,
    })

    # Ably
    if ABLY_KEY:
        key_id, key_secret = ABLY_KEY.split(":")
        requests.post(
            "https://rest.ably.io/channels/evez-ops/messages",
            json={"name": "BUS_ALIVE", "data": json.dumps(event)},
            auth=(key_id, key_secret)
        )
        print(f"  📡 BUS_ALIVE → evez-ops")

    return event


def main():
    print(f"\n📡 evez-meme-bus Heartbeat — {now_iso()}")
    event = emit_bus_alive()
    print(f"  Signal: {event['signal']}")
    print("  ✅ Bus alive.")


if __name__ == "__main__":
    main()
