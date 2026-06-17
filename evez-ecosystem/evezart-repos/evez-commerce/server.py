#!/usr/bin/env python3
"""EVEZ Commerce — Product catalog + Stripe. Port 8904"""
from fastapi import FastAPI
import time
app = FastAPI(title="EVEZ Commerce", version="1.0.0")

PRODUCTS = [
    {"id": "clawbreak-api", "name": "ClawBreak API Access", "price": 29.99, "interval": "month"},
    {"id": "cognition-api", "name": "Cognition API Access", "price": 49.99, "interval": "month"},
    {"id": "research-agent", "name": "Research Agent", "price": 19.99, "interval": "month"},
    {"id": "digital-twin", "name": "Digital Twin Access", "price": 39.99, "interval": "month"},
    {"id": "mesh-network", "name": "Mesh Network Seat", "price": 25.00, "interval": "month"},
    {"id": "guard-security", "name": "Guard Security Monitor", "price": 14.99, "interval": "month"},
]

@app.get("/health")
def health(): return {"status": "ok", "version": "1.0.0", "service": "evez-commerce", "ts": int(time.time())}

@app.get("/")
def root(): return {"service": "EVEZ Commerce", "version": "1.0.0", "endpoints": ["/health", "/products", "/products/{id}"]}

@app.get("/products")
def products():
    return {"products": PRODUCTS, "count": len(PRODUCTS), "mrr_potential": sum(p["price"] for p in PRODUCTS)}

@app.get("/products/{product_id}")
def product(product_id: str):
    p = next((p for p in PRODUCTS if p["id"] == product_id), None)
    return p or {"error": "not found"}