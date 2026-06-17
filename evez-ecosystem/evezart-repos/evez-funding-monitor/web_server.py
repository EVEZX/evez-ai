"""
EVEZ-OS Funding Monitor — Web Dashboard
FastAPI service on :8101 for funding opportunity tracking.
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import json
import os
import time
from datetime import datetime

app = FastAPI(title="EVEZ-OS Funding Monitor", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MONITOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(MONITOR_DIR, "funding_monitor_state.json")

# Funding targets with status
TARGETS = {
    "government_contracts": [
        {"name": "AARO Gap Analysis Contract", "agency": "DoD/AARO", "ask": "$750K-$1.5M",
         "status": "concept_paper", "deadline": "NDAA FY2027 cycle (Q3 2026)", "priority": 1},
        {"name": "DARPA BAA — GAPS Program", "agency": "DARPA", "ask": "$500K-$1M",
         "status": "researching", "deadline": "Rolling (BAA open)", "priority": 2},
        {"name": "DARPA Seedling", "agency": "DARPA", "ask": "$150K-$300K",
         "status": "researching", "deadline": "Quarterly", "priority": 3},
        {"name": "CISA Information Integrity", "agency": "DHS/CISA", "ask": "$500K-$1M",
         "status": "concept_paper", "deadline": "SBIR quarterly", "priority": 2},
        {"name": "IARPA Information Extraction", "agency": "ODNI/IARPA", "ask": "$300K-$1M",
         "status": "researching", "deadline": "Varies by program", "priority": 3},
    ],
    "government_grants": [
        {"name": "NSF Computational Social Science", "agency": "NSF", "ask": "$300K-$500K",
         "status": "planning", "deadline": "January annual cycle", "priority": 2},
        {"name": "NSF Secure & Trustworthy Cyberspace", "agency": "NSF", "ask": "$500K-$1M",
         "status": "planning", "deadline": "Annual cycle", "priority": 3},
        {"name": "NEH Digital Humanities", "agency": "NEH", "ask": "$100K-$300K",
         "status": "exploring", "deadline": "Semi-annual", "priority": 4},
    ],
    "foundations": [
        {"name": "Knight Foundation — FOIA Tech", "agency": "Knight", "ask": "$200K-$500K",
         "status": "loi_drafted", "deadline": "Rolling", "priority": 1},
        {"name": "MacArthur Foundation", "agency": "MacArthur", "ask": "$100K-$300K",
         "status": "exploring", "deadline": "Quarterly review", "priority": 3},
        {"name": "Open Society Foundations", "agency": "Soros", "ask": "$200K-$500K",
         "status": "exploring", "deadline": "Rolling", "priority": 2},
        {"name": "Schmidt Futures / Mozilla", "agency": "Tech Philanthropy", "ask": "$50K-$200K",
         "status": "exploring", "deadline": "Varies", "priority": 3},
    ],
    "revenue": [
        {"name": "News Org SaaS (ProPublica, Bellingcat)", "agency": "Media", "ask": "$5K-$50K/yr each",
         "status": "planning", "deadline": "N/A", "priority": 2},
        {"name": "FOIA/Legal Firms", "agency": "Legal", "ask": "Per-case", "status": "planning",
         "deadline": "N/A", "priority": 3},
        {"name": "Congressional Offices", "agency": "Legislative", "ask": "$100K-$500K contracts",
         "status": "exploring", "deadline": "Appropriations cycle", "priority": 2},
    ],
}


@app.get("/health")
def health():
    return {"status": "ok", "service": "funding-monitor", "version": "1.0.0", "ts": int(time.time())}


@app.get("/api/v1/targets")
def get_targets():
    """All funding targets with status."""
    return {"targets": TARGETS, "total_targets": sum(len(v) for v in TARGETS.values())}


@app.get("/api/v1/targets/{category}")
def get_category(category: str):
    """Funding targets for a specific category."""
    if category not in TARGETS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Category not found: {category}")
    return {"category": category, "targets": TARGETS[category]}


@app.get("/api/v1/pipeline")
def get_pipeline():
    """Funding pipeline summary."""
    total_ask = 0
    by_status = {}
    for category, targets in TARGETS.items():
        for t in targets:
            status = t["status"]
            by_status[status] = by_status.get(status, 0) + 1
            total_ask += 1

    return {
        "total_opportunities": total_ask,
        "by_status": by_status,
        "by_category": {k: len(v) for k, v in TARGETS.items()},
        "estimated_year1_low": 525000,
        "estimated_year1_high": 2000000,
        "estimated_year3": 2300000,
    }


@app.get("/api/v1/keywords")
def get_keywords():
    """Keywords monitored across grant databases."""
    return {
        "keywords": [
            "UAP", "unidentified anomalous", "transparency", "FOIA",
            "disclosure", "redaction", "censorship", "information integrity",
            "computational social science", "spectral analysis", "gap detection",
            "AARO", "anomaly resolution", "misinformation", "open government",
        ],
        "sources_monitored": 6,
    }


@app.get("/api/v1/next_actions")
def next_actions():
    """Prioritized next actions for funding pursuit."""
    return {
        "actions": [
            {"priority": 1, "action": "Register on SAM.gov + get UEI number",
             "why": "Required for all federal contracts/grants", "timeline": "This week"},
            {"priority": 2, "action": "Submit AARO concept paper",
             "why": "Largest single opportunity, NDAA timing", "timeline": "2 weeks"},
            {"priority": 3, "action": "Submit Knight Foundation LOI",
             "why": "LOI drafted, lowest barrier to entry", "timeline": "This week"},
            {"priority": 4, "action": "Build demo video of AARO gap detection",
             "why": "Visual proof for every pitch", "timeline": "3 days"},
            {"priority": 5, "action": "Contact Schumer/Gillibrand offices",
             "why": "UAP Disclosure Act relevance", "timeline": "1 week"},
            {"priority": 6, "action": "Pitch ProPublica / The Intercept",
             "why": "Revenue + proof of concept", "timeline": "2 weeks"},
            {"priority": 7, "action": "Set up DARPA BAA submission",
             "why": "Rolling deadline, high fit for GAPS program", "timeline": "2 weeks"},
            {"priority": 8, "action": "Submit to CISA SBIR Phase I",
             "why": "Information integrity angle, quarterly deadline", "timeline": "3 weeks"},
        ]
    }


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Simple funding dashboard."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>EVEZ-OS Funding Monitor</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #0a0a0a; color: #e0e0e0; margin: 0; padding: 20px; }
        h1 { color: #00ff88; }
        h2 { color: #00ccff; margin-top: 30px; }
        .card { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 16px; margin: 8px 0; }
        .priority-1 { border-left: 4px solid #ff4444; }
        .priority-2 { border-left: 4px solid #ffaa00; }
        .priority-3 { border-left: 4px solid #00ccff; }
        .priority-4 { border-left: 4px solid #666; }
        .stat { font-size: 2em; color: #00ff88; }
        .label { color: #888; font-size: 0.9em; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
        .ask { color: #00ff88; font-weight: bold; }
        .status { padding: 2px 8px; border-radius: 4px; font-size: 0.85em; }
        .status-concept_paper { background: #ff444433; color: #ff6666; }
        .status-loi_drafted { background: #00ff8833; color: #00ff88; }
        .status-researching { background: #ffaa0033; color: #ffaa00; }
        .status-planning { background: #00ccff33; color: #00ccff; }
        .status-exploring { background: #66666633; color: #999; }
    </style>
</head>
<body>
    <h1>💰 EVEZ-OS Funding Monitor</h1>
    <div class="grid">
        <div class="card">
            <div class="stat">15</div>
            <div class="label">Active Opportunities</div>
        </div>
        <div class="card">
            <div class="stat">$525K–$2M</div>
            <div class="label">Year 1 Projection</div>
        </div>
        <div class="card">
            <div class="stat">$2.3M</div>
            <div class="label">Year 3 Projection</div>
        </div>
        <div class="card">
            <div class="stat">6</div>
            <div class="label">Sources Monitored</div>
        </div>
    </div>
    <h2>🔥 Top Priority Actions</h2>
    <div class="card priority-1"><b>1. Register SAM.gov + UEI</b> — Required for all federal awards. Do this today.</div>
    <div class="card priority-1"><b>2. Submit AARO Concept Paper</b> — $750K–$1.5M, NDAA FY2027 timing</div>
    <div class="card priority-2"><b>3. Submit Knight LOI</b> — $200K–$500K, LOI drafted, lowest barrier</div>
    <div class="card priority-2"><b>4. Build Demo Video</b> — Visual proof for every pitch, 3 days</div>
    <div class="card priority-2"><b>5. Contact Schumer/Gillibrand</b> — UAP Disclosure Act wedge</div>
    <h2>📊 Pipeline by Category</h2>
    <div class="card">🏛️ Government Contracts: 5 targets ($750K–$1.5M top ask)</div>
    <div class="card">📄 Government Grants: 3 targets ($300K–$1M top ask)</div>
    <div class="card">🏛️ Foundations: 4 targets ($200K–$500K top ask)</div>
    <div class="card">💰 Revenue: 3 channels ($5K–$500K)</div>
</body>
</html>
"""
