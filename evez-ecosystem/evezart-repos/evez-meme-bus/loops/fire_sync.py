"""
FireSync — reads the EVEZ-OS spine fire_log.jsonl and emits FIRE_EVENT
for any new FIRE entries (fire_numbers non-empty).
This feeds real FIRE topology data into the CaptionAgent.
Runs on a poll loop; tracks last-seen entry by logged_at.
"""
import os, pathlib, json, time
from datetime import datetime, timezone
from bus.events import emit_event

SPINE_LOG = pathlib.Path(os.getenv(
    "SPINE_LOG_PATH",
    "../spine/fire_log.jsonl"
))
STATE_FILE = pathlib.Path("src/memory/fire_sync_state.json")

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_logged_at": None, "fires_emitted": 0}

def _save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

def run_poll_loop(interval_sec: int = 120):
    state = _load_state()
    last_logged_at = state.get("last_logged_at")
    fires_emitted = state.get("fires_emitted", 0)
    print(f"[FireSync] starting — last_logged_at={last_logged_at}, fires_emitted={fires_emitted}")

    while True:
        if not SPINE_LOG.exists():
            time.sleep(interval_sec)
            continue

        new_last = last_logged_at
        new_count = 0

        for line in SPINE_LOG.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue

            logged_at = entry.get("logged_at", "")
            fire_numbers = entry.get("fire_numbers", [])

            # skip already-seen entries
            if last_logged_at and logged_at <= last_logged_at:
                continue

            # only emit FIRE_EVENT for entries with explicit fire numbers
            if fire_numbers:
                for fn in fire_numbers:
                    v_vals = entry.get("v_values", [])
                    rounds = entry.get("rounds", [])
                    emit_event("fire", "FIRE_EVENT", {
                        "fire_number": fn,
                        "v_value": v_vals[0] if v_vals else None,
                        "round": rounds[0] if rounds else None,
                        "raw_text": entry.get("raw_text", ""),
                        "tweet_id": entry.get("tweet_id"),
                        "falsifier": entry.get("falsifier", "")
                    }, {"source_agent": "FireSync"})
                    fires_emitted += 1
                    new_count += 1

            if logged_at > (new_last or ""):
                new_last = logged_at

        if new_count > 0:
            print(f"[FireSync] emitted {new_count} FIRE_EVENTs")

        state["last_logged_at"] = new_last
        state["fires_emitted"] = fires_emitted
        _save_state(state)

        time.sleep(interval_sec)

if __name__ == "__main__":
    run_poll_loop()
