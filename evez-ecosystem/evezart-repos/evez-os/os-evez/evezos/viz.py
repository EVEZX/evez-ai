"""evezos.viz — minimal ASCII spine visualizer (no heavy deps required)."""
import json
from pathlib import Path


def summarize_spine(spine_path: Path) -> str:
    lines = []
    if not Path(spine_path).exists():
        return "spine.jsonl not found"
    events = [json.loads(l) for l in Path(spine_path).read_text().splitlines() if l.strip()]
    lines.append(f"Spine: {spine_path} ({len(events)} events)")
    for i, evt in enumerate(events[-10:]):
        lines.append(f"  [{i:3d}] {evt['type']:20s}  {evt['chain_hash'][:12]}...")
    return "\n".join(lines)
