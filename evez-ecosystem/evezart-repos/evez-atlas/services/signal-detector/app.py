"""app.py — FastAPI service for EVEZ signal-detector

Endpoints:
  POST /detect          — run detect_B on a single value
  POST /ingest/signal   — normalize + detect_B with metadata
  GET  /health          — health check
  GET  /state           — current detector state

Canonical reference: docs/architecture/EVEZ_IMPL.md
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import time

from detect_b import DetectB, DetectorConfig

app = FastAPI(
    title="EVEZ Signal Detector",
    description="detect_B signal detection service. The hyperloop fire condition poly_c >= 0.500 is detect_B with fixed_threshold=0.500.",
    version="1.0.0",
)

# Default detector instance (adaptive mode)
_detector = DetectB()
# Hyperloop detector instance (fixed threshold mode)
_hyperloop_detector = DetectB(DetectorConfig.hyperloop_fire())


class DetectRequest(BaseModel):
    value: float = Field(..., description="Normalized signal value (e.g. poly_c)")
    timestamp_ms: Optional[float] = Field(None, description="Unix timestamp ms (default: now)")
    dt_ms: float = Field(16.67, description="Time since last sample in ms")
    mode: str = Field("adaptive", description="'adaptive' or 'hyperloop'")


class IngestSignalRequest(BaseModel):
    source: str = Field(..., description="Source identifier (e.g. 'hyperloop', 'media-ingest')")
    channel: str = Field("classical", description="Channel name")
    raw_value: float = Field(..., description="Raw signal value")
    session_id: Optional[str] = Field(None)
    round: Optional[int] = Field(None, description="Hyperloop round number if applicable")
    timestamp_ms: Optional[float] = Field(None)
    dt_ms: float = Field(16.67)
    mode: str = Field("adaptive", description="'adaptive' or 'hyperloop'")


@app.get("/health")
def health():
    return {"ok": True, "service": "signal-detector", "version": "1.0.0"}


@app.get("/state")
def state():
    return {
        "ok": True,
        "adaptive": {
            "sample_count": _detector._sample_count,
            "fire_count": _detector._fire_count,
            "baseline_mean": _detector.baseline_mean,
            "baseline_std": _detector.baseline_std,
            "peak_threshold": _detector.peak_threshold(),
            "last_fire_ms": _detector._last_fire_ms,
        },
        "hyperloop": {
            "sample_count": _hyperloop_detector._sample_count,
            "fire_count": _hyperloop_detector._fire_count,
            "peak_threshold": _hyperloop_detector.peak_threshold(),
            "last_fire_ms": _hyperloop_detector._last_fire_ms,
        },
    }


@app.post("/detect")
def detect(req: DetectRequest):
    ts = req.timestamp_ms or (time.time() * 1000)
    detector = _hyperloop_detector if req.mode == "hyperloop" else _detector
    result = detector.process(req.value, ts, req.dt_ms)
    return {"ok": True, "data": result, "latency_ms": 0}


@app.post("/ingest/signal")
def ingest_signal(req: IngestSignalRequest):
    ts = req.timestamp_ms or (time.time() * 1000)
    detector = _hyperloop_detector if req.mode == "hyperloop" else _detector
    result = detector.process(req.raw_value, ts, req.dt_ms)
    result["source"] = req.source
    result["channel"] = req.channel
    if req.session_id:
        result["session_id"] = req.session_id
    if req.round is not None:
        result["round"] = req.round
    return {
        "ok": True,
        "data": result,
        "request_id": f"req_{result['id']}",
    }


@app.post("/reset")
def reset(mode: str = "adaptive"):
    """Reset detector state. Use between independent signal streams."""
    if mode == "hyperloop":
        _hyperloop_detector.reset()
    else:
        _detector.reset()
    return {"ok": True, "reset": mode}
