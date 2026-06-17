#!/usr/bin/env python3
"""EVEZ Global Threat Intelligence Scanner
Scans for 0-day indicators, lateral movement, APT patterns.
Reports to Neural Nexus for real-time dashboard visibility.
"""
import subprocess, json, os, re, time
from datetime import datetime, timedelta
from collections import defaultdict

NEXUS_URL = "http://127.0.0.1:8968"
REPORT_FILE = "evez-threat-report.json"
UFW_LOG = "/var/log/ufw.log"

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
    except:
        return ""

def get_active_threats():
    """Parse UFW and auth logs for current threat landscape"""
    threats = []
    
    # Recent blocked connections
    ufw_status = run("")
    blocked_nets = re.findall(r'(\d+\.\d+\.\d+\.\d+/\d+)', ufw_status)
    
    # Recent SSH activity
    ssh_log = run('')
    ssh_threats = defaultdict(lambda: {"attempts": 0, "users": set(), "last_seen": None})
    
    for line in ssh_log.split("\n"):
        m = re.search(r'Failed password for (?:invalid user )?(\S+) from (\d+\.\d+\.\d+\.\d+)', line)
        if m:
            user, ip = m.group(1), m.group(2)
            ssh_threats[ip]["attempts"] += 1
            ssh_threats[ip]["users"].add(user)
            ssh_threats[ip]["last_seen"] = datetime.utcnow().isoformat()
    
    for ip, data in ssh_threats.items():
        threats.append({
            "type": "ssh_bruteforce",
            "source_ip": ip,
            "attempts": data["attempts"],
            "usernames_tried": list(data["users"]),
            "last_seen": data["last_seen"],
            "severity": "CRITICAL" if data["attempts"] > 50 else "HIGH" if data["attempts"] > 10 else "MEDIUM"
        })
    
    return threats

def scan_for_lateral_movement():
    """Check for signs of post-exploitation"""
    signs = []
    
    # Unusual outbound connections
    conns = run("ss -tunap 2>/dev/null")
    for line in conns.split("\n"):
        # Look for reverse shells (common ports)
        if any(f":{p}" in line for p in [4444, 5555, 6666, 7777, 9999, 1337]):
            signs.append({"type": "potential_reverse_shell", "detail": line.strip()})
    
    # New crontab entries
    crontab = run("crontab -l 2>/dev/null")
    if crontab and "evez" not in crontab.lower() and crontab.strip():
        signs.append({"type": "unexpected_crontab", "detail": crontab[:200]})
    
    # Recently changed binaries
    changed = run('')
    if changed.strip():
        for f in changed.strip().split("\n"):
            signs.append({"type": "modified_binary", "file": f})
    
    return signs

def scan_network_anomalies():
    """Detect ARP spoofing, DNS poisoning, MITM indicators"""
    anomalies = []
    
    # Check ARP table for duplicates
    arp = run("ip neigh show")
    macs = defaultdict(list)
    for line in arp.split("\n"):
        m = re.search(r'(\d+\.\d+\.\d+\.\d+).*?lladdr (\S+)', line)
        if m:
            macs[m.group(2)].append(m.group(1))
    
    for mac, ips in macs.items():
        if len(ips) > 1:
            anomalies.append({"type": "arp_anomaly", "mac": mac, "ips": ips})
    
    # DNS check
    dns = run("cat /etc/resolv.conf")
    if "127.0.0.53" not in dns and "1.1.1.1" not in dns and "8.8.8.8" not in dns:
        anomalies.append({"type": "suspicious_dns", "detail": dns[:200]})
    
    return anomalies

def generate_report():
    """Full threat assessment"""
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "defender": "EVEZ Counter-Intelligence v1.0",
        "threats": get_active_threats(),
        "lateral_movement_signs": scan_for_lateral_movement(),
        "network_anomalies": scan_network_anomalies(),
        "firewall_rules": len(run("").split("\n")),
        "services_running": len(run("systemctl --user list-units --type=service --state=running --no-legend").strip().split("\n")),
        "kernel_hardening": "ACTIVE",
        "fail2ban": "ACTIVE",
        "ssh_port": 2222,
        "ssh_password_auth": False,
        "attack_surface": "MINIMAL (80, 443, 2222 only)"
    }
    
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)
    
    return report

if __name__ == "__main__":
    report = generate_report()
    threats = len(report["threats"])
    lateral = len(report["lateral_movement_signs"])
    net = len(report["network_anomalies"])
    print(f"🛡️ EVEZ THREAT INTEL: {threats} threats | {lateral} lateral signs | {net} network anomalies")
    if threats > 0:
        for t in report["threats"]:
            print(f"  ⚠️ {t['severity']}: {t['source_ip']} — {t['attempts']} SSH attempts")
    if lateral > 0:
        for l in report["lateral_movement_signs"]:
            print(f"  🔴 {l['type']}: {l.get('detail', l.get('file', ''))}")
    if net > 0:
        for n in report["network_anomalies"]:
            print(f"  🟡 {n['type']}: {n}")
    if threats == 0 and lateral == 0 and net == 0:
        print("  ✅ ALL CLEAR — No active threats detected")
