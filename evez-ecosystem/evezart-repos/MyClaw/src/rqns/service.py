"""
RQNS v2 Service — FastAPI endpoint for the quantum sentinel
"""
from fastapi import APIRouter
from rqns.orchestrator import ConcreteRQNSPipeline
from rqns.core.interfaces import AnomalySignal
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import time

router = APIRouter(prefix="/rqns", tags=["RQNS v2"])

_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = ConcreteRQNSPipeline()
    return _pipeline

class ProcessRequest(BaseModel):
    raw_data: Optional[List[float]] = None

@router.get("/status")
async def rqns_status():
    p = get_pipeline()
    return {
        "version": "2.0",
        "spine_events": len(p.spine.events),
        "total_spikes": p.sensor.total_spikes,
        "learning": p.patcher.cumulative_learning,
        "steering": p.steering.state(),
    }

@router.post("/process")
async def rqns_process(req: ProcessRequest = None):
    p = get_pipeline()
    data = req.raw_data if req and req.raw_data else np.random.exponential(0.15, 50).tolist()
    signal = AnomalySignal(source_id=f"api_{int(time.time())}", raw_data=data)
    return p.process_signal(signal)

@router.post("/inject")
async def rqns_inject(anomaly: bool = False):
    p = get_pipeline()
    raw = np.random.exponential(0.15, 50).tolist()
    if anomaly:
        raw[8:18] = [x + np.random.uniform(1.2, 2.8) for x in raw[8:18]]
    signal = AnomalySignal(source_id=f"inject_{int(time.time())}", raw_data=raw)
    return p.process_signal(signal)

@router.get("/spine")
async def rqns_spine(domain: str = None, limit: int = 20):
    p = get_pipeline()
    events = p.spine.replay(domain)
    return {
        "total": len(events),
        "events": [
            {"id": e.event_id, "type": e.event_type, "domain": e.domain, 
             "timestamp": e.timestamp, "data": e.data}
            for e in events[-limit:]
        ]
    }
