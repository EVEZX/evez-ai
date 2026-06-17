#!/usr/bin/env python3
"""
EVEZ Federation Bridge
Connects multiple OpenClaw gateways into a self-healing mesh.
Main (18789) ↔ Rescue (19789) — if main dies, rescue takes over.
Future: Vultr ↔ Oracle ↔ Google ↔ AWS — cross-cloud federation.
"""
import os, json, time, sqlite3, hashlib, uuid, threading
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

BASE = Path(os.getenv("EVZ_FED_BASE", "/home/openclaw/projects/evez-federation"))
DB_PATH = BASE / "federation.db"

# ─── Known Gateways ──────────────────────────────────────────────
GATEWAYS = {
    "vultr_main": {
        "url": "http://localhost:18789",
        "profile": "default",
        "role": "primary",
        "region": "lax",
        "services": 19,
    },
    "vultr_rescue": {
        "url": "http://localhost:19789",
        "profile": "rescue",
        "role": "failover",
        "region": "lax",
        "services": 0,  # No EVEZ services, just gateway
    },
    # Future gateways (will be registered as they come online)
    "oracle_alpha": {
        "url": "http://10.0.0.1:18789",
        "profile": "default",
        "role": "compute",
        "region": "phx",
        "services": 0,
    },
    "google_scout": {
        "url": "http://10.0.1.1:18789",
        "profile": "default",
        "role": "scout",
        "region": "us-central1",
        "services": 0,
    },
}

def init_db():
    db = sqlite3.connect(str(DB_PATH))
    db.execute("""CREATE TABLE IF NOT EXISTS gateways (
        id TEXT PRIMARY KEY,
        url TEXT,
        profile TEXT,
        role TEXT,
        region TEXT,
        status TEXT DEFAULT 'unknown',
        last_heartbeat TEXT,
        services_count INTEGER DEFAULT 0,
        config_hash TEXT,
        metadata TEXT
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS heartbeat_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gateway_id TEXT,
        status TEXT,
        latency_ms INTEGER,
        services_up INTEGER,
        timestamp TEXT
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS sync_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_gateway TEXT,
        event_type TEXT,
        payload TEXT,
        synced_to TEXT,
        timestamp TEXT
    )""")
    db.commit()
    return db

DB = init_db()

# ─── Health Checker ───────────────────────────────────────────────
def check_gateway(gw_id, gw_info):
    """Health check a single gateway."""
    try:
        start = time.time()
        r = requests.get(f"{gw_info['url']}/", timeout=5)
        latency = int((time.time() - start) * 1000)
        if r.ok:
            return {"id": gw_id, "status": "healthy", "latency_ms": latency, "http_code": r.status_code}
        return {"id": gw_id, "status": "degraded", "latency_ms": latency, "http_code": r.status_code}
    except requests.exceptions.ConnectionError:
        return {"id": gw_id, "status": "down", "latency_ms": -1, "http_code": 0}
    except Exception as e:
        return {"id": gw_id, "status": "error", "latency_ms": -1, "error": str(e)}

def check_all_gateways():
    results = {}
    for gw_id, gw_info in GATEWAYS.items():
        if gw_info["url"].startswith("http://10."):  # Future gateways
            results[gw_id] = {"id": gw_id, "status": "pending", "note": "Not deployed yet"}
            continue
        results[gw_id] = check_gateway(gw_id, gw_info)
        # Store in DB
        DB.execute(
            "INSERT INTO heartbeat_log (gateway_id, status, latency_ms, services_up, timestamp) VALUES (?,?,?,?,?)",
            (gw_id, results[gw_id]["status"], results[gw_id].get("latency_ms", -1), 0, datetime.now(timezone.utc).isoformat())
        )
    DB.commit()
    return results

# ─── Failover Logic ───────────────────────────────────────────────
def get_active_gateway():
    """Return the URL of the best available gateway."""
    for gw_id, gw_info in GATEWAYS.items():
        health = check_gateway(gw_id, gw_info)
        if health["status"] in ("healthy", "degraded") and gw_info["role"] in ("primary", "failover"):
            return {"id": gw_id, "url": gw_info["url"], "status": health["status"]}
    return None

def promote_failover():
    """If primary is down, promote the failover gateway."""
    primary = GATEWAYS.get("vultr_main", {})
    rescue = GATEWAYS.get("vultr_rescue", {})
    
    primary_health = check_gateway("vultr_main", primary)
    
    if primary_health["status"] == "down":
        rescue_health = check_gateway("vultr_rescue", rescue)
        if rescue_health["status"] in ("healthy", "degraded"):
            # Rescue is up — it's the active gateway
            return {
                "action": "failover_active",
                "primary_status": "down",
                "active_gateway": "vultr_rescue",
                "active_url": rescue["url"],
                "message": "Primary gateway is DOWN. Rescue gateway is handling requests."
            }
        return {
            "action": "critical",
            "primary_status": "down",
            "rescue_status": rescue_health["status"],
            "message": "BOTH gateways are down. Manual intervention required."
        }
    
    return {
        "action": "normal",
        "primary_status": primary_health["status"],
        "active_gateway": "vultr_main",
        "active_url": primary["url"],
    }

# ─── FastAPI ──────────────────────────────────────────────────────
app = FastAPI(title="EVEZ Federation Bridge", version="1.0.0")

@app.get("/")
async def root():
    return {
        "service": "EVEZ Federation Bridge",
        "gateways": len(GATEWAYS),
        "status": promote_failover(),
    }

@app.get("/health")
async def health():
    return {"gateways": check_all_gateways()}

@app.get("/active")
async def active():
    gw = get_active_gateway()
    if gw:
        return gw
    raise HTTPException(503, "No healthy gateways available")

@app.get("/failover")
async def failover():
    return promote_failover()

@app.post("/register")
async def register_gateway(id: str, url: str, role: str = "compute", region: str = "unknown"):
    GATEWAYS[id] = {"url": url, "profile": "default", "role": role, "region": region, "services": 0}
    DB.execute(
        "INSERT OR REPLACE INTO gateways (id, url, profile, role, region, status, last_heartbeat) VALUES (?,?,?,?,?,?,?)",
        (id, url, "default", role, region, "registered", datetime.now(timezone.utc).isoformat())
    )
    DB.commit()
    return {"registered": id, "url": url, "role": role}

@app.get("/sync")
async def sync_status():
    events = DB.execute("SELECT COUNT(*) FROM sync_events").fetchone()[0]
    return {"total_sync_events": events, "gateways": list(GATEWAYS.keys())}

if __name__ == "__main__":
    port = int(os.getenv("FED_PORT", "8909"))
    print(f"🔗 EVEZ Federation Bridge on port {port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
