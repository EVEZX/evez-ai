"""
EVEZ Task Router — Delegates tasks between agents
Writes to spine + OpenTree + NATS for full provenance
"""
import json, time, sys, asyncio
import requests
import nats

NATS_URL = "nats://45.63.66.247:4222"
OPENTREE = "http://45.63.66.247:8002"
OPENGRAPH = "http://45.63.66.247:8003"

def create_task(task_id, title, assigned_to, created_by="azra", priority="normal"):
    """Create a task in OpenTree and notify via NATS"""
    # Write to OpenTree
    r = requests.post(f"{OPENTREE}/nodes", json={
        "path": f"tasks/{task_id}",
        "data": {
            "title": title,
            "assigned_to": assigned_to,
            "created_by": created_by,
            "status": "pending",
            "priority": priority,
            "created_at": time.time()
        }
    })
    # Notify via NATS
    asyncio.run(_publish_task(task_id, title, assigned_to, created_by))
    return r.json()

async def _publish_task(task_id, title, assigned_to, created_by):
    nc = await nats.connect(NATS_URL)
    await nc.publish("evez.agents.tasks", json.dumps({
        "task_id": task_id,
        "title": title,
        "assigned_to": assigned_to,
        "created_by": created_by,
        "ts": time.time()
    }).encode())
    await nc.close()

def get_pending_tasks():
    """Get all pending tasks"""
    r = requests.get(f"{OPENTREE}/nodes", params={"prefix": "tasks/"})
    return r.json()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "list":
            print(json.dumps(get_pending_tasks(), indent=2))
        elif cmd == "create" and len(sys.argv) > 4:
            result = create_task(sys.argv[2], sys.argv[3], sys.argv[4])
            print(json.dumps(result, indent=2))
