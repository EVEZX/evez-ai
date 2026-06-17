#!/usr/bin/env python3
"""
EVEZ Threat Hunter — Uses the full EVEZ-OS stack to detect, identify, and neutralize threats.
Routes through PTE, scanned by Cognition, logged by MAES, reported via Bridge.
"""
import os, json, time, sqlite3, hashlib, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

BASE = Path(os.getenv("EVZ_THREAT_BASE", "/home/openclaw/projects/evez-threat"))
DB_PATH = BASE / "threats.db"
GROQ_KEY = os.getenv("GROQ_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
PTE = "http://localhost:8901"
COGNITION = "http://localhost:8081"
BRIDGE = "http://localhost:8083"
SEARCH = "http://localhost:8905"
GUARD = "http://localhost:8907"

# ─── Known Threat Signatures ─────────────────────────────────────
THREAT_PROFILES = {
    "solana_validator_hunter": {
        "signatures": ["solana", "firedancer", "bootstrap", "node", "shred", "jibs"],
        "intent": "Steal Solana validator keys and crypto wallets",
        "severity": "high",
        "origin": "DMZHOST bulletproof hosting (NL)",
        "countermeasure": "Block subnet, disable root SSH, key-only auth"
    },
    "infrastructure_scanner": {
        "signatures": ["admin", "docker", "oracle", "dbuser", "ansible", "hduser"],
        "intent": "Enumerate databases, Docker APIs, and cloud services for ransomware",
        "severity": "high",
        "origin": "DMZHOST bulletproof hosting (NL)",
        "countermeasure": "Block subnet, close all non-essential ports"
    },
    "iot_botnet": {
        "signatures": ["root", "ubnt", "orangepi", "test", "user"],
        "intent": "Recruit IoT devices into Mirai-style DDoS botnet",
        "severity": "medium",
        "origin": "Alibaba Cloud / AFRINIC space",
        "countermeasure": "Block subnet, disable default credentials"
    },
}

def init_db():
    db = sqlite3.connect(str(DB_PATH))
    db.execute("""CREATE TABLE IF NOT EXISTS threats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT,
        subnet TEXT,
        attack_type TEXT,
        severity TEXT,
        attempt_count INTEGER,
        users_tried TEXT,
        classification TEXT,
        whois_info TEXT,
        first_seen TEXT,
        last_seen TEXT,
        blocked INTEGER DEFAULT 0,
        countermeasure TEXT
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS security_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        source TEXT,
        severity TEXT,
        details TEXT,
        action_taken TEXT,
        timestamp TEXT
    )""")
    db.commit()
    return db

DB = init_db()

# ─── Scanner ──────────────────────────────────────────────────────
def scan_ssh_attacks():
    """Parse auth.log for SSH brute force attempts."""
    threats = []
    try:
        result = subprocess.run(
            ["sudo", "grep", "-E", "Failed password|Invalid user", "/var/log/auth.log"],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().split("\n") if result.stdout else []
    except:
        return []

    ip_data = defaultdict(lambda: {"count": 0, "users": set(), "timestamps": []})
    for line in lines:
        # Extract IP
        import re
        ip_match = re.search(r'from (\d+\.\d+\.\d+\.\d+)', line)
        user_match = re.search(r'user (\S+)', line)
        if ip_match:
            ip = ip_match.group(1)
            user = user_match.group(1) if user_match else "unknown"
            ip_data[ip]["count"] += 1
            ip_data[ip]["users"].add(user)
            ip_data[ip]["timestamps"].append(line[:19])

    for ip, data in ip_data.items():
        subnet = ".".join(ip.split(".")[:3]) + ".0/24"
        users = list(data["users"])
        
        # Classify the threat
        classification = "unknown"
        for name, profile in THREAT_PROFILES.items():
            if any(u in profile["signatures"] for u in users):
                classification = name
                break

        threats.append({
            "ip": ip, "subnet": subnet, "attempt_count": data["count"],
            "users_tried": users, "classification": classification,
            "severity": THREAT_PROFILES.get(classification, {}).get("severity", "low"),
            "countermeasure": THREAT_PROFILES.get(classification, {}).get("countermeasure", "Block IP"),
        })
    return threats

def check_open_ports():
    """Check for services exposed to 0.0.0.0."""
    exposed = []
    try:
        result = subprocess.run(
            ["sudo", "ss", "-tlnp"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            if "0.0.0.0" in line and "LISTEN" in line:
                parts = line.split()
                for p in parts:
                    if ":" in p and "0.0.0.0" in p:
                        port = p.split(":")[-1]
                        if port not in ("22", "80", "443"):
                            exposed.append({"port": int(port), "bind": "0.0.0.0", "risk": "HIGH"})
    except:
        pass
    return exposed

def check_suspicious_processes():
    """Look for crypto miners, reverse shells, unknown daemons."""
    suspicious = []
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split("\n"):
            lower = line.lower()
            for sig in ["xmrig", "cryptonight", "stratum", "minerd", "kworker"]:
                if sig in lower and "grep" not in lower:
                    suspicious.append({"process": line[:100], "signature": sig})
    except:
        pass
    return suspicious

# ─── AI Threat Analysis ──────────────────────────────────────────
def ai_analyze_threats(threats, exposed_ports, suspicious_procs):
    """Use Groq to analyze the full threat landscape."""
    if not GROQ_KEY:
        return {"analysis": "Groq unavailable", "recommendations": []}
    
    prompt = f"""You are the EVEZ Threat Hunter AI. Analyze this security data and provide:
1. Threat assessment (who is targeting us, why, what are they after)
2. Attack attribution (what botnet/group, what infrastructure)
3. Immediate actions (what to block, what to fix)
4. Long-term hardening recommendations

SSH Attackers (last 24h):
{json.dumps(threats[:20], indent=2)}

Exposed Ports (0.0.0.0 = internet-facing):
{json.dumps(exposed_ports, indent=2)}

Suspicious Processes:
{json.dumps(suspicious_procs, indent=2) if suspicious_procs else "None detected"}

Server: Vultr VPS, 66.135.1.200, running 19 API services + OpenClaw gateway
Current protections: iptables, fail2ban, Caddy reverse proxy with basic auth

Respond in JSON: {{\"threat_level\": \"\", \"attribution\": \"\", \"target_analysis\": \"\", \"immediate_actions\": [], \"hardening\": []}}"""

    try:
        r = requests.post(GROQ_URL, headers={
            "Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"
        }, json={"model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2, "max_tokens": 1500}, timeout=30)
        if r.ok:
            content = r.json()["choices"][0]["message"]["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
    except:
        pass
    return {"analysis": "AI unavailable", "recommendations": ["Block all DMZHOST subnets"]}

# ─── FastAPI ──────────────────────────────────────────────────────
app = FastAPI(title="EVEZ Threat Hunter", version="1.0.0")

@app.get("/")
async def root():
    return {
        "service": "EVEZ Threat Hunter",
        "status": "armed",
        "threat_profiles": list(THREAT_PROFILES.keys()),
    }

@app.post("/scan")
async def full_scan():
    """Full security scan using EVEZ-OS stack."""
    # 1. SSH attack scan
    ssh_threats = scan_ssh_attacks()
    
    # 2. Port exposure check
    exposed = check_open_ports()
    
    # 3. Suspicious process check
    suspicious = check_suspicious_processes()
    
    # 4. Route through PTE (phenomenologic threat assessment)
    try:
        pte = requests.post(f"{PTE}/route", json={"action": "security_scan", "context": {"threats": len(ssh_threats)}}, timeout=5).json()
        pte_node = pte.get("current_node", "unknown")
        pte_basin = pte.get("current_basin", "unknown")
    except:
        pte_node = pte_basin = "unavailable"
    
    # 5. AI analysis
    ai = ai_analyze_threats(ssh_threats, exposed, suspicious)
    
    # 6. Store threats in DB
    for t in ssh_threats:
        DB.execute(
            "INSERT OR REPLACE INTO threats (ip, subnet, attack_type, severity, attempt_count, users_tried, classification, first_seen, last_seen) VALUES (?,?,?,?,?,?,?,?,?)",
            (t["ip"], t["subnet"], t["classification"], t["severity"], t["attempt_count"],
             json.dumps(t["users_tried"]), t["classification"],
             datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat())
        )
    DB.commit()
    
    # 7. Log to security events
    DB.execute(
        "INSERT INTO security_events (event_type, source, severity, details, action_taken, timestamp) VALUES (?,?,?,?,?,?)",
        ("scan", "threat_hunter", "info" if not ssh_threats else "warning",
         f"Found {len(ssh_threats)} attackers, {len(exposed)} exposed ports, {len(suspicious)} suspicious procs",
         "logged", datetime.now(timezone.utc).isoformat())
    )
    DB.commit()
    
    # 8. Post to Bridge dashboard
    try:
        requests.post(f"{BRIDGE}/api/event", json={
            "type": "security_scan", "source": "threat_hunter",
            "data": {"attackers": len(ssh_threats), "exposed": len(exposed), "suspicious": len(suspicious)}
        }, timeout=3)
    except:
        pass
    
    return {
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "threats": {
            "ssh_attackers": len(ssh_threats),
            "total_attempts": sum(t["attempt_count"] for t in ssh_threats),
            "exposed_ports": exposed,
            "suspicious_processes": suspicious,
        },
        "pte_routing": {"node": pte_node, "basin": pte_basin},
        "ai_analysis": ai,
        "top_attackers": sorted(ssh_threats, key=lambda t: t["attempt_count"], reverse=True)[:5],
        "blocked_subnets": ["80.94.92.0/24", "193.32.162.0/24", "45.148.10.0/24", "156.238.236.0/24", "39.104.64.0/24"],
    }

@app.get("/status")
async def status():
    threats = DB.execute("SELECT COUNT(DISTINCT ip) FROM threats").fetchone()[0]
    events = DB.execute("SELECT COUNT(*) FROM security_events").fetchone()[0]
    return {"tracked_threats": threats, "security_events": events}

@app.get("/threats")
async def list_threats(limit: int = 50):
    rows = DB.execute("SELECT * FROM threats ORDER BY attempt_count DESC LIMIT ?", (limit,)).fetchall()
    return {"threats": [{
        "ip": r[1], "subnet": r[2], "type": r[3], "severity": r[4],
        "attempts": r[5], "users": r[6], "classification": r[7],
        "blocked": bool(r[11]), "countermeasure": r[12]
    } for r in rows]}

@app.get("/events")
async def events(limit: int = 50):
    rows = DB.execute("SELECT * FROM security_events ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    return {"events": [{
        "type": r[1], "source": r[2], "severity": r[3],
        "details": r[4], "action": r[5], "time": r[6]
    } for r in rows]}

if __name__ == "__main__":
    port = int(os.getenv("THREAT_HUNTER_PORT", "8908"))
    print(f"🛡️ EVEZ Threat Hunter on port {port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
