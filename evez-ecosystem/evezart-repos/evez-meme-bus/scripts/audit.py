"""Audit the meme spine event log."""
from bus.storage import count_by_kind, replay_events
import json

if __name__ == "__main__":
    counts = count_by_kind()
    print("=== MEME SPINE AUDIT ===")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print("\n=== LAST 10 EVENTS ===")
    events = list(replay_events())
    for ev in events[-10:]:
        print(json.dumps(ev, indent=2))