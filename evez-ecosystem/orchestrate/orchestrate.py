#!/usr/bin/env python3
"""
EVEZ Orchestrate — Port 10015
Multi-agent task orchestrator. Decompose goals, assign to agents, track completion.
"""
import json, time, hashlib, sqlite3, asyncio
from aiohttp import web

PORT = 10015
DB = sqlite3.connect("/home/openclaw/evez-ecosystem/orchestrate/orchestrate.db")
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE IF NOT EXISTS goals (
        id TEXT PRIMARY KEY, title TEXT, description TEXT,
        status TEXT DEFAULT 'active', priority TEXT DEFAULT 'normal',
        decomposed INTEGER DEFAULT 0, created REAL, completed REAL
    );
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY, goal_id TEXT, title TEXT, description TEXT,
        assignee TEXT DEFAULT '', status TEXT DEFAULT 'pending',
        result TEXT DEFAULT '', order_idx INTEGER, created REAL, completed REAL
    );
    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY, name TEXT, capabilities TEXT,
        status TEXT DEFAULT 'idle', last_heartbeat REAL
    );
""")
DB.commit()

async def handle_create_goal(req):
    body = await req.json()
    gid = hashlib.md5(f"{body['title']}{time.time()}".encode()).hexdigest()[:8]
    DB.execute("INSERT INTO goals VALUES (?,?,?,?,?,?,?,?)",
              (gid, body["title"], body.get("description",""), "active",
               body.get("priority","normal"), 0, time.time(), None))
    DB.commit()
    return web.json_response({"id": gid, "title": body["title"], "status": "active"})

async def handle_decompose(req):
    gid = req.match_info.get("id", "")
    goal = DB.execute("SELECT * FROM goals WHERE id=?", (gid,)).fetchone()
    if not goal: return web.json_response({"error": "Not found"}, status=404)
    
    tasks_data = (await req.json()).get("tasks", [])
    for i, t in enumerate(tasks_data):
        tid = hashlib.md5(f"{gid}{t}{time.time()}".encode()).hexdigest()[:8]
        DB.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)",
                  (tid, gid, t, "", "", "pending", "", i, time.time(), None))
    DB.execute("UPDATE goals SET decomposed=1 WHERE id=?", (gid,))
    DB.commit()
    return web.json_response({"goal_id": gid, "tasks_created": len(tasks_data)})

async def handle_assign_task(req):
    tid = req.match_info.get("id", "")
    body = await req.json()
    DB.execute("UPDATE tasks SET assignee=?, status='assigned' WHERE id=?",
              (body.get("assignee",""), tid))
    DB.commit()
    return web.json_response({"task_id": tid, "assignee": body.get("assignee"), "status": "assigned"})

async def handle_complete_task(req):
    tid = req.match_info.get("id", "")
    body = await req.json()
    DB.execute("UPDATE tasks SET status='completed', result=?, completed=? WHERE id=?",
              (body.get("result",""), time.time(), tid))
    # Check if all goal tasks are done
    task = DB.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
    if task:
        remaining = DB.execute("SELECT COUNT(*) as c FROM tasks WHERE goal_id=? AND status!='completed'",
                              (task["goal_id"],)).fetchone()["c"]
        if remaining == 0:
            DB.execute("UPDATE goals SET status='completed', completed=? WHERE id=?",
                      (time.time(), task["goal_id"]))
    DB.commit()
    return web.json_response({"task_id": tid, "status": "completed"})

async def handle_goals(req):
    rows = DB.execute("SELECT * FROM goals ORDER BY created DESC").fetchall()
    return web.json_response({"goals": [dict(r) for r in rows]})

async def handle_tasks(req):
    gid = req.query.get("goal_id", "")
    rows = DB.execute("SELECT * FROM tasks WHERE goal_id=? ORDER BY order_idx", (gid,)).fetchall()
    return web.json_response({"tasks": [dict(r) for r in rows]})

async def handle_heartbeat(req):
    body = await req.json()
    aid = body.get("agent_id", "unknown")
    DB.execute("INSERT OR REPLACE INTO agents VALUES (?,?,?,?,?)",
              (aid, body.get("name", aid), json.dumps(body.get("capabilities",[])),
               body.get("status","idle"), time.time()))
    DB.commit()
    # Assign pending tasks
    task = DB.execute("SELECT * FROM tasks WHERE assignee=? AND status='pending' LIMIT 1", (aid,)).fetchone()
    if task:
        DB.execute("UPDATE tasks SET status='assigned' WHERE id=?", (task["id"],))
        DB.commit()
        return web.json_response({"assigned": dict(task)})
    return web.json_response({"assigned": None})

async def handle_health(req):
    goals = DB.execute("SELECT COUNT(*) as c FROM goals").fetchone()["c"]
    tasks = DB.execute("SELECT COUNT(*) as c FROM tasks").fetchone()["c"]
    agents = DB.execute("SELECT COUNT(*) as c FROM agents").fetchone()["c"]
    return web.json_response({"status": "healthy", "service": "evez-orchestrate",
                             "goals": goals, "tasks": tasks, "agents": agents, "port": PORT})

app = web.Application()
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/goals", handle_create_goal)
app.router.add_post("/v1/goals/{id}/decompose", handle_decompose)
app.router.add_get("/v1/goals", handle_goals)
app.router.add_get("/v1/tasks", handle_tasks)
app.router.add_post("/v1/tasks/{id}/assign", handle_assign_task)
app.router.add_post("/v1/tasks/{id}/complete", handle_complete_task)
app.router.add_post("/v1/heartbeat", handle_heartbeat)

if __name__ == "__main__":
    print(f"🎯 EVEZ Orchestrate → :{PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)
