#!/usr/bin/env python3
"""EVEZ Vault — Revenue and cost tracking for the EVEZ ecosystem"""
import json, time, sqlite3, logging
from typing import List
from pydantic import BaseModel
from fastapi import FastAPI
import yaml

app = FastAPI(title="EVEZ Vault", version="1.0.0")

class CostEntry(BaseModel):
    service: str
    count: int
    total_cost: float

class CostReport(BaseModel):
    services: List[CostEntry]
    grand_total: float
    currency: str = "USD"

DB_PATH = "evez-vault.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS costs (id INTEGER PRIMARY KEY, service TEXT, count INTEGER DEFAULT 0, cost_per_unit REAL, category TEXT, ts REAL)")
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok", "service": "evez-vault", "ts": int(time.time())}

@app.get("/costs")
def get_costs():
    return [dict(r) for r in get_db().execute("SELECT * FROM costs").fetchall()]

@app.get("/services")
def get_services():
    return [dict(r) for r in get_db().execute("SELECT DISTINCT service, cost_per_unit, category FROM costs").fetchall()]

@app.get("/report")
def get_report():
    rows = get_db().execute("SELECT service, SUM(count) as total_count, cost_per_unit, SUM(count * cost_per_unit) as total_cost FROM costs GROUP BY service").fetchall()
    entries = [CostEntry(service=r["service"], count=r["total_count"], total_cost=round(r["total_cost"], 4)) for r in rows]
    return CostReport(services=entries, grand_total=round(sum(e.total_cost for e in entries), 4))

@app.post("/track")
def track_cost(service: str, cost_per_unit: float = 0.0, count: int = 1, category: str = "general"):
    conn = get_db()
    conn.execute("INSERT INTO costs (service, count, cost_per_unit, category, ts) VALUES (?, ?, ?, ?, ?)", (service, count, cost_per_unit, category, time.time()))
    conn.commit()
    return {"status": "tracked", "service": service, "cost": cost_per_unit * count}
