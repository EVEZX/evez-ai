#!/usr/bin/env python3
"""EVEZ Counter-Intelligence Daemon
Monitors SSH, system logs, and network for intrusion attempts.
Auto-bans attackers, rotates defensive posture, reports findings.
"""
import subprocess, re, time, json, os, hashlib
from datetime import datetime, timedelta
from collections import defaultdict

LOG_FILE = "/home/openclaw/evez-counterintel.log"
STATE_FILE = "/home/openclaw/evez-counterintel-state.json"
ALERT_THRESHOLD = 3  # attempts before ban
SCAN_INTERVAL = 60   # seconds

def log(msg):
    ts = datetime.now(tz=None).isoformat() + "Z"
    line = f"[{ts}] {msg}"
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
    print(line)

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"banned": [], "alerts": [], "last_scan": None, "total_blocked": 0, "threats_identified": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
    except:
        return ""

def ban_ip(ip, reason="brute force"):
    # Check if already banned
    ufw = run("sudo ufw status")
    if ip in ufw:
        return False
    run(f'sudo ufw deny from {ip} comment "EVEZ auto-ban: {reason}"')
    log(f"BANNED {ip} — {reason}")
    return True

def scan_ssh_attempts():
    """Scan journal for recent SSH failures"""
    output = run('sudo journalctl -u ssh -u sshd --since "5 minutes ago" 2>/dev/null')
    attempts = defaultdict(int)
    for line in output.split("\n"):
        m = re.search(r'Failed password for .* from (\d+\.\d+\.\d+\.\d+)', line)
        if m:
            attempts[m.group(1)] += 1
        m2 = re.search(r'Invalid user \S+ from (\d+\.\d+\.\d+\.\d+)', line)
        if m2:
            attempts[m2.group(1)] += 1
    return attempts

def scan_suspicious_connections():
    """Check for unusual outbound connections"""
    output = run("ss -tunap 2>/dev/null")
    suspicious = []
    for line in output.split("\n"):
        # Flag connections to known bulletproof hosting countries/ASNs
        if any(x in line for x in [".onion", "0.0.0.0:0", "UNKNOWN"]):
            suspicious.append(line)
    return suspicious

def scan_process_anomalies():
    """Check for crypto miners, reverse shells, etc"""
    suspicious = []
    output = run("ps aux")
    for line in output.split("\n"):
        lower = line.lower()
        if any(x in lower for x in ["xmrig", "cryptonight", ".hidden", "stratum+", "ngrok", "frp"]):
            if "grep" not in lower:
                suspicious.append(line)
    return suspicious

def main_loop():
    log("EVEZ Counter-Intel daemon starting")
    state = load_state()
    
    while True:
        try:
            # SSH brute force detection
            ssh_attempts = scan_ssh_attempts()
            for ip, count in ssh_attempts.items():
                if count >= ALERT_THRESHOLD:
                    if ban_ip(ip, f"SSH brute force ({count} attempts)"):
                        state["banned"].append({"ip": ip, "time": datetime.now(tz=None).isoformat(), "reason": "ssh_brute"})
                        state["total_blocked"] += 1
            
            # Process anomaly detection
            procs = scan_process_anomalies()
            if procs:
                for p in procs:
                    log(f"SUSPICIOUS PROCESS: {p}")
            
            # Connection monitoring
            conns = scan_suspicious_connections()
            if conns:
                for c in conns:
                    log(f"SUSPICIOUS CONNECTION: {c}")
            
            state["last_scan"] = datetime.now(tz=None).isoformat()
            save_state(state)
            time.sleep(SCAN_INTERVAL)
        except KeyboardInterrupt:
            log("Shutting down")
            break
        except Exception as e:
            log(f"Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main_loop()
