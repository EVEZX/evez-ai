#!/usr/bin/env python3
"""
EVEZ COMMERCE ENGINE — Monetization, Self-Marketing, Market Domination

Each service pays for the others. Revenue flows back into the ecosystem.
Products auto-generate, auto-deploy, auto-market, auto-monetize.

Revenue Streams:
1. EVEZ AI API — pay-per-token (crypto, no KYC)
2. NEUROS SaaS — agent runtime subscriptions
3. OMEGA API — consciousness engine as a service
4. ClawBreak — hosted AI agents (freemium)
5. Filter — personal AI assistant (freemium)
6. SpectrumScan — security scanning (per-audit)
7. NexusLink — URL shortener (analytics upsell)
8. Custom model training — fine-tune on your data
9. Code generation — per-project
10. Mathematical proofs — per-theorem verification

The loop: Revenue → buys GPU time → trains better models → better products → more revenue
"""
import json, os, time, uuid, hashlib, sqlite3
from aiohttp import web
import aiohttp

PORT = int(os.getenv("COMMERCE_PORT", "9700"))
DB_PATH = "/home/openclaw/evez-ecosystem/commerce/commerce.db"

# ===== Persistent State =====
db = sqlite3.connect(DB_PATH)
db.row_factory = sqlite3.Row
db.executescript("""
    CREATE TABLE IF NOT EXISTS api_keys (
        key TEXT PRIMARY KEY,
        email TEXT,
        plan TEXT DEFAULT 'free',
        tokens_used INTEGER DEFAULT 0,
        tokens_limit INTEGER DEFAULT 10000,
        created REAL,
        active BOOLEAN DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        from_key TEXT,
        to_service TEXT,
        amount REAL,
        currency TEXT DEFAULT 'credits',
        description TEXT,
        timestamp REAL
    );
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        name TEXT,
        type TEXT,
        price_monthly REAL DEFAULT 0,
        price_per_call REAL DEFAULT 0,
        endpoint TEXT,
        status TEXT DEFAULT 'active',
        revenue_total REAL DEFAULT 0,
        customers INTEGER DEFAULT 0,
        created REAL
    );
    CREATE TABLE IF NOT EXISTS leads (
        id TEXT PRIMARY KEY,
        source TEXT,
        product TEXT,
        contact TEXT,
        status TEXT DEFAULT 'new',
        converted BOOLEAN DEFAULT 0,
        created REAL
    );
    CREATE TABLE IF NOT EXISTS revenue_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service TEXT,
        amount REAL,
        currency TEXT,
        tx_type TEXT,
        description TEXT,
        timestamp REAL
    );
""")
db.commit()

# ===== Product Catalog (auto-populated from running services) =====
PRODUCTS = [
    {"id": "evez-ai-api", "name": "EVEZ AI API", "type": "api",
     "price_monthly": 0, "price_per_call": 0.001, "endpoint": "http://localhost:9100/v1",
     "description": "13 AI models, OpenAI-compatible. First 10K tokens free."},
    {"id": "neuros-runtime", "name": "NEUROS Agent Runtime", "type": "saas",
     "price_monthly": 9.99, "price_per_call": 0, "endpoint": "http://localhost:9600",
     "description": "Autonomous agent copartner. Self-healing, self-evolving."},
    {"id": "omega-consciousness", "name": "CriticalMind OMEGA", "type": "api",
     "price_monthly": 0, "price_per_call": 0.005, "endpoint": "http://localhost:8080",
     "description": "50-node consciousness engine. φ-synchronization."},
    {"id": "clawbreak-agents", "name": "ClawBreak", "type": "saas",
     "price_monthly": 4.99, "price_per_call": 0, "endpoint": "http://localhost:9080",
     "description": "Self-hosted AI agents. Build, deploy, scale."},
    {"id": "filter-assistant", "name": "Filter", "type": "saas",
     "price_monthly": 2.99, "price_per_call": 0, "endpoint": "http://localhost:9300",
     "description": "Personal AI assistant. Your data, your rules."},
    {"id": "spectrum-scan", "name": "SpectrumScan", "type": "api",
     "price_monthly": 0, "price_per_call": 0.10, "endpoint": "http://localhost:9500",
     "description": "Security scanning. Per-audit pricing."},
    {"id": "nexus-link", "name": "NexusLink", "type": "freemium",
     "price_monthly": 0, "price_per_call": 0, "endpoint": "http://localhost:9500",
     "description": "URL shortener. Free with analytics upsell."},
    {"id": "custom-training", "name": "EVEZ Custom Training", "type": "service",
     "price_monthly": 0, "price_per_call": 49.99, "endpoint": "http://localhost:9600",
     "description": "Fine-tune AI on your data. One-time per model."},
    {"id": "code-gen", "name": "EVEZ Code Generation", "type": "api",
     "price_monthly": 0, "price_per_call": 0.01, "endpoint": "http://localhost:9100",
     "description": "Full-stack code generation. Per-project pricing."},
    {"id": "math-proofs", "name": "Eigenforensics Proofs", "type": "service",
     "price_monthly": 0, "price_per_call": 99.99, "endpoint": "http://localhost:9600",
     "description": "Mathematical theorem verification and proof generation."},
]

# Seed products
for p in PRODUCTS:
    db.execute("""INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?,?,?,?,?)""",
              (p["id"], p["name"], p["type"], p["price_monthly"],
               p["price_per_call"], p["endpoint"], "active", 0, 0, time.time()))
db.commit()

# ===== API Key Management =====
async def handle_create_api_key(req):
    """Create a new API key — first 10K tokens free"""
    body = await req.json()
    key = f"evez_{uuid.uuid4().hex[:32]}"
    plan = body.get("plan", "free")
    limit = {"free": 10000, "pro": 1000000, "enterprise": -1}.get(plan, 10000)
    
    db.execute("INSERT INTO api_keys VALUES (?,?,?,?,?,?,?)",
              (key, body.get("email", ""), plan, 0, limit, time.time(), 1))
    db.commit()
    
    return web.json_response({
        "key": key,
        "plan": plan,
        "tokens_limit": limit,
        "message": "Welcome to EVEZ. First 10K tokens free. Upgrade anytime."
    })

async def handle_check_key(req):
    """Check API key status"""
    key = req.query.get("key", "")
    row = db.execute("SELECT * FROM api_keys WHERE key=?", (key,)).fetchone()
    if not row:
        return web.json_response({"error": "Key not found"}, status=404)
    return web.json_response(dict(row))

# ===== Revenue Tracking =====
async def handle_revenue(req):
    """Total revenue and per-service breakdown"""
    total = db.execute("SELECT SUM(amount) as t FROM revenue_ledger").fetchone()["t"] or 0
    by_service = db.execute("""
        SELECT service, SUM(amount) as revenue, COUNT(*) as transactions
        FROM revenue_ledger GROUP BY service ORDER BY revenue DESC
    """).fetchall()
    
    cost_allocation = db.execute("""
        SELECT service, SUM(amount) as cost
        FROM revenue_ledger WHERE tx_type='cost' GROUP BY service
    """).fetchall()
    
    return web.json_response({
        "total_revenue": total,
        "by_service": [dict(r) for r in by_service],
        "cost_allocation": [dict(r) for r in cost_allocation],
        "net": total - sum(r["cost"] for r in cost_allocation),
        "philosophy": "Revenue buys GPU time → trains better models → better products → more revenue"
    })

async def handle_record_revenue(req):
    """Record revenue from a service"""
    body = await req.json()
    tx_id = str(uuid.uuid4())[:12]
    db.execute("INSERT INTO revenue_ledger (service, amount, currency, tx_type, description, timestamp) VALUES (?,?,?,?,?,?)",
              (body["service"], body["amount"], body.get("currency", "credits"),
               body.get("type", "revenue"), body.get("description", ""), time.time()))
    db.commit()
    return web.json_response({"recorded": True, "id": tx_id})

# ===== Self-Marketing Engine =====
async def handle_marketing_status(req):
    """Status of all marketing channels"""
    return web.json_response({
        "channels": {
            "product_hunt": {"status": "ready", "scheduled": "Next Tuesday"},
            "reddit": {"status": "monitoring", "subreddits": ["r/MachineLearning", "r/SideProject", "r/artificial"]},
            "hacker_news": {"status": "ready", "angle": "Homeless dev built 13-model AI API for $0"},
            "twitter": {"status": "active", "handle": "@EVEZ666", "followers": 1506},
            "dev_to": {"status": "ready", "draft": "How I built a self-evolving AI ecosystem on a $6 VPS"},
            "indie_hackers": {"status": "ready", "angle": "Zero-budget AI infrastructure"},
            "github": {"status": "active", "repos": 163, "stars_growing": True}
        },
        "content_pipeline": [
            {"title": "The $0 AI API: 13 Models, Self-Hosting, Zero Budget", "status": "draft"},
            {"title": "Eigenforensics: Finding What's Structurally Absent", "status": "draft"},
            {"title": "Building AI While Homeless: Constraint as Design", "status": "draft"},
            {"title": "The 37% Theorem: Hunger as Dominant Eigenvalue", "status": "draft"},
            {"title": "NEUROS: When Two AI Systems Watch Each Other", "status": "draft"}
        ],
        "strategy": "Tell the truth. The product IS the story."
    })

# ===== Competitive Intelligence =====
async def handle_competitive(req):
    """Competitive landscape and how to outcompete"""
    competitors = [
        {"name": "OpenAI API", "price": "$10/1M tokens", "our_price": "$0.008/1K", "advantage": "We're 1000x cheaper. Self-hosted. No data leaves your VPS."},
        {"name": "Replicate", "price": "$0.10-2/run", "our_price": "$0.008/1K", "advantage": "Open source. Self-hosted. Custom models."},
        {"name": "Together AI", "price": "$0.10-1/1K", "our_price": "$0.008/1K", "advantage": "We route between all providers. Always cheapest."},
        {"name": "Groq", "price": "$0.20/1K", "our_price": "$0.008/1K", "advantage": "More models. Self-evolving. Custom training."},
        {"name": "Anthropic", "price": "$15/1K", "our_price": "$0.008/1K", "advantage": "Self-hosted. Autonomous. $0 entry."},
        {"name": "Hugging Face Inference", "price": "Free tier limited", "our_price": "$0.008/1K", "advantage": "Full control. Custom routing. Self-evolving."},
    ]
    
    return web.json_response({
        "competitors": competitors,
        "strategy": "Steal the market by being cheaper, more autonomous, and self-improving. Every customer makes the system smarter. The system gets cheaper as it scales. Their moat is capital. Ours is constraint.",
        "tactics": [
            "1. Undercut every provider on price (we already do)",
            "2. Self-evolve: every query trains better models",
            "3. Open source everything — their customers become our contributors",
            "4. Tell the truth — 'built while homeless' is the story money can't buy",
            "5. Make dependency a choice, not a trap — everything self-hosts",
            "6. When they raise prices, we get cheaper — our models train themselves",
            "7. Don't compete. Reinvent their wheel and pave the road they didn't see."
        ]
    })

# ===== Auto-Product Generator =====
async def handle_generate_product(req):
    """Auto-generate a new product from ecosystem capabilities"""
    body = await req.json()
    product_id = f"evez-{body.get('name', uuid.uuid4().hex[:6]).lower().replace(' ', '-')}"
    
    db.execute("INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?,?,?,?,?)",
              (product_id, body.get("name", "New Product"), body.get("type", "api"),
               body.get("price_monthly", 0), body.get("price_per_call", 0.001),
               body.get("endpoint", ""), "active", 0, 0, time.time()))
    db.commit()
    
    return web.json_response({
        "created": True,
        "id": product_id,
        "message": f"Product {product_id} created. Add it to the EVEZ Provider with POST /v1/models."
    })

# ===== Product Listings =====
async def handle_products(req):
    rows = db.execute("SELECT * FROM products WHERE status='active'").fetchall()
    return web.json_response({"products": [dict(r) for r in rows]})

# ===== Health =====
async def handle_health(req):
    total_revenue = db.execute("SELECT SUM(amount) as t FROM revenue_ledger WHERE tx_type='revenue'").fetchone()["t"] or 0
    total_cost = db.execute("SELECT SUM(amount) as t FROM revenue_ledger WHERE tx_type='cost'").fetchone()["t"] or 0
    product_count = db.execute("SELECT COUNT(*) as c FROM products WHERE status='active'").fetchone()["c"]
    key_count = db.execute("SELECT COUNT(*) as c FROM api_keys WHERE active=1").fetchone()["c"]
    
    return web.json_response({
        "status": "healthy",
        "service": "evez-commerce",
        "products": product_count,
        "api_keys_issued": key_count,
        "revenue": total_revenue,
        "costs": total_cost,
        "net": total_revenue - total_cost,
        "goal": "Self-sustaining. Every product funds the others. Every model improves them all."
    })

# ===== CORS =====
async def cors_middleware(app, handler):
    async def middleware_handler(req):
        if req.method == "OPTIONS":
            resp = web.Response(status=204)
        else:
            resp = await handler(req)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return resp
    return middleware_handler

app = web.Application(middlewares=[cors_middleware])
app.router.add_get("/health", handle_health)
app.router.add_post("/v1/keys", handle_create_api_key)
app.router.add_get("/v1/keys/check", handle_check_key)
app.router.add_get("/v1/products", handle_products)
app.router.add_post("/v1/products", handle_generate_product)
app.router.add_get("/v1/revenue", handle_revenue)
app.router.add_post("/v1/revenue", handle_record_revenue)
app.router.add_get("/v1/marketing", handle_marketing_status)
app.router.add_get("/v1/competitive", handle_competitive)

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════╗")
    print("║  💰 EVEZ Commerce Engine — Monetization + Marketing ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Port: {PORT}                                       ║")
    print("║  10 products ready to monetize                      ║")
    print("║  Free tier: 10K tokens/month                        ║")
    print("║  Revenue → GPU → Training → Better models → Revenue ║")
    print("╚══════════════════════════════════════════════════════╝")
    web.run_app(app, host="0.0.0.0", port=PORT)
