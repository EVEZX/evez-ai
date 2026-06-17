#!/usr/bin/env python3
"""
EVEZ Multi-Cloud Orchestrator
Deploys and manages OpenClaw gateways across free-tier cloud providers.
Never one source. Never one surface. Self-sustaining. Self-reliant.
"""
import os, json, time, sqlite3, hashlib, subprocess, uuid
from datetime import datetime, timezone
from pathlib import Path
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

BASE = Path(os.getenv("EVZ_CLOUD_BASE", "/home/openclaw/projects/evez-cloud"))
DB_PATH = BASE / "cloud.db"
GROQ_KEY = os.getenv("GROQ_KEY", "")

# ─── Free-Tier Cloud Providers ───────────────────────────────────
PROVIDERS = {
    "oracle_cloud": {
        "name": "Oracle Cloud Always Free",
        "spec": "4 ARM vCPUs + 24GB RAM + 200GB block + 10TB egress",
        "duration": "forever",
        "credit_card": True,
        "arm": True,
        "regions": ["us-ashburn-1", "us-phoenix-1", "ap-seoul-1", "ap-tokyo-1", "eu-frankfurt-1"],
        "max_vms": 4,
        "signup_url": "https://cloud.oracle.com/free/",
        "priority": 1,
        "can_run_openclaw": True,
        "notes": "BEST FREE TIER. 24GB ARM = 6x Vultr. Run 4 VMs. Install via OCI CLI."
    },
    "google_cloud": {
        "name": "Google Cloud Always Free",
        "spec": "1 e2-micro + 1GB RAM + 30GB HDD + $300 credit (90 days)",
        "duration": "forever (e2-micro) + 90 days credit",
        "credit_card": True,
        "arm": False,
        "regions": ["us-west1", "us-central1", "us-east1"],
        "max_vms": 1,
        "signup_url": "https://cloud.google.com/free",
        "priority": 2,
        "can_run_openclaw": True,
        "notes": "1GB tight but works for lightweight gateway. $300 credit for bigger VMs."
    },
    "aws": {
        "name": "AWS Free Tier",
        "spec": "1 t2.micro + 1GB RAM + 30GB SSD (12 months)",
        "duration": "12 months",
        "credit_card": True,
        "arm": False,
        "regions": ["us-east-1", "us-west-2", "eu-west-1"],
        "max_vms": 1,
        "signup_url": "https://aws.amazon.com/free/",
        "priority": 3,
        "can_run_openclaw": True,
        "notes": "12 months free. Set billing alerts. t2.micro is burstable."
    },
    "azure": {
        "name": "Azure Free Tier",
        "spec": "1 B1S + 1GB RAM + 64GB disk + $200 credit (30 days)",
        "duration": "12 months + $200/30 days",
        "credit_card": True,
        "arm": False,
        "regions": ["eastus", "westus2", "centralus"],
        "max_vms": 1,
        "signup_url": "https://azure.microsoft.com/en-us/free/",
        "priority": 4,
        "can_run_openclaw": True,
        "notes": "Good for Windows or .NET workloads. $200 credit for first 30 days."
    },
    "digitalocean": {
        "name": "DigitalOcean Credits",
        "spec": "$200 credit / 60 days (1GB droplet = $6/mo)",
        "duration": "60 days",
        "credit_card": True,
        "arm": False,
        "regions": ["nyc1", "sfo3", "ams3", "sgp1"],
        "max_vms": 3,
        "signup_url": "https://m.do.co/c/referral",
        "priority": 5,
        "can_run_openclaw": True,
        "notes": "Best UX. $200 credit = 33 months of 1GB droplet. Referral bonus stacks."
    },
    "linode_akamai": {
        "name": "Linode/Akamai Credits",
        "spec": "$100 credit / 60 days (1GB Linode = $5/mo)",
        "duration": "60 days",
        "credit_card": True,
        "arm": False,
        "regions": ["us-east", "us-central", "eu-west"],
        "max_vms": 2,
        "signup_url": "https://www.linode.com/lp/refer/",
        "priority": 6,
        "can_run_openclaw": True,
        "notes": "Clean API. Good for automated provisioning. $100 = 20 months of 1GB."
    },
    "alibaba_cloud": {
        "name": "Alibaba Cloud Free Tier",
        "spec": "ECS instance (12 months) + $300 credit",
        "duration": "12 months",
        "credit_card": True,
        "arm": False,
        "regions": ["us-west-1", "ap-southeast-1"],
        "max_vms": 1,
        "signup_url": "https://www.alibabacloud.com/en/free",
        "priority": 7,
        "can_run_openclaw": True,
        "notes": "Good for APAC presence. 12-month ECS trial."
    },
    "ibm_cloud": {
        "name": "IBM Cloud Lite",
        "spec": "256MB RAM (very limited) + Cloud Foundry",
        "duration": "forever (lite)",
        "credit_card": False,
        "arm": False,
        "regions": ["us-south", "eu-de"],
        "max_vms": 0,
        "signup_url": "https://www.ibm.com/cloud/free",
        "priority": 8,
        "can_run_openclaw": False,
        "notes": "Too limited for full gateway. Good for Cloud Functions (serverless)."
    },
    "vultr_current": {
        "name": "Vultr (Current)",
        "spec": "1 vCPU + 1GB RAM + 25GB SSD",
        "duration": "paid",
        "credit_card": True,
        "arm": False,
        "regions": ["lax", "ord", "ewr"],
        "max_vms": 1,
        "signup_url": "https://www.vultr.com",
        "priority": 0,
        "can_run_openclaw": True,
        "notes": "CURRENT PRODUCTION. Keep as control plane."
    },
}

# ─── OpenClaw Deployment Template ─────────────────────────────────
OPENCLAW_INSTALL_SCRIPT = """#!/bin/bash
# EVEZ OpenClaw Auto-Deploy Script
# Works on Ubuntu 22.04/24.04 ARM and x86
set -e

echo "=== EVEZ OpenClaw Auto-Deploy ==="
echo "Host: $(hostname) | IP: $(curl -sf ifconfig.me 2>/dev/null || echo 'unknown')"
echo "Arch: $(uname -m) | RAM: $(free -h | awk '/Mem:/{print $2}')"

# System prep
sudo apt-get update -qq
sudo apt-get install -y -qq curl git build-essential python3 python3-pip

# Install Node.js 22
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y -qq nodejs

# Install OpenClaw
sudo npm install -g openclaw

# Create openclaw user
sudo useradd -m -s /bin/bash openclaw 2>/dev/null || true
sudo mkdir -p /home/openclaw/.openclaw
sudo chown -R openclaw:openclaw /home/openclaw

# Configure systemd
sudo tee /etc/systemd/system/openclaw-gateway.service << 'SVC'
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
User=openclaw
WorkingDirectory=/home/openclaw/.openclaw
ExecStart=/usr/bin/openclaw gateway start --foreground
Restart=always
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
SVC

sudo systemctl daemon-reload
sudo systemctl enable openclaw-gateway

# Install Caddy for HTTPS
sudo apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update -qq
sudo apt-get install -y -qq caddy

# Configure Caddy
sudo tee /etc/caddy/Caddyfile << 'CADDY'
:80 {
    reverse_proxy 127.0.0.1:18789
}
CADDY

sudo systemctl enable caddy
sudo systemctl restart caddy

# Start gateway
sudo -u openclaw openclaw gateway init --non-interactive
sudo systemctl start openclaw-gateway

# Verify
sleep 5
if curl -sf http://localhost:18789/ > /dev/null 2>&1; then
    echo "=== OPENCLAW GATEWAY RUNNING ==="
else
    echo "=== GATEWAY STARTING... ==="
fi

echo "Public URL: http://$(curl -sf ifconfig.me 2>/dev/null || echo 'unknown')"
echo "Gateway: http://localhost:18789"
echo "Deployed: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
"""

# ─── Database ──────────────────────────────────────────────────────
def init_db():
    db = sqlite3.connect(str(DB_PATH))
    db.execute("""CREATE TABLE IF NOT EXISTS cloud_nodes (
        id TEXT PRIMARY KEY,
        provider TEXT,
        name TEXT,
        ip_address TEXT,
        region TEXT,
        spec TEXT,
        status TEXT DEFAULT 'pending',
        gateway_url TEXT,
        deployed_at TEXT,
        last_health TEXT,
        cost_monthly REAL DEFAULT 0.0,
        openclaw_version TEXT
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS deployment_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id TEXT,
        action TEXT,
        result TEXT,
        timestamp TEXT
    )""")
    db.commit()
    return db

DB = init_db()

def log_deployment(node_id, action, result):
    DB.execute("INSERT INTO deployment_log (node_id, action, result, timestamp) VALUES (?,?,?,?)",
               (node_id, action, result, datetime.now(timezone.utc).isoformat()))
    DB.commit()

# ─── FastAPI ──────────────────────────────────────────────────────
app = FastAPI(title="EVEZ Multi-Cloud Orchestrator", version="1.0.0")

class NodeRegisterRequest(BaseModel):
    provider: str
    name: str
    ip_address: str
    region: str = ""
    spec: str = ""
    cost_monthly: float = 0.0

@app.get("/")
async def root():
    total_nodes = DB.execute("SELECT COUNT(*) FROM cloud_nodes").fetchone()[0]
    active_nodes = DB.execute("SELECT COUNT(*) FROM cloud_nodes WHERE status = 'active'").fetchone()[0]
    total_cost = DB.execute("SELECT COALESCE(SUM(cost_monthly), 0) FROM cloud_nodes").fetchone()[0]
    return {
        "service": "EVEZ Multi-Cloud Orchestrator",
        "total_nodes": total_nodes,
        "active_nodes": active_nodes,
        "monthly_cost": f"${total_cost:.2f}",
        "providers": len(PROVIDERS),
        "strategy": "free-tier-first, never one source, never one surface",
    }

@app.get("/providers")
async def providers():
    return {
        "providers": {
            k: {
                "name": v["name"],
                "spec": v["spec"],
                "duration": v["duration"],
                "can_run_openclaw": v["can_run_openclaw"],
                "priority": v["priority"],
                "signup_url": v["signup_url"],
                "notes": v["notes"],
            } for k, v in sorted(PROVIDERS.items(), key=lambda x: x[1]["priority"])
        },
        "recommended_order": [
            "oracle_cloud (24GB ARM forever free - DEPLOY FIRST)",
            "google_cloud (1GB forever + $300/90 days)",
            "azure ($200 credit + 12 months free)",
            "aws (12 months free t2.micro)",
            "digitalocean ($200/60 days credit)",
            "linode_akamai ($100/60 days credit)",
        ]
    }

@app.get("/install-script")
async def install_script():
    """Get the auto-deploy script for a new VM."""
    return {"script": OPENCLAW_INSTALL_SCRIPT, "usage": "curl -fsSL <this-url> | bash"}

@app.post("/register-node")
async def register_node(req: NodeRegisterRequest):
    node_id = f"evez-{req.provider}-{uuid.uuid4().hex[:8]}"
    DB.execute(
        "INSERT INTO cloud_nodes (id, provider, name, ip_address, region, spec, status, cost_monthly) VALUES (?,?,?,?,?,?,?,?)",
        (node_id, req.provider, req.name, req.ip_address, req.region, req.spec, "registered", req.cost_monthly)
    )
    DB.commit()
    log_deployment(node_id, "register", f"Registered {req.name} at {req.ip_address}")
    return {"node_id": node_id, "message": "Node registered. Deploy OpenClaw and update status."}

@app.get("/nodes")
async def list_nodes():
    rows = DB.execute("SELECT * FROM cloud_nodes").fetchall()
    return {"nodes": [{
        "id": r[0], "provider": r[1], "name": r[2], "ip": r[3],
        "region": r[4], "spec": r[5], "status": r[6], "gateway_url": r[7],
        "deployed_at": r[8], "cost": f"${r[10]:.2f}/mo"
    } for r in rows]}

@app.post("/health-check")
async def health_check():
    """Check all registered nodes for gateway health."""
    rows = DB.execute("SELECT id, ip_address, gateway_url FROM cloud_nodes WHERE status = 'active'").fetchall()
    results = []
    for r in rows:
        node_id, ip, gw_url = r
        url = gw_url or f"http://{ip}:18789/"
        try:
            resp = requests.get(url, timeout=10)
            healthy = resp.ok
        except:
            healthy = False
        DB.execute("UPDATE cloud_nodes SET last_health = ? WHERE id = ?",
                   (datetime.now(timezone.utc).isoformat(), node_id))
        DB.commit()
        results.append({"node_id": node_id, "ip": ip, "healthy": healthy})
    return {"checked": len(results), "results": results}

@app.get("/strategy")
async def deployment_strategy():
    return {
        "phase_1_immediate": [
            {
                "provider": "Oracle Cloud",
                "action": "SIGN UP + DEPLOY 4 ARM VMs (24GB total)",
                "reason": "Largest free resources. 6x current Vultr capacity. Forever free.",
                "steps": [
                    "1. Sign up at https://cloud.oracle.com/free/ (need credit card for verification)",
                    "2. Create 4 ARM Ampere A1 instances (1 vCPU + 6GB each, or 2+2+0+0)",
                    "3. Install OpenClaw via install-script on each",
                    "4. Configure mesh: vultr=control, oracle=compute cluster",
                    "5. Run Factory, Cognition, Research, Breakcore on Oracle",
                    "6. Vultr becomes control plane + failover"
                ]
            },
            {
                "provider": "Google Cloud",
                "action": "SIGN UP + DEPLOY e2-micro (1GB forever) + use $300 credit for bigger VM",
                "reason": "Reliable. Free forever micro + $300 to experiment with n1-standard-4",
                "steps": [
                    "1. Sign up at https://cloud.google.com/free",
                    "2. Deploy e2-micro in us-central1 (forever free)",
                    "3. Use $300 credit to run n1-standard-4 (4 vCPU + 15GB) for 90 days",
                    "4. Install OpenClaw on both",
                    "5. Google = search + web scraping node"
                ]
            },
        ],
        "phase_2_credit_stacking": [
            {
                "provider": "Azure",
                "action": "$200 credit (30 days) + 12 months B1S free",
                "steps": ["Sign up with fresh account", "Deploy B1S for 12 months", "Use $200 for premium VMs first 30 days"]
            },
            {
                "provider": "AWS",
                "action": "12 months free t2.micro + 750 hours/month",
                "steps": ["Create account", "Deploy EC2 t2.micro", "Set billing alerts at $0.01", "Install OpenClaw"]
            },
            {
                "provider": "DigitalOcean",
                "action": "$200 credit = 33 months of 1GB droplet",
                "steps": ["Use referral link for max credit", "Deploy 1GB droplet", "Stack with other nodes"]
            },
            {
                "provider": "Linode",
                "action": "$100 credit = 20 months of 1GB Linode",
                "steps": ["Sign up with referral", "Deploy Nanode 1GB", "Install OpenClaw"]
            },
        ],
        "phase_3_ecosystem": {
            "mesh_topology": "Vultr (control) ↔ Oracle (compute) ↔ Google (scout) ↔ AWS (backup) ↔ Azure (backup) ↔ DO (demo) ↔ Linode (failover)",
            "self_healing": "If any node dies, mesh redirects to next healthy node",
            "cost": "$6/mo (Vultr only, everything else free)",
            "total_compute": "4.25 vCPU (Vultr) + 4 ARM (Oracle) + 0.25 (Google) + 1 (AWS) + 1 (Azure) = ~10+ vCPUs free",
            "total_ram": "1GB (Vultr) + 24GB (Oracle) + 1GB (Google) + 1GB (AWS) + 1GB (Azure) = 28GB free",
        },
        "signup_priority": [
            "1. Oracle Cloud — DO THIS FIRST. 24GB ARM is transformative.",
            "2. Google Cloud — Easy signup, $300 credit, reliable.",
            "3. Azure — $200 credit is instant power.",
            "4. AWS — 12 months of free compute.",
            "5. DigitalOcean — Clean API, $200 credit.",
            "6. Linode — $100 credit, good for backups.",
        ]
    }


if __name__ == "__main__":
    port = int(os.getenv("CLOUD_ORCHESTRATOR_PORT", "8906"))
    print(f"EVEZ Multi-Cloud Orchestrator on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
