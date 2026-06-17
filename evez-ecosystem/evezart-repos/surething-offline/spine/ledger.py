"""
SureThing Offline — Event Spine
Append-only JSONL ledger with SHA-256 hash chain.
Every event: evidence_hash (meaning) + event_hash (meaning+ancestry).
"""
from __future__ import annotations
import hashlib, json, os, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

SPINE_PATH = Path(os.getenv("SPINE_PATH", "./data/spine.jsonl"))
EventType = Literal["observation","transformation","claim","test","decision","linkage","system"]

def _utcnow(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def _jcs(obj): return json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode("utf-8")
def _sha256(data): return hashlib.sha256(data).hexdigest()

def _evidence_hash(event):
    stripped = {k:v for k,v in event.items() if k not in ("parent_hash","evidence_hash","event_hash","id")}
    return _sha256(_jcs(stripped))

def _event_hash(event):
    stripped = {k:v for k,v in event.items() if k != "event_hash"}
    return _sha256(_jcs(stripped))

def _last_event_hash():
    SPINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SPINE_PATH.exists(): return None
    last = None
    with SPINE_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try: last = json.loads(line).get("event_hash")
                except: pass
    return last

def emit(event_type, payload, operator_lane="system", subject=None, tags=None):
    SPINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {"id": str(uuid.uuid4()), "type": event_type, "operator_lane": operator_lane,
             "subject": subject, "tags": tags or [], "timestamp": _utcnow(),
             "payload": payload, "parent_hash": _last_event_hash()}
    event["evidence_hash"] = _evidence_hash(event)
    event["event_hash"] = _event_hash(event)
    with SPINE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True, separators=(",",":")) + "\n")
    return event

def read_events(limit=100, offset=0):
    if not SPINE_PATH.exists(): return []
    events = []
    with SPINE_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try: events.append(json.loads(line))
                except: pass
    return events[offset:offset+limit]

def verify_chain():
    events = read_events(limit=999999)
    issues = []
    for i, ev in enumerate(events):
        check = {k:v for k,v in ev.items() if k not in ("parent_hash","evidence_hash","event_hash","id")}
        if ev.get("evidence_hash") != _sha256(_jcs(check)):
            issues.append({"index":i,"id":ev["id"],"issue":"evidence_hash_mismatch"})
        if i > 0 and ev.get("parent_hash") != events[i-1].get("event_hash"):
            issues.append({"index":i,"id":ev["id"],"issue":"parent_chain_broken"})
    return {"total_events": len(events), "issues": issues, "chain_valid": len(issues)==0}
