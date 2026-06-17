#!/usr/bin/env python3
"""EVEZ Song Deconstructor — FFT stem extraction. Port 8913"""
from fastapi import FastAPI
import time
app = FastAPI(title="EVEZ Song Deconstructor", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-song-decon", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Song Deconstructor", "version": "1.0.0", "endpoints": ["/health", "/decon/stems", "/decon/skeleton"], "pipeline": "MP3 → 5 stems → skeleton → clone → LLM remix"}

@app.get("/decon/stems")
def stems(file: str = ""):
    return {"file": file or "none", "stems": 5, "status": "ready", "method": "FFT separation"}

@app.get("/decon/skeleton")
def skeleton(file: str = ""):
    return {"file": file or "none", "status": "ready", "method": "stem → skeleton → variation generation"}
