"""Append-only JSONL storage layer for meme spine events."""
import json, pathlib
from typing import Iterator
from bus.events import Event

DB_PATH = pathlib.Path("src/memory/meme_events.jsonl")

def replay_events() -> Iterator[dict]:
    """Replay all events from the log — useful for audit and recovery."""
    if not DB_PATH.exists():
        return
    with DB_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def count_by_kind() -> dict:
    counts = {}
    for ev in replay_events():
        k = ev.get("kind", "UNKNOWN")
        counts[k] = counts.get(k, 0) + 1
    return counts