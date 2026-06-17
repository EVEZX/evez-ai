#!/usr/bin/env python3
"""EVEZ Profit — P&L tracking. Port 8910"""
from fastapi import FastAPI
import time
app = FastAPI(title="EVEZ Profit Engine", version="1.0.0")

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-profit", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Profit Engine", "version": "1.0.0", "endpoints": ["/health", "/profit/summary", "/profit/by-product"]}

@app.get("/profit/summary")
def summary():
    return {"cost_monthly": 6.00, "revenue_monthly": 0, "subscribers": 0, "mrr_potential": 179.96, "breakeven": "1 subscriber at $6/mo"}

@app.get("/profit/by-product")
def by_product():
    return {"products": [], "note": "No revenue yet — Phase 1 is getting the first customer"}
