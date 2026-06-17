"""WF-08 — Recursive Spawn Protocol.

When queue_depth > SPAWN_THRESHOLD, spawn ephemeral child agents.
Children inherit parent system_prompt from metarom.
Children have TTL = CHILD_TTL_MINUTES, dissolve after merging results.

Routes:
  POST /api/spawn
  GET  /api/spawn/status
  POST /api/spawn/{child_id}/dissolve
"""
import os, time, json, secrets, logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

router = APIRouter(prefix="/api/spawn", tags=["spawn"])
log = logging.getLogger("spawn")

DATA_DIR        = Path(os.environ.get("OG_DATA_DIR", Path.home() / "og_data"))
SPAWN_DIR       = DATA_DIR / "spawns"
SPAWN_DIR.mkdir(parents=True, exist_ok=True)

SPAWN_THRESHOLD     = int(os.environ.get("SPAWN_THRESHOLD", "5"))
MAX_CHILDREN        = int(os.environ.get("MAX_CHILDREN_PER_AGENT", "3"))
CHILD_TTL_MINUTES   = int(os.environ.get("CHILD_TTL_MINUTES", "30"))


def _fire(event: str, data: dict):
    import httpx
    url = os.environ.get("N8N_FIRE_URL", "")
    if not url: return
    try: httpx.post(url, json={"event": event, "data": data, "ts": time.time()}, timeout=5)
    except: pass


class SpawnRequest(BaseModel):
    parent_agent_id: str
    queue_depth:     int
    task_batch:      list


@router.post("")
def spawn_children(req: SpawnRequest):
    if req.queue_depth < SPAWN_THRESHOLD:
        return {"spawned": 0, "reason": f"queue_depth {req.queue_depth} < threshold {SPAWN_THRESHOLD}"}

    # Check existing children for this parent
    existing = [f for f in SPAWN_DIR.glob(f"{req.parent_agent_id}_*.json")]
    active   = []
    for ef in existing:
        d = json.loads(ef.read_text())
        if d.get("status") == "active" and time.time() < d.get("ttl_ts", 0):
            active.append(d)

    slots = MAX_CHILDREN - len(active)
    if slots <= 0:
        return {"spawned": 0, "reason": "max_children reached"}

    # Fetch parent system_prompt from metarom
    parent_prompt = ""
    metarom_url = os.environ.get("METAROM_URL", "")
    if metarom_url:
        try:
            import httpx
            r = httpx.get(f"{metarom_url}/memory/read",
                          params={"agent_id": req.parent_agent_id,
                                  "key": "system_prompt"},
                          timeout=5)
            parent_prompt = r.json().get("value", "")
        except: pass

    spawned = []
    for i, task in enumerate(req.task_batch[:slots]):
        child_id  = f"{req.parent_agent_id}_child_{secrets.token_hex(4)}"
        ttl_ts    = time.time() + CHILD_TTL_MINUTES * 60
        child_rec = {
            "child_id":        child_id,
            "parent_id":       req.parent_agent_id,
            "task":            task,
            "system_prompt":   parent_prompt,
            "status":          "active",
            "spawned_at":      time.time(),
            "ttl_ts":          ttl_ts,
            "ttl_minutes":     CHILD_TTL_MINUTES,
            "result":          None
        }
        (SPAWN_DIR / f"{child_id}.json").write_text(json.dumps(child_rec, indent=2))
        spawned.append(child_id)
        _fire("FIRE_AGENT_SPAWNED", {"child_id": child_id, "parent_id": req.parent_agent_id})
        log.info(f"Spawned {child_id} (TTL {CHILD_TTL_MINUTES}m)")

    return {"spawned": len(spawned), "children": spawned,
            "ttl_minutes": CHILD_TTL_MINUTES}


@router.get("/status")
def spawn_status():
    now = time.time()
    all_files = list(SPAWN_DIR.glob("*.json"))
    active, expired = [], []
    for f in all_files:
        d = json.loads(f.read_text())
        if d.get("status") == "active":
            if now < d.get("ttl_ts", 0):
                active.append({"child_id": d["child_id"],
                                "parent_id": d["parent_id"],
                                "ttl_remaining_s": int(d["ttl_ts"] - now)})
            else:
                expired.append(d["child_id"])
    return {"active_children": active, "expired_pending_dissolve": expired,
            "spawn_threshold": SPAWN_THRESHOLD, "max_children": MAX_CHILDREN}


@router.post("/{child_id}/dissolve")
def dissolve_child(child_id: str, result: dict = None):
    cf = SPAWN_DIR / f"{child_id}.json"
    if not cf.exists(): raise HTTPException(404, "child not found")
    d = json.loads(cf.read_text())
    d["status"]       = "dissolved"
    d["result"]       = result
    d["dissolved_at"] = time.time()
    cf.write_text(json.dumps(d, indent=2))
    _fire("FIRE_AGENT_DISSOLVED", {"child_id": child_id, "parent_id": d["parent_id"]})
    log.info(f"Dissolved {child_id}")
    return {"dissolved": True, "child_id": child_id}
