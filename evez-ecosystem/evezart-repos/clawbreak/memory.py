"""ClawBreak - Persistent memory with full-text search."""
import sqlite3
import json
import time
from pathlib import Path

class Memory:
    def __init__(self, db_path="data/clawbreak.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                session_id TEXT DEFAULT 'default',
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                timestamp REAL NOT NULL,
                access_count INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_facts_key ON facts(key);

            CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
                key, value, category,
                content=facts, content_rowid=id
            );

            CREATE TRIGGER IF NOT EXISTS facts_ai AFTER INSERT ON facts BEGIN
                INSERT INTO facts_fts(rowid, key, value, category)
                VALUES (new.id, new.key, new.value, new.category);
            END;

            CREATE TRIGGER IF NOT EXISTS facts_ad AFTER DELETE ON facts BEGIN
                INSERT INTO facts_fts(facts_fts, rowid, key, value, category)
                VALUES ('delete', old.id, old.key, old.value, old.category);
            END;

            CREATE TRIGGER IF NOT EXISTS facts_au AFTER UPDATE ON facts BEGIN
                INSERT INTO facts_fts(facts_fts, rowid, key, value, category)
                VALUES ('delete', old.id, old.key, old.value, old.category);
                INSERT INTO facts_fts(rowid, key, value, category)
                VALUES (new.id, new.key, new.value, new.category);
            END;
        """)
        self.conn.commit()

    def store_message(self, role, content, session_id="default", metadata=None):
        self.conn.execute(
            "INSERT INTO messages (role, content, timestamp, session_id, metadata) VALUES (?, ?, ?, ?, ?)",
            (role, content, time.time(), session_id, json.dumps(metadata or {}))
        )
        self.conn.commit()

    def get_messages(self, session_id="default", limit=20):
        rows = self.conn.execute(
            "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit)
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def store_fact(self, key, value, category="general"):
        self.conn.execute(
            """INSERT INTO facts (key, value, category, timestamp, access_count)
               VALUES (?, ?, ?, ?, 0)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, category=excluded.category, timestamp=excluded.timestamp""",
            (key, value, category, time.time())
        )
        self.conn.commit()

    def recall_facts(self, query, limit=5):
        rows = self.conn.execute(
            """SELECT f.key, f.value, f.category, f.access_count, rank
               FROM facts_fts ft JOIN facts f ON ft.rowid = f.id
               WHERE facts_fts MATCH ?
               ORDER BY rank LIMIT ?""",
            (query, limit)
        ).fetchall()
        # Increment access count
        for r in rows:
            self.conn.execute("UPDATE facts SET access_count = access_count + 1 WHERE key = ?", (r["key"],))
        self.conn.commit()
        return [{"key": r["key"], "value": r["value"], "category": r["category"]} for r in rows]

    def list_facts(self, category=None, limit=50):
        if category:
            rows = self.conn.execute(
                "SELECT key, value, category, access_count FROM facts WHERE category = ? ORDER BY timestamp DESC LIMIT ?",
                (category, limit)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT key, value, category, access_count FROM facts ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [{"key": r["key"], "value": r["value"], "category": r["category"], "access_count": r["access_count"]} for r in rows]

    def delete_fact(self, key):
        self.conn.execute("DELETE FROM facts WHERE key = ?", (key,))
        self.conn.commit()

    def cleanup_old_messages(self, session_id="default", keep=100):
        self.conn.execute(
            """DELETE FROM messages WHERE session_id = ? AND id NOT IN (
               SELECT id FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?
            )""",
            (session_id, session_id, keep)
        )
        self.conn.commit()
