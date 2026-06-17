"""WF-08 — Recursive Spawn Protocol: ephemeral child agents on FIRE_SPAWN_NEEDED"""
import os, asyncio, httpx
from app.fire import on_fire, fire

METAROM_URL  = os.environ.get("METAROM_URL",  "https://metarom.onrender.com")
AGENTNET_URL = os.environ.get("AGENTNET_URL", "https://evez-agentnet.onrender.com")
MAX_CHILDREN = int(os.environ.get("MAX_CHILDREN_PER_AGENT", "3"))
CHILD_TTL    = int(os.environ.get("CHILD_TTL_MINUTES",      "30"))

_children: dict = {}  # parent_id -> [child_id, ...]

@on_fire("FIRE_SPAWN_NEEDED")
async def handle_spawn(payload: dict):
    pid = payload["agent_id"]
    kids = _children.get(pid, [])
    if len(kids) >= MAX_CHILDREN:
        return

    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.get(f"{METAROM_URL}/prompt/{pid}")
        parent_prompt = r.json().get("system_prompt", "") if r.status_code == 200 else ""

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{AGENTNET_URL}/spawn", json={
            "parent_id":    pid,
            "system_prompt": parent_prompt,
            "ttl_minutes":  CHILD_TTL,
        })
    if r.status_code != 200:
        return

    cid = r.json().get("child_id")
    kids.append(cid)
    _children[pid] = kids
    await fire("FIRE_AGENT_SPAWNED", {"parent_id": pid, "child_id": cid})
    asyncio.create_task(_dissolve(pid, cid))

async def _dissolve(pid: str, cid: str):
    await asyncio.sleep(CHILD_TTL * 60)
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"{AGENTNET_URL}/dissolve/{cid}")
    _children.get(pid, []).remove(cid)
    await fire("FIRE_AGENT_DISSOLVED", {"parent_id": pid, "child_id": cid})
