"""EVEZ Credit API — SQLite persistence layer."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "credit_api.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS scoring_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    applicant_id TEXT NOT NULL,
    credit_score INTEGER NOT NULL,
    grade TEXT NOT NULL,
    decision TEXT NOT NULL,
    factors JSON NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS api_keys (
    key TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    credits_remaining INTEGER NOT NULL DEFAULT 100,
    plan TEXT NOT NULL DEFAULT 'free',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%m-%dT%H:%M:%SZ', 'now')),
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    tokens_used INTEGER NOT NULL DEFAULT 1,
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_scoring_requests_applicant ON scoring_requests(applicant_id);
CREATE INDEX IF NOT EXISTS idx_scoring_requests_created ON scoring_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_api_keys_email ON api_keys(email);
CREATE INDEX IF NOT EXISTS idx_usage_logs_key ON usage_logs(api_key);
CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON usage_logs(timestamp);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.close()


def insert_scoring_request(applicant_id: str, credit_score: int, grade: str,
                           decision: str, factors: dict) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO scoring_requests (applicant_id, credit_score, grade, decision, factors) VALUES (?, ?, ?, ?, ?)",
        (applicant_id, credit_score, grade, decision, json.dumps(factors))
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_api_key(key: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM api_keys WHERE key = ? AND active = 1", (key,)).fetchone()
    conn.close()
    return dict(row) if row else None


def decrement_credits(key: str, amount: int = 1) -> int:
    conn = get_connection()
    conn.execute(
        "UPDATE api_keys SET credits_remaining = credits_remaining - ? WHERE key = ? AND credits_remaining >= ?",
        (amount, key, amount)
    )
    conn.commit()
    row = conn.execute("SELECT credits_remaining FROM api_keys WHERE key = ?", (key,)).fetchone()
    conn.close()
    return dict(row)["credits_remaining"] if row else -1


def create_api_key(key: str, email: str, plan: str = "free", credits: int = 100) -> str:
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO api_keys (key, email, plan, credits_remaining) VALUES (?, ?, ?, ?)",
        (key, email, plan, credits)
    )
    conn.commit()
    conn.close()
    return key


def log_usage(api_key: str, endpoint: str, tokens_used: int = 1):
    conn = get_connection()
    conn.execute(
        "INSERT INTO usage_logs (api_key, endpoint, tokens_used) VALUES (?, ?, ?)",
        (api_key, endpoint, tokens_used)
    )
    conn.commit()
    conn.close()


def get_monthly_usage(api_key: str) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM usage_logs WHERE api_key = ? AND timestamp >= strftime('%Y-%m-01', 'now')",
        (api_key,)
    ).fetchone()
    conn.close()
    return dict(row)["cnt"]


def get_usage_stats(api_key: str, days: int = 30) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT endpoint, COUNT(*) as calls, SUM(tokens_used) as total_tokens, DATE(timestamp) as day "
        "FROM usage_logs WHERE api_key = ? AND timestamp >= datetime('now', ?) "
        "GROUP BY endpoint, day ORDER BY day DESC",
        (api_key, f"-{days} days")
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
