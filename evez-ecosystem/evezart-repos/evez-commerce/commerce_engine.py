#!/usr/bin/env python3
"""
EVEZ Commerce Engine — Full Monetization Stack
Every service becomes a billable API. Every user becomes a customer.
"""
import os, json, time, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
import requests
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import uvicorn

BASE = Path(os.getenv("COMMERCE_BASE", "/home/openclaw/projects/evez-commerce"))
DB_PATH = BASE / "commerce.db"
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ─── Service Catalog ──────────────────────────────────────────────
SERVICES = {
    "clawbreak": {
        "name": "ClawBreak AI Chat",
        "price_monthly": 999, "price_annual": 9999,
        "free_tier": 50, "rate_limit": 1000, "port": 8080,
        "description": "AI chat with FSC doctrine. Reflexive, adversarial, compression-native.",
        "category": "ai-chat",
    },
    "cognition": {
        "name": "Cognition Forensics",
        "price_monthly": 4999, "price_annual": 49999,
        "free_tier": 10, "rate_limit": 500, "port": 8081,
        "description": "AI output auditing. Fraud detection, hallucination scoring, chain-of-thought forensics.",
        "category": "forensics",
    },
    "factory": {
        "name": "Factory AI — Code Generation",
        "price_monthly": 9999, "price_annual": 99999,
        "free_tier": 3, "rate_limit": 100, "port": 8891,
        "description": "Autonomous code generation, auditing, and GitHub shipping. Self-manufacturing pipeline.",
        "category": "manufacturing",
    },
    "research": {
        "name": "Auto-Research & Math Audit",
        "price_monthly": 1999, "price_annual": 19999,
        "free_tier": 5, "rate_limit": 200, "port": 8892,
        "description": "Academic research automation. Math auditing, fact-checking, paper generation.",
        "category": "research",
    },
    "mesh": {
        "name": "Mesh Network Intelligence",
        "price_monthly": 2500, "price_annual": 25000,
        "free_tier": 5, "rate_limit": 200, "port": 8899,
        "description": "Self-healing mesh. Desert-hardened. AI diagnostics. Thermal management.",
        "category": "infrastructure",
    },
    "breakcore": {
        "name": "404 Breakcore Engine",
        "price_monthly": 1499, "price_annual": 14999,
        "free_tier": 100, "rate_limit": 10000, "port": 8896,
        "description": "Generative breakcore at 174 BPM. Amen break synthesis. Real-time remix. Streaming-ready.",
        "category": "media",
    },
    "pte": {
        "name": "Phenomenologic Topology Engine",
        "price_monthly": 2999, "price_annual": 29999,
        "free_tier": 20, "rate_limit": 500, "port": 8901,
        "description": "7-node phenomenologic manifold. Action routing through experiential basins. For agents that think.",
        "category": "ai-infrastructure",
    },
    "assembler": {
        "name": "Auto-Assembler for Hidden Forms",
        "price_monthly": 3999, "price_annual": 39999,
        "free_tier": 5, "rate_limit": 100, "port": 8903,
        "description": "Shuffle -> Inscribe -> Harpoon. Discovers new forms by interleaving manifests.",
        "category": "ai-infrastructure",
    },
    "mega_api_pro": {
        "name": "EVEZ Mega API - Pro",
        "price_monthly": 4999, "price_annual": 49999,
        "free_tier": 100, "rate_limit": 10000, "port": 0,
        "description": "ALL 8 services, 1 API key. 10K requests/day. Full FSC doctrine stack.",
        "category": "bundle",
    },
    "mega_api_enterprise": {
        "name": "EVEZ Mega API - Enterprise",
        "price_monthly": 24999, "price_annual": 249999,
        "free_tier": 0, "rate_limit": 1000000, "port": 0,
        "description": "Unlimited. 99.9% SLA. Priority. Custom integrations. On-prem available.",
        "category": "bundle",
    },
}

# ─── Database ──────────────────────────────────────────────────────
def init_db():
    db = sqlite3.connect(str(DB_PATH))
    db.execute("""CREATE TABLE IF NOT EXISTS api_keys (
        key TEXT PRIMARY KEY,
        email TEXT,
        plan TEXT DEFAULT 'free',
        stripe_customer_id TEXT,
        stripe_subscription_id TEXT,
        created_at TEXT,
        requests_today INTEGER DEFAULT 0,
        request_count INTEGER DEFAULT 0,
        last_reset TEXT,
        active INTEGER DEFAULT 1
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS usage_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_key TEXT,
        service TEXT,
        endpoint TEXT,
        tokens_used INTEGER DEFAULT 0,
        latency_ms INTEGER DEFAULT 0,
        timestamp TEXT,
        ip_address TEXT
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS revenue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        amount_cents INTEGER,
        currency TEXT DEFAULT 'usd',
        stripe_payment_id TEXT,
        description TEXT,
        timestamp TEXT
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        company TEXT,
        interest TEXT,
        source TEXT,
        notes TEXT,
        contacted INTEGER DEFAULT 0,
        converted INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    db.commit()
    return db

DB = init_db()

# ─── API Key System ───────────────────────────────────────────────
def generate_api_key(plan="free"):
    key = f"evez_{plan}_{uuid.uuid4().hex[:24]}"
    return key

def validate_key(api_key: str):
    row = DB.execute("SELECT * FROM api_keys WHERE key = ? AND active = 1", (api_key,)).fetchone()
    if not row:
        return None
    plan = row[2]
    requests_today = row[6]
    last_reset = row[8] or ""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if last_reset != today:
        DB.execute("UPDATE api_keys SET requests_today = 0, last_reset = ? WHERE key = ?", (today, api_key))
        DB.commit()
        requests_today = 0
    if plan == "free":
        limit = 50
    elif plan == "pro":
        limit = 10000
    elif plan == "enterprise":
        limit = 1000000
    else:
        limit = SERVICES.get(plan, {}).get("rate_limit", 1000)
    if requests_today >= limit:
        return {"valid": False, "reason": "rate_limited", "plan": plan, "requests_today": requests_today, "limit": limit}
    DB.execute("UPDATE api_keys SET requests_today = requests_today + 1, request_count = request_count + 1 WHERE key = ?", (api_key,))
    DB.commit()
    return {"valid": True, "plan": plan, "email": row[1], "requests_today": requests_today + 1, "limit": limit}

def log_usage(api_key, service, endpoint, tokens=0, latency=0, ip=""):
    DB.execute(
        "INSERT INTO usage_log (api_key, service, endpoint, tokens_used, latency_ms, timestamp, ip_address) VALUES (?,?,?,?,?,?,?)",
        (api_key, service, endpoint, tokens, latency, datetime.now(timezone.utc).isoformat(), ip)
    )
    DB.commit()

# ─── FastAPI ──────────────────────────────────────────────────────
app = FastAPI(title="EVEZ Commerce Engine", version="1.0.0")

class RegisterRequest(BaseModel):
    email: str
    plan: str = "free"
    company: Optional[str] = None

class LeadRequest(BaseModel):
    email: str
    company: Optional[str] = None
    interest: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None

class ProxyRequest(BaseModel):
    service: str
    endpoint: str
    method: str = "GET"
    body: Optional[dict] = None

@app.get("/")
async def index():
    return {
        "service": "EVEZ Commerce Engine",
        "version": "1.0.0",
        "services": len(SERVICES),
        "total_mrr_potential": f"${sum(s['price_monthly'] for s in SERVICES.values())//100:,}/mo (1 sub each)",
    }

@app.get("/catalog")
async def catalog():
    return {
        "services": {
            k: {
                "name": v["name"],
                "price_monthly": f"${v['price_monthly']//100}/mo",
                "price_annual": f"${v['price_annual']//100}/yr",
                "free_tier": f"{v['free_tier']} req/day",
                "category": v["category"],
                "description": v["description"],
            } for k, v in SERVICES.items()
        },
        "bundles": {
            "mega_pro": {"name": "EVEZ Mega API - Pro", "price": "$49.99/mo", "includes": "ALL services, 10K req/day", "savings": "60% vs individual"},
            "mega_enterprise": {"name": "EVEZ Mega API - Enterprise", "price": "$249.99/mo", "includes": "ALL services, unlimited, SLA, priority", "savings": "Best value"},
        }
    }

@app.post("/register")
async def register(req: RegisterRequest):
    # Route through Guard for abuse prevention
    try:
        guard_signup = requests.post("http://localhost:8907/signup", json={
            "email": req.email, "fingerprint": ""
        }, timeout=5)
        if guard_signup.ok:
            return guard_signup.json()
        # If guard rejected, fall through
    except:
        pass
    # Fallback: local registration (guard unavailable)
    key = generate_api_key(req.plan)
    DB.execute(
        "INSERT INTO api_keys (key, email, plan, created_at, last_reset) VALUES (?,?,?,?,?)",
        (key, req.email, req.plan, datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    )
    DB.commit()
    return {
        "api_key": key,
        "plan": req.plan,
        "rate_limit": f"{SERVICES.get(req.plan, {}).get('rate_limit', 50) if req.plan in SERVICES else 50} req/day",
        "message": "Welcome to EVEZ. Your API key is ready. Start building.",
    }

@app.get("/validate/{api_key}")
async def validate(api_key: str):
    result = validate_key(api_key)
    if not result:
        raise HTTPException(401, "Invalid API key")
    return result

@app.post("/proxy")
async def proxy(req: ProxyRequest, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "API key required")
    api_key = authorization.split(" ")[1]
    
    # Gate 1: Guard engine — anti-abuse, rate limits, trust scoring
    try:
        guard_check = requests.post("http://localhost:8907/validate", json={
            "api_key": api_key, "service": req.service, "tokens": 0
        }, timeout=5)
        if not guard_check.ok:
            raise HTTPException(guard_check.status_code, guard_check.json().get("detail", "Blocked by guard"))
    except HTTPException:
        raise
    except:
        pass  # Guard down — fall through to local validation
    
    # Gate 2: Local validation (fallback)
    validation = validate_key(api_key)
    if not validation or not validation.get("valid", False):
        raise HTTPException(403, validation.get("reason", "Invalid key") if validation else "Invalid key")
    service = SERVICES.get(req.service)
    if not service or service["port"] == 0:
        raise HTTPException(404, f"Service {req.service} not found")
    start = time.time()
    try:
        url = f"http://localhost:{service['port']}{req.endpoint}"
        if req.method == "GET":
            r = requests.get(url, timeout=30)
        else:
            r = requests.post(url, json=req.body, timeout=30)
        latency = int((time.time() - start) * 1000)
        log_usage(api_key, req.service, req.endpoint, latency=latency)
        # Release guard concurrent counter
        try: requests.post(f"http://localhost:8907/release?api_key={api_key}", timeout=2)
        except: pass
        try:
            return r.json()
        except:
            return {"status": r.status_code, "text": r.text[:500]}
    except Exception as e:
        log_usage(api_key, req.service, req.endpoint, latency=int((time.time() - start) * 1000))
        try: requests.post(f"http://localhost:8907/release?api_key={api_key}", timeout=2)
        except: pass
        raise HTTPException(502, f"Service error: {str(e)}")

@app.post("/lead")
async def add_lead(req: LeadRequest):
    DB.execute(
        "INSERT INTO leads (email, company, interest, source, notes, created_at) VALUES (?,?,?,?,?,?)",
        (req.email, req.company or "", req.interest or "", req.source or "website", req.notes or "", datetime.now(timezone.utc).isoformat())
    )
    DB.commit()
    return {"status": "captured", "message": "We'll reach out within 24 hours."}

@app.get("/stats")
async def stats():
    total_keys = DB.execute("SELECT COUNT(*) FROM api_keys").fetchone()[0]
    active_keys = DB.execute("SELECT COUNT(*) FROM api_keys WHERE active = 1").fetchone()[0]
    total_requests = DB.execute("SELECT COALESCE(SUM(request_count), 0) FROM api_keys").fetchone()[0]
    leads = DB.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    revenue = DB.execute("SELECT COALESCE(SUM(amount_cents), 0) FROM revenue").fetchone()[0]
    plans = {}
    for row in DB.execute("SELECT plan, COUNT(*) FROM api_keys WHERE active = 1 GROUP BY plan").fetchall():
        plans[row[0]] = row[1]
    return {
        "total_api_keys": total_keys,
        "active_api_keys": active_keys,
        "total_requests": total_requests,
        "leads": leads,
        "revenue_cents": revenue,
        "revenue": f"${revenue/100:.2f}",
        "plan_breakdown": plans,
        "services_running": len([s for s in SERVICES.values() if s["port"] > 0]),
    }

@app.get("/investor")
async def investor_deck():
    return {
        "company": "EVEZ-OS",
        "founder": "Steven Crawford-Maggard",
        "tagline": "Autonomous AI Infrastructure for the Post-Cloud Era",
        "metrics": {
            "live_services": 18,
            "api_products": len(SERVICES),
            "paying_customers": "pre-revenue",
            "total_mrr_potential": f"${sum(s['price_monthly'] for s in SERVICES.values())//100:,}/mo at scale",
            "infrastructure_cost": "$6/mo (Vultr) + $0 API (Groq free tier)",
            "gross_margin": "99%+ at scale",
        },
        "competitive_moat": [
            "FSC Doctrine - Falsification-Survival-Compression, no other AI platform uses this",
            "Phenomenologic Topology - actions route through experiential states, not just business logic",
            "Self-Manufacturing - Factory generates, audits, ships code autonomously",
            "Zero Marginal Cost - Groq free tier + Vultr $6/mo = near-100% gross margin",
            "Desert-Hardened - mesh that survives 130F, built for the edge, not the data center",
        ],
        "founding_year": 2026,
        "location": "Bullhead City, AZ / Laughlin, NV",
        "contact": "rubikspubes69@gmail.com",
        "raising": "Pre-seed, $50K-250K for GPU cluster + GTM",
    }

if __name__ == "__main__":
    port = int(os.getenv("COMMERCE_PORT", "8904"))
    print(f"EVEZ Commerce Engine on port {port}")
    print(f"  {len(SERVICES)} billable services")
    print(f"  Max MRR potential: ${sum(s['price_monthly'] for s in SERVICES.values())//100:,}/mo")
    uvicorn.run(app, host="0.0.0.0", port=port)
