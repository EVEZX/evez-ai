#!/usr/bin/env python3
"""EVEZ Witness — Compliance and policy enforcement for EVEZ agents"""
import json, time, sqlite3, logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI
import yaml

app = FastAPI(title="EVEZ Witness", version="1.0.0")

class Violation(BaseModel):
    agent_id: str
    rule_id: str
    details: str
    severity: str
    timestamp: float = time.time()

class AuditEntry(BaseModel):
    agent_id: str
    total_violations: int
    critical: int
    high: int
    medium: int
    low: int

DB_PATH = "evez-witness.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS violations (id INTEGER PRIMARY KEY, agent_id TEXT, rule_id TEXT, details TEXT, severity TEXT, ts REAL)")
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok", "service": "evez-witness", "ts": int(time.time())}

@app.post("/report")
def report_violation(violation: Violation):
    conn = get_db()
    conn.execute("INSERT INTO violations (agent_id, rule_id, details, severity, ts) VALUES (?, ?, ?, ?, ?)", (violation.agent_id, violation.rule_id, violation.details, violation.severity, time.time()))
    conn.commit()
    return {"status": "logged", "agent_id": violation.agent_id}

@app.get("/violations")
def get_violations(agent_id: Optional[str] = None, limit: int = 50):
    conn = get_db()
    if agent_id:
        rows = conn.execute("SELECT * FROM violations WHERE agent_id = ? ORDER BY ts DESC LIMIT ?", (agent_id, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM violations ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]

@app.get("/audit")
def get_audit():
    rows = get_db().execute("SELECT agent_id, COUNT(*) as total, SUM(CASE WHEN severity='critical' THEN 1 ELSE 0 END) as critical, SUM(CASE WHEN severity='high' THEN 1 ELSE 0 END) as high, SUM(CASE WHEN severity='medium' THEN 1 ELSE 0 END) as medium, SUM(CASE WHEN severity='low' THEN 1 ELSE 0 END) as low FROM violations GROUP BY agent_id").fetchall()
    return [AuditEntry(agent_id=r["agent_id"], total_violations=r["total"], critical=r["critical"], high=r["high"], medium=r["medium"], low=r["low"]) for r in rows]
