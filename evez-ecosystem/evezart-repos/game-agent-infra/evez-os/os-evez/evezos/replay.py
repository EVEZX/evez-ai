"""evezos.replay — deterministic event replay."""
import json
from pathlib import Path
from .spine import Spine, _chain_hash


def replay(spine_path: Path) -> tuple[bool, str, list]:
    """Replay spine, verifying chain hashes. Returns (ok, message, events)."""
    events = Spine(spine_path).read_all()
    if not events:
        return True, "empty spine", []
    prev_hash = "0" * 64
    for i, evt in enumerate(events):
        expected = _chain_hash(prev_hash, {k: v for k, v in evt.items() if k != "chain_hash"})
        if evt.get("chain_hash") != expected:
            return False, f"chain break at event {i}", events[:i]
        prev_hash = evt["chain_hash"]
    return True, f"OK ({len(events)} events)", events
