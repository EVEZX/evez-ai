"""evezos.spine — append-only spine writer with per-event chain hash."""
import hashlib, json, time
from pathlib import Path


def _chain_hash(prev_hash: str, event: dict) -> str:
    payload = prev_hash + json.dumps(event, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


class Spine:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._prev_hash = "0" * 64
        # replay to get last hash
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    evt = json.loads(line)
                    self._prev_hash = evt.get("chain_hash", self._prev_hash)

    def append(self, event_type: str, data: dict) -> dict:
        evt = {
            "ts": time.time(),
            "type": event_type,
            "data": data,
        }
        evt["chain_hash"] = _chain_hash(self._prev_hash, evt)
        self._prev_hash = evt["chain_hash"]
        with self.path.open("a") as f:
            f.write(json.dumps(evt, separators=(",", ":")) + "\n")
        return evt

    def read_all(self) -> list:
        if not self.path.exists():
            return []
        return [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]
