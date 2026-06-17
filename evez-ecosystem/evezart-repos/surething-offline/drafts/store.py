"""
SureThing Offline — Draft Store
"""
from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DRAFTS_PATH = Path(os.getenv("DRAFTS_PATH", "./data/drafts"))

def _utcnow(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def create(draft_type, content, task_id=None):
    DRAFTS_PATH.mkdir(parents=True, exist_ok=True)
    d = {"id": str(uuid.uuid4()), "type": draft_type, "status": "pending",
         "content": content, "task_id": task_id, "created_at": _utcnow(), "updated_at": _utcnow()}
    (DRAFTS_PATH / f"{d['id']}.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
    return d

def get(draft_id):
    p = DRAFTS_PATH / f"{draft_id}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def update(draft_id, **kwargs):
    d = get(draft_id)
    if not d: return None
    d.update(kwargs); d["updated_at"] = _utcnow()
    (DRAFTS_PATH / f"{draft_id}.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
    return d

def list_drafts(status=None):
    DRAFTS_PATH.mkdir(parents=True, exist_ok=True)
    drafts = []
    for p in DRAFTS_PATH.glob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if status is None or d.get("status") == status: drafts.append(d)
        except: pass
    return sorted(drafts, key=lambda x: x.get("created_at",""), reverse=True)

def approve(draft_id): return update(draft_id, status="approved")
def cancel(draft_id): return update(draft_id, status="cancelled")
