"""Agent Registry — tracks all agent instances, their capabilities, and status."""
import sqlite3
import json
import time
import subprocess
from pathlib import Path

class AgentRegistry:
    """Central registry for all agent instances."""
    
    def __init__(self, db_path="data/station.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                status TEXT DEFAULT 'unknown',
                capabilities TEXT DEFAULT '[]',
                model TEXT DEFAULT '',
                created_at REAL NOT NULL,
                last_heartbeat REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                transfer_state TEXT DEFAULT 'local'
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                assigned_to TEXT,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5,
                created_at REAL NOT NULL,
                started_at REAL,
                completed_at REAL,
                result TEXT,
                parent_task TEXT
            );

            CREATE TABLE IF NOT EXISTS transfers (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                source_host TEXT NOT NULL,
                target_host TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                started_at REAL,
                completed_at REAL,
                snapshot_path TEXT,
                error TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_agent TEXT NOT NULL,
                to_agent TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                read INTEGER DEFAULT 0
            );
        """)
        self.conn.commit()

    def register_agent(self, agent_id, name, host, port, capabilities=None, model="", metadata=None):
        """Register a new agent instance."""
        self.conn.execute("""
            INSERT OR REPLACE INTO agents (id, name, host, port, status, capabilities, model, created_at, last_heartbeat, metadata)
            VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
        """, (
            agent_id, name, host, port,
            json.dumps(capabilities or []),
            model, time.time(), time.time(),
            json.dumps(metadata or {})
        ))
        self.conn.commit()

    def heartbeat(self, agent_id):
        """Update agent heartbeat."""
        self.conn.execute("UPDATE agents SET last_heartbeat = ?, status = 'active' WHERE id = ?",
                         (time.time(), agent_id))
        self.conn.commit()

    def get_agent(self, agent_id):
        """Get agent details."""
        row = self.conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
        return dict(row) if row else None

    def list_agents(self, status=None):
        """List all registered agents."""
        if status:
            rows = self.conn.execute("SELECT * FROM agents WHERE status = ?", (status,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM agents").fetchall()
        return [dict(r) for r in rows]

    def find_capable(self, capability):
        """Find agents with a specific capability."""
        rows = self.conn.execute("SELECT * FROM agents WHERE status = 'active'").fetchall()
        results = []
        for r in rows:
            caps = json.loads(r["capabilities"])
            if capability in caps:
                results.append(dict(r))
        return results

    def deregister_agent(self, agent_id):
        """Remove an agent from the registry."""
        self.conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        self.conn.commit()

    def mark_offline(self, agent_id):
        """Mark agent as offline."""
        self.conn.execute("UPDATE agents SET status = 'offline' WHERE id = ?", (agent_id,))
        self.conn.commit()

    # --- Tasks ---

    def create_task(self, task_id, description, priority=5, parent_task=None):
        """Create a new task."""
        self.conn.execute("""
            INSERT INTO tasks (id, description, status, priority, created_at, parent_task)
            VALUES (?, ?, 'pending', ?, ?, ?)
        """, (task_id, description, priority, time.time(), parent_task))
        self.conn.commit()

    def assign_task(self, task_id, agent_id):
        """Assign a task to an agent."""
        self.conn.execute("UPDATE tasks SET assigned_to = ?, status = 'assigned' WHERE id = ?",
                         (agent_id, task_id))
        self.conn.commit()

    def start_task(self, task_id):
        """Mark task as started."""
        self.conn.execute("UPDATE tasks SET status = 'running', started_at = ? WHERE id = ?",
                         (time.time(), task_id))
        self.conn.commit()

    def complete_task(self, task_id, result):
        """Mark task as completed."""
        self.conn.execute("UPDATE tasks SET status = 'completed', completed_at = ?, result = ? WHERE id = ?",
                         (time.time(), json.dumps(result), task_id))
        self.conn.commit()

    def fail_task(self, task_id, error):
        """Mark task as failed."""
        self.conn.execute("UPDATE tasks SET status = 'failed', completed_at = ?, result = ? WHERE id = ?",
                         (time.time(), json.dumps({"error": error}), task_id))
        self.conn.commit()

    def get_pending_tasks(self, agent_id=None):
        """Get pending/unassigned tasks."""
        if agent_id:
            rows = self.conn.execute("SELECT * FROM tasks WHERE assigned_to = ? AND status IN ('pending', 'assigned')",
                                     (agent_id,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM tasks WHERE status IN ('pending', 'assigned')").fetchall()
        return [dict(r) for r in rows]

    def get_tasks(self, status=None):
        """Get all tasks, optionally filtered by status."""
        if status:
            rows = self.conn.execute("SELECT * FROM tasks WHERE status = ?", (status,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    # --- Messages ---

    def send_message(self, from_agent, to_agent, content):
        """Send a message between agents."""
        self.conn.execute("""
            INSERT INTO messages (from_agent, to_agent, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (from_agent, to_agent, content, time.time()))
        self.conn.commit()

    def get_messages(self, agent_id, unread_only=False):
        """Get messages for an agent."""
        if unread_only:
            rows = self.conn.execute("SELECT * FROM messages WHERE to_agent = ? AND read = 0 ORDER BY timestamp",
                                     (agent_id,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM messages WHERE to_agent = ? ORDER BY timestamp DESC LIMIT 50",
                                     (agent_id,)).fetchall()
        # Mark as read
        self.conn.execute("UPDATE messages SET read = 1 WHERE to_agent = ? AND read = 0", (agent_id,))
        self.conn.commit()
        return [dict(r) for r in rows]

    # --- Transfers ---

    def create_transfer(self, transfer_id, agent_id, source, target):
        """Create a transfer record."""
        self.conn.execute("""
            INSERT INTO transfers (id, agent_id, source_host, target_host, status, started_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
        """, (transfer_id, agent_id, source, target, time.time()))
        self.conn.commit()

    def update_transfer(self, transfer_id, status, error=None, snapshot_path=None):
        """Update transfer status."""
        if status == 'completed':
            self.conn.execute("""
                UPDATE transfers SET status = ?, completed_at = ?, snapshot_path = COALESCE(?, snapshot_path)
                WHERE id = ?
            """, (status, time.time(), snapshot_path, transfer_id))
        elif error:
            self.conn.execute("UPDATE transfers SET status = ?, error = ? WHERE id = ?",
                             (status, error, transfer_id))
        else:
            self.conn.execute("UPDATE transfers SET status = ? WHERE id = ?", (status, transfer_id))
        self.conn.commit()

    def get_transfers(self):
        """Get all transfers."""
        rows = self.conn.execute("SELECT * FROM transfers ORDER BY started_at DESC").fetchall()
        return [dict(r) for r in rows]
