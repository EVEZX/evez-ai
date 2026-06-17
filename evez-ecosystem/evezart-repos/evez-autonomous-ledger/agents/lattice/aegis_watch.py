#!/usr/bin/env python3
"""
agents/lattice/aegis_watch.py
Lightweight AEGIS threat watch - fits evez-autonomous-ledger agent pattern.
"""
import json, os, hashlib, requests
from pathlib import Path
from datetime import datetime, timezone

SCAN_PATH    = Path("DECISIONS/aegis")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER        = "EvezArt"
H = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json",
     "X-GitHub-Api-Version": "2022-11-28"} if GITHUB_TOKEN else {}

def ts(): return datetime.now(timezone.utc).isoformat()
def sha(d): return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]

def scan_forks():
    threats = []
    try:
        r = requests.get(f"https://api.github.com/repos/{OWNER}/evez-os/forks?per_page=10", headers=H, timeout=8)
        if r.ok:
            for fork in r.json():
                owner = fork.get("owner", {}).get("login", "")
                if owner.lower() not in ["evezart", "evez666"]:
                    threats.append({"type": "unexpected_fork", "repo": fork.get("full_name"), "owner": owner})
    except: pass
    return threats

def scan_rate_limit():
    try:
        r = requests.get("https://api.github.com/rate_limit", headers=H, timeout=5)
        if r.ok:
            d = r.json().get("rate", {})
            remaining = d.get("remaining", 5000)
            if remaining < 100:
                return {"type": "rate_limit_low", "remaining": remaining, "limit": d.get("limit")}
    except: pass
    return None

def run():
    SCAN_PATH.mkdir(parents=True, exist_ok=True)
    threats = scan_forks()
    rt = scan_rate_limit()
    if rt: threats.append(rt)
    hawkes_lambda = round(0.1 + 0.3 * len(threats), 4)
    risk = "RED" if len(threats) > 3 else "YELLOW" if threats else "GREEN"
    report = {
        "ts": ts(), "threats": threats, "threat_count": len(threats),
        "hawkes_lambda": hawkes_lambda, "risk_level": risk,
        "falsifier": "If threats are false positives, reduce hawkes_alpha and re-scan.",
    }
    report["hash"] = sha(report)
    ts_safe = ts().replace(":", "-").replace(".", "-")
    (SCAN_PATH / f"{ts_safe}_scan.json").write_text(json.dumps(report, indent=2))
    print(f"[aegis_watch] risk={risk} | threats={len(threats)} | lambda={hawkes_lambda}")
    return report

if __name__ == "__main__": run()
