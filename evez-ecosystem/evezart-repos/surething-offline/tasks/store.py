"""
SureThing Offline — Task Spine (SQLite)
"""
from __future__ import annotations
import json, os, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(os.getenv("TASKS_DB_PATH", "./data/tasks.db"))

def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def _init():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
            executor TEXT NOT NULL DEFAULT 'ai', action TEXT, why_human TEXT, draft_id TEXT,
            trigger_type TEXT, trigger_config TEXT, condition TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        c.commit()

def _utcnow(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def create(title, executor="ai", action=None, why_human=None, draft_id=None,
           trigger_type=None, trigger_config=None, condition=None):
    _init()
    tid = str(uuid.uuid4()); now = _utcnow()
    with _conn() as c:
        c.execute("INSERT INTO tasks (id,title,status,executor,action,why_human,draft_id,"
                  "trigger_type,trigger_config,condition,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (tid,title,"pending",executor,action,why_human,draft_id,trigger_type,
                   json.dumps(trigger_config) if trigger_config else None,condition,now,now))
        c.commit()
    return get(tid)

def get(task_id):
    _init()
    with _conn() as c:
        row = c.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    return dict(row) if row else None

def update(task_id, **kwargs):
    _init()
    allowed = {"title","status","executor","action","why_human","draft_id","trigger_type","trigger_config","condition"}
    fields = {k:v for k,v in kwargs.items() if k in allowed}
    if not fields: return get(task_id)
    fields["updated_at"] = _utcnow()
    sc = ", ".join(f"{k}=?" for k in fields)
    with _conn() as c:
        c.execute(f"UPDATE tasks SET {sc} WHERE id=?", list(fields.values())+[task_id])
        c.commit()
    return get(task_id)

def list_tasks(status=None, executor=None, limit=50):
    _init()
    q = "SELECT * FROM tasks WHERE 1=1"; p: list[Any] = []
    if status: q += " AND status=?"; p.append(status)
    if executor: q += " AND executor=?"; p.append(executor)
    q += " ORDER BY created_at DESC LIMIT ?"; p.append(limit)
    with _conn() as c: rows = c.execute(q, p).fetchall()
    return [dict(r) for r in rows]

def delete(task_id):
    _init()
    with _conn() as c:
        affected = c.execute("DELETE FROM tasks WHERE id=?", (task_id,)).rowcount
        c.commit()
    return affected > 0
