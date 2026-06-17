from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Callable
import uuid, json, hashlib, pathlib

@dataclass
class Event:
    id: str
    ts: str
    domain: str
    kind: str
    payload: Dict[str, Any]
    meta: Dict[str, Any]
    prevHash: str = ""
    hash: str = ""

EVENT_LOG_PATH = pathlib.Path("src/memory/meme_events.jsonl")
_subscribers: List[Callable] = []
_last_hash: str = ""

def _compute_hash(ev_dict: dict) -> str:
    canon = json.dumps(ev_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canon.encode()).hexdigest()

def emit_event(domain, kind, payload, meta=None) -> "Event":
    global _last_hash
    ev = Event(
        id=str(uuid.uuid4()),
        ts=datetime.now(timezone.utc).isoformat(),
        domain=domain, kind=kind,
        payload=payload, meta=meta or {},
        prevHash=_last_hash
    )
    d = ev.__dict__.copy()
    ev.hash = _compute_hash(d)
    d["hash"] = ev.hash
    _last_hash = ev.hash
    EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVENT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(d) + "\n")
    for sub in list(_subscribers):
        try:
            sub(ev)
        except Exception as e:
            print(f"[bus] subscriber error: {e}")
    return ev

def subscribe(handler: Callable) -> None:
    _subscribers.append(handler)
