#!/usr/bin/python3
"""
EVEZ Profit Engine — Maximum revenue, zero cost, self-sustaining
Every tool is free. Every service earns. No paid providers. Ever.
"""
import os, json, sqlite3, time, hashlib, uuid
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
import requests
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import uvicorn

BASE = Path(os.getenv("PROFIT_BASE", "/home/openclaw/projects/evez-profit"))
DB_PATH = BASE / "profit.db"
PORT = int(os.getenv("PROFIT_PORT", "8911"))

def init_db():
    db = sqlite3.connect(str(DB_PATH))
    db.execute("""CREATE TABLE IF NOT EXISTS revenue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        amount_cents INTEGER,
        customer_email TEXT,
        product TEXT,
        stripe_event_id TEXT,
        timestamp TEXT
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS api_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_key_hash TEXT,
        endpoint TEXT,
        tokens_used INTEGER DEFAULT 0,
        cost_cents INTEGER DEFAULT 0,
        timestamp TEXT
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS cost_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        amount_cents INTEGER,
        description TEXT,
        timestamp TEXT
    )""")
    db.commit()
    return db

DB = init_db()

MONTHLY_COSTS = {"vultr_vps": 600}
FREE_SERVICES = {"groq_cloud": 0, "composio": 0, "github": 0, "gmail": 0, "slack": 0, "caddy_zerossl": 0, "searxng": 0, "fail2ban": 0, "stripe": 0, "psyche_engine": 0}

PRODUCTS = {
    "clawbreak": {"price_cents": 999, "interval": "month", "stripe": "https://buy.stripe.com/7sYfZj4GT1Kf0VNaRs0RG0u"},
    "cognition": {"price_cents": 4999, "interval": "month", "stripe": "https://buy.stripe.com/14A6oJ1uHbkPeMD0cO0RG0v"},
    "factory": {"price_cents": 9999, "interval": "month", "stripe": "https://buy.stripe.com/bJe14pa1d9cH47Ze3E0RG0t"},
    "research": {"price_cents": 1999, "interval": "month", "stripe": "https://buy.stripe.com/fZu28t7T5coTgUL4t40RG0w"},
    "mesh": {"price_cents": 2500, "interval": "month", "stripe": "https://buy.stripe.com/6oUcN7ehtagL1ZRbVw0RG0x"},
    "bridge": {"price_cents": 500, "interval": "once", "stripe": "https://buy.stripe.com/3cIeVfa1d2Oj0VNaRs0RG0s"},
    "psyche_engine": {"price_cents": 1499, "interval": "month"},
    "federation": {"price_cents": 999, "interval": "month"},
    "threat_hunter": {"price_cents": 2999, "interval": "month"},
    "mega_api": {"price_cents": 24999, "interval": "month"},
}

def get_monthly_cost():
    return sum(MONTHLY_COSTS.values())

def get_potential_mrr():
    total = 0
    for p in PRODUCTS.values():
        if p["interval"] == "month":
            total += p["price_cents"]
    return total

def get_break_even():
    cost = get_monthly_cost()
    cheapest = min(p["price_cents"] for p in PRODUCTS.values() if p["interval"] == "month")
    return cost / cheapest

app = FastAPI(title="EVEZ Profit Engine", version="1.0.0")

@app.get("/")
async def root():
    cost = get_monthly_cost()
    mrr = get_potential_mrr()
    return {
        "service": "EVEZ Profit Engine",
        "philosophy": "Every tool free. Every service earns. No paid providers. Ever.",
        "monthly_cost_cents": cost,
        "monthly_cost_display": f"${cost/100:.2f}",
        "potential_mrr_cents": mrr,
        "potential_mrr_display": f"${mrr/100:.2f}/mo",
        "net_if_full_adoption": f"${(mrr - cost)/100:.2f}/mo",
        "break_even": f"{get_break_even():.1f} subscribers on cheapest plan",
        "products": len(PRODUCTS),
        "free_services": len(FREE_SERVICES),
        "cost_breakdown": {
            "paid": {k: f"${v/100:.2f}" for k, v in MONTHLY_COSTS.items()},
            "free": list(FREE_SERVICES.keys()),
        },
        "zero_cost_stack": [
            "Vultr Inference (GLM-5.1-FP8) — included with VPS",
            "Groq Cloud — free tier, unlimited inference",
            "Composio — free tier, 1000 tool calls/mo",
            "Psyche Engine — pure numpy math, zero APIs",
            "SearXNG — self-hosted search",
            "GitHub — free org tier",
            "Caddy + ZeroSSL — free HTTPS",
            "fail2ban — self-hosted security",
            "Stripe — pays from revenue (2.9% + 30c per transaction)",
        ]
    }

@app.get("/products")
async def products():
    result = {}
    for pid, p in PRODUCTS.items():
        result[pid] = {
            "price": f"${p['price_cents']/100:.2f}",
            "interval": p["interval"],
            "stripe_link": p.get("stripe"),
        }
    return result

@app.get("/pnl")
async def pnl():
    total_revenue = DB.execute("SELECT COALESCE(SUM(amount_cents), 0) FROM revenue").fetchone()[0]
    total_cost = get_monthly_cost()
    net = total_revenue - total_cost
    return {
        "revenue_cents": total_revenue,
        "revenue_display": f"${total_revenue/100:.2f}",
        "monthly_cost_cents": total_cost,
        "monthly_cost_display": f"${total_cost/100:.2f}",
        "net_cents": net,
        "net_display": f"${net/100:.2f}",
        "status": "PROFITABLE" if net > 0 else "INVESTING",
    }

@app.get("/forecast")
async def forecast(subscribers: int = 1, product: str = "clawbreak"):
    p = PRODUCTS.get(product, PRODUCTS["clawbreak"])
    monthly_rev = p["price_cents"] * subscribers
    monthly_cost = get_monthly_cost()
    net = monthly_rev - monthly_cost
    return {
        "product": product,
        "subscribers": subscribers,
        "monthly_revenue": f"${monthly_rev/100:.2f}",
        "monthly_cost": f"${monthly_cost/100:.2f}",
        "monthly_profit": f"${net/100:.2f}",
        "annual_profit": f"${net*12/100:.2f}",
    }

@app.get("/investor")
async def investor_deck():
    cost = get_monthly_cost()
    mrr = get_potential_mrr()
    return {
        "pitch": "EVEZ-OS: 20+ API services, $6/mo cost, zero paid providers",
        "competitive_moat": "Pure math audio, free-tier AI, self-hosted everything",
        "monthly_burn": f"${cost/100:.2f}",
        "max_mrr": f"${mrr/100:.2f}",
        "margin_at_scale": f"{(1 - cost/mrr)*100:.0f}%",
        "tech_stack_cost": "$0 in API fees",
        "raising": "Pre-seed $50K-250K for Oracle Cloud GPU + marketing",
        "traction": "20 services, 83 repos, 6 Stripe products, live since 2026-05-22",
    }

if __name__ == "__main__":
    print(f"EVEZ Profit Engine on port {PORT}")
    uvicorn.run(app, host="127.0.0.1", port=PORT)
