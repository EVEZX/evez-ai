#!/usr/bin/env python3
"""EVEZ Game — Desert Survival + game engine. Port 8914"""
from fastapi import FastAPI
import time
app = FastAPI(title="EVEZ Game Engine", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-game", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Game Engine", "version": "1.0.0", "endpoints": ["/health", "/game/status", "/game/desert"]}

@app.get("/game/status")
def game_status():
    return {"engine": "ready", "games": ["desert-survival"]}

@app.get("/game/desert")
def desert():
    return {"day": 1, "player": {"hp": 100, "sanity": 85, "cash": 47.50}, "pablo_morale": 90, "car_gas": 3.2, "temp_f": -56, "lake_mead_ft": 1041.9}