"""
Jubilee Forgiveness Service
A stub implementation for the swarm demo.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import os
import json

app = FastAPI(title="Jubilee Forgiveness Service")


class ForgivenessRequest(BaseModel):
    account_id: str
    amount: Optional[float] = None
    reason: Optional[str] = None


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "jubilee",
        "mode": os.environ.get("JUBILEE_MODE", "default"),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/forgive")
async def forgive_debt(request: ForgivenessRequest):
    """
    Process a debt forgiveness request.
    """
    # Generate event
    event = {
        "event_type": "forgiveness",
        "account_id": request.account_id,
        "amount": request.amount,
        "reason": request.reason,
        "status": "forgiven",
        "timestamp": datetime.utcnow().isoformat(),
        "touch_id": os.environ.get("JUBILEE_TOUCH_ID", "unknown")
    }
    
    # Log to file
    os.makedirs("/app/data", exist_ok=True)
    with open("/app/data/events.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")
    
    return event


@app.get("/events")
async def get_events(limit: int = 10):
    """
    Retrieve recent events.
    """
    events_file = "/app/data/events.jsonl"
    
    if not os.path.exists(events_file):
        return {"events": [], "count": 0}
    
    with open(events_file, "r") as f:
        lines = f.readlines()
    
    events = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    
    return {
        "events": events,
        "count": len(events),
        "total": len(lines)
    }


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Jubilee Forgiveness Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/healthz",
            "forgive": "/forgive (POST)",
            "events": "/events"
        }
    }
