"""
SpineBridge — writes every MEME_PUBLISHED and MEME_POSTED event back to
the EVEZ-OS canonical spine (fire_log.jsonl) as a falsifier record.
This is the constitutional link between the meme bus and the parent OS.
"""
import os, pathlib, json, time
from datetime import datetime, timezone
from bus.events import subscribe, Event

SPINE_LOG = pathlib.Path(os.getenv(
    "SPINE_LOG_PATH",
    "../spine/fire_log.jsonl"  # override with absolute path in prod
))

def _write_spine(record: dict):
    SPINE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SPINE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print(f"[SpineBridge] wrote spine entry: {record.get('falsifier')}")

def handle_event(ev: Event):
    if ev.domain == "publish" and ev.kind == "MEME_PUBLISHED":
        record = {
            "tweet_id": None,
            "created_at": ev.ts,
            "raw_text": ev.payload.get("caption", ""),
            "fire_numbers": [],
            "v_values": [],
            "rounds": [],
            "is_fire_relevant": True,
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "falsifier": f"meme:bus:{ev.id}",
            "event_id": ev.id,
            "domain": "meme",
            "slot": ev.payload.get("slot", ""),
            "output_path": ev.payload.get("output_path", "")
        }
        _write_spine(record)

    if ev.domain == "twitter" and ev.kind == "MEME_POSTED":
        record = {
            "tweet_id": ev.payload.get("tweet_id"),
            "created_at": ev.ts,
            "raw_text": ev.payload.get("tweet_text", ""),
            "fire_numbers": [],
            "v_values": [],
            "rounds": [],
            "is_fire_relevant": True,
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "falsifier": f"twitter:tweet:{ev.payload.get('tweet_id')}",
            "event_id": ev.id,
            "domain": "meme_posted",
            "tweet_url": ev.payload.get("tweet_url", "")
        }
        _write_spine(record)

def start():
    subscribe(handle_event)

if __name__ == "__main__":
    start()
    print(f"[SpineBridge] writing falsifiers to {SPINE_LOG}")
    while True:
        time.sleep(60)
