"""Shared utilities for OMEGA CONDUCTOR."""
import json, subprocess, math
from datetime import datetime, timezone

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def exec_sql(sql):
    r = subprocess.run(['surething', 'appdb', 'exec-sql', sql], capture_output=True, text=True)
    try:   return json.loads(r.stdout)
    except: return None

def q(s):
    if s is None: return 'NULL'
    return "'" + str(s).replace("'","''")[:1000] + "'"

def run_tool(slug, args):
    """Thin wrapper — calls run_composio_tool from the surething runtime."""
    try:
        data, err = run_composio_tool(slug, args)
        return data, err
    except Exception as e:
        return None, str(e)

def omega_score(n=4, d=4, lam=1.0, N=15.5):
    return n * math.exp(lam * d) * math.log(N)

def ensure_appdb_tables():
    tables = [
        """CREATE TABLE IF NOT EXISTS omega_events (
            id TEXT PRIMARY KEY,
            surface TEXT,
            event_type TEXT,
            payload TEXT,
            delta_score REAL DEFAULT 0.0,
            synthesized INTEGER DEFAULT 0,
            created_at TEXT,
            synced_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS omega_actions (
            id TEXT PRIMARY KEY,
            source_event_id TEXT,
            target_surface TEXT,
            action_type TEXT,
            payload TEXT,
            status TEXT DEFAULT 'pending',
            executed_at TEXT,
            created_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS omega_self_dev_log (
            id TEXT PRIMARY KEY,
            iteration INTEGER,
            surfaces_scanned INTEGER,
            issues_found INTEGER,
            capabilities_added INTEGER,
            omega_delta REAL,
            notes TEXT,
            created_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS omega_meta (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )""",
    ]
    for t in tables:
        exec_sql(t + ";")

def update_meta(key, value):
    ts = now_iso()
    exec_sql(f"INSERT OR REPLACE INTO omega_meta VALUES ({q(key)},{q(str(value))},{q(ts)});")
