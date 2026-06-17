#!/usr/bin/env python3
"""
EVEZ-OS OSINT DEFENDER — LIVE MONITOR
Real-time attack surface monitoring. Watches our VPS 24/7.
All data from REAL system calls. Zero mock. Zero fake.

Run as: python3 osint_monitor.py
Or as systemd service for 24/7 operation.
"""

import hashlib
import json
import time
import subprocess
import re
import urllib.request
import ssl
from pathlib import Path
from collections import defaultdict
from datetime import datetime

_ctx = ssl.create_default_context()
OUR_IP = "45.63.66.247"
SPINE = Path("/home/openclaw/.openclaw/workspace/evez-os-sensors/monitor_spine.jsonl")
REPORT = Path("/home/openclaw/.openclaw/workspace/evez-os-sensors/latest_report.json")

def _json(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "EVEZ-MONITOR/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=_ctx) as r:
            return json.loads(r.read())
    except: return None

def _run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else None
    except: return None

def spine_append(event_type, data):
    """Append to the monitoring spine."""
    SPINE.parent.mkdir(parents=True, exist_ok=True)
    last_hash = "GENESIS"
    if SPINE.exists():
        with open(SPINE) as f:
            for line in f:
                if line.strip():
                    try:
                        e = json.loads(line)
                        if "hash" in e: last_hash = e["hash"]
                    except: pass
    raw = f"{event_type}:{time.time()}:{last_hash}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:24]
    entry = {"type": event_type, "data": data, "hash": h, "prev": last_hash, "ts": time.time(), "utc": datetime.utcnow().isoformat(), "powered_by": "EVEZ-MONITOR"}
    with open(SPINE, "a") as f: f.write(json.dumps(entry) + "\n")
    return entry

def check_connections():
    """Get ALL real network connections right now."""
    output = _run("ss -tnp 2>/dev/null")
    connections = []
    if output:
        for line in output.split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 5:
                state = parts[0]
                local = parts[3]
                remote = parts[4] if len(parts) > 4 else "?"
                process = parts[-1] if len(parts) > 5 else "?"
                if state == "ESTAB":
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', remote)
                    port_match = re.search(r':(\d+)$', remote)
                    connections.append({
                        "local": local,
                        "remote_ip": ip_match.group(1) if ip_match else "?",
                        "remote_port": port_match.group(1) if port_match else "?",
                        "process": process[:50]
                    })
    return connections

def check_listening():
    """Get all listening ports right now."""
    output = _run("ss -tlnp 2>/dev/null")
    services = []
    if output:
        for line in output.split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 4 and "LISTEN" in line:
                local = parts[3]
                port = local.split(':')[-1] if ':' in local else '?'
                bind = local.rsplit(':', 1)[0] if ':' in local else '?'
                process = parts[-1] if len(parts) > 4 else "?"
                exposed = bind not in ('127.0.0.1', '::1', '127.0.0.53', '127.0.0.54', '*')
                services.append({"port": port, "bind": bind, "process": process[:40], "exposed": exposed})
    return services

def check_firewall():
    """Check real firewall rules."""
    ufw = _run("sudo ufw status 2>/dev/null")
    iptables = _run("sudo iptables -L INPUT -n 2>/dev/null | head -20")
    return {"ufw": ufw or "NO_ACCESS", "iptables": iptables or "NO_ACCESS"}

def check_ssh_attempts():
    """Check for real SSH brute force attempts."""
    # journalctl
    journal = _run("journalctl -u sshd --since '1 hour ago' --no-pager 2>/dev/null")
    failed = []
    if journal:
        for line in journal.split('\n'):
            m = re.search(r'Failed password for (?:invalid user )?(\S+) from (\d+\.\d+\.\d+\.\d+)', line)
            if m: failed.append({"user": m.group(1), "ip": m.group(2)})
            m2 = re.search(r'Invalid user (\S+) from (\d+\.\d+\.\d+\.\d+)', line)
            if m2: failed.append({"user": m2.group(1), "ip": m2.group(2)})
    
    # Also check auth.log
    auth = Path("/var/log/auth.log")
    if auth.exists():
        try:
            with open(auth) as f:
                for line in f:
                    m = re.search(r'Failed password for (?:invalid user )?(\S+) from (\d+\.\d+\.\d+\.\d+)', line)
                    if m: failed.append({"user": m.group(1), "ip": m.group(2)})
        except: pass
    
    # Count by IP
    ip_counts = defaultdict(int)
    for f in failed: ip_counts[f["ip"]] += 1
    return {"total_failed": len(failed), "unique_ips": len(ip_counts), "top_attackers": dict(sorted(ip_counts.items(), key=lambda x: -x[1])[:10])}

def check_http_probes():
    """Check nginx access log for real HTTP probes."""
    log = Path("/var/log/nginx/access.log")
    probes = defaultdict(lambda: {"count": 0, "paths": set()})
    if log.exists():
        try:
            with open(log) as f:
                for line in f:
                    m = re.match(r'(\d+\.\d+\.\d+\.\d+).*?"(\w+)\s+(\S+)', line)
                    if m:
                        ip, method, path = m.group(1), m.group(2), m.group(3)
                        suspicious = any(p in path.lower() for p in ['.env', 'wp-admin', 'wp-login', 'admin', 'shell', 'cgi', 'phpmy', 'config', '.git', 'actuator', 'php'])
                        if suspicious:
                            probes[ip]["count"] += 1
                            probes[ip]["paths"].add(path[:60])
        except: pass
    return {ip: {"count": v["count"], "paths": list(v["paths"])[:5]} for ip, v in probes.items()}

def enrich_ip(ip):
    """Enrich an IP with real geolocation data."""
    geo = _json(f"http://ip-api.com/json/{ip}")
    if geo and geo.get("status") == "success":
        return {"ip": ip, "org": geo.get("org", "?"), "country": geo.get("countryCode", "?"),
                "city": geo.get("city", "?"), "isp": geo.get("isp", "?"), "hosting": geo.get("hosting", False)}
    return {"ip": ip, "org": "?", "country": "?", "city": "?", "isp": "?", "hosting": None}

def generate_block_rules(threat_ips):
    """Generate iptables/ufw rules for threatening IPs."""
    rules = []
    for ip, info in threat_ips.items():
        if info.get("attempts", 0) > 5 or info.get("count", 0) > 5:
            rule = f"sudo ufw deny from {ip}  # {info.get('org','?')} | {info.get('country','?')} | attempts={info.get('attempts',0)}"
            rules.append(rule)
    return rules

def full_scan():
    """Run a complete OSINT defense scan."""
    t0 = time.time()
    
    print("=" * 65)
    print(f"  EVEZ-OS OSINT DEFENDER — LIVE SCAN — {datetime.utcnow().isoformat()}")
    print("=" * 65)
    
    # L0: Our surface
    print("\n▸ L0: OUR ATTACK SURFACE")
    listening = check_listening()
    exposed = [s for s in listening if s["exposed"]]
    print(f"  Listening services: {len(listening)} | Exposed to internet: {len(exposed)}")
    for s in exposed:
        print(f"    ⚠ PORT {s['port']} ({s['process']}) bound to {s['bind']}")
    
    # L1: Active connections
    print("\n▸ L1: ACTIVE CONNECTIONS")
    connections = check_connections()
    external = [c for c in connections if c["remote_ip"] not in ("127.0.0.1", OUR_IP, "?")]
    print(f"  Total: {len(connections)} | External: {len(external)}")
    for c in external[:10]:
        print(f"    → {c['remote_ip']}:{c['remote_port']} ({c['process'][:30]})")
    
    # L2: SSH brute force
    print("\n▸ L2: SSH BRUTE FORCE (last hour)")
    ssh = check_ssh_attempts()
    print(f"  Failed attempts: {ssh['total_failed']} | Unique IPs: {ssh['unique_ips']}")
    if ssh["top_attackers"]:
        for ip, count in list(ssh["top_attackers"].items())[:5]:
            info = enrich_ip(ip)
            print(f"    🔴 {ip} → {count} attempts | {info['org']} | {info['country']}")
    
    # L3: HTTP probes
    print("\n▸ L3: HTTP PROBES")
    probes = check_http_probes()
    print(f"  Probing IPs: {len(probes)}")
    for ip, info in probes.items():
        p_info = enrich_ip(ip)
        print(f"    🔴 {ip} → {info['count']} probes | paths: {info['paths'][:3]} | {p_info['org']}")
    
    # L4: Firewall
    print("\n▸ L4: FIREWALL STATUS")
    fw = check_firewall()
    ufw_active = "active" in fw["ufw"].lower() if fw["ufw"] != "NO_ACCESS" else False
    print(f"  UFW: {'ACTIVE ✓' if ufw_active else 'INACTIVE ✗'}")
    
    # L5: Identify and isolate
    print("\n▸ L5: THREAT ACTORS & ISOLATION")
    threat_ips = {}
    for ip, count in ssh.get("top_attackers", {}).items():
        if count > 3:
            info = enrich_ip(ip)
            threat_ips[ip] = {"attempts": count, **info}
    for ip, info in probes.items():
        if ip not in threat_ips:
            threat_ips[ip] = {"count": info["count"], "paths": info["paths"]}
            threat_ips[ip].update(enrich_ip(ip))
    
    if threat_ips:
        rules = generate_block_rules(threat_ips)
        print(f"  Threat IPs: {len(threat_ips)} | Block rules: {len(rules)}")
        for r in rules:
            print(f"    {r}")
    else:
        print("  No active threats detected. Surface is clean (for now).")
        rules = []
    
    # Summary
    elapsed = round(time.time() - t0, 1)
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "our_ip": OUR_IP,
        "exposed_ports": [s["port"] for s in exposed],
        "external_connections": len(external),
        "ssh_failures": ssh["total_failed"],
        "http_probes": len(probes),
        "threat_ips": len(threat_ips),
        "block_rules": len(rules),
        "ufw_active": ufw_active,
        "scan_time_s": elapsed
    }
    
    # Write report
    with open(REPORT, "w") as f: json.dump(report, f, indent=2)
    
    # Spine
    spine_append("LIVE_SCAN", report)
    
    print(f"\n{'='*65}")
    print(f"  SCAN COMPLETE — {elapsed}s — Report: {REPORT}")
    print(f"  Spine: {SPINE}")
    print(f"  Next scan: run again or set up cron")
    print(f"{'='*65}")
    
    return report

if __name__ == "__main__":
    full_scan()
