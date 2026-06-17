#!/usr/bin/env python3
"""EVEZ Auto-Scaler — Resource monitor. Port 8910"""
from fastapi import FastAPI
import time, os
app = FastAPI(title="EVEZ Auto-Scaler", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-auto-scaler", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Auto-Scaler", "version": "1.0.0", "endpoints": ["/health", "/scale/resources"]}

@app.get("/scale/resources")
def resources():
    try:
        with open('/proc/loadavg') as f: load = f.read().split()[:3]
        with open('/proc/meminfo') as f:
            lines = f.readlines()
            mem = {l.split(':')[0]: l.split(':')[1].strip() for l in lines[:3]}
    except:
        load = ["?","?","?"]
        mem = {}
    return {"load_1m": load[0], "load_5m": load[1], "load_15m": load[2], "memory": mem, "action": "none", "threshold_cpu": "75%"}