#!/usr/bin/env python3
"""
EVEZ Auto-Scaler
Monitors system health and recommends/auto-provisions cloud resources.
When RAM >90% or CPU >80% sustained, triggers scaling alerts.
"""
import os, json, time, subprocess, threading
from datetime import datetime, timezone
from pathlib import Path
import requests
from fastapi import FastAPI
import uvicorn

PTE = "http://localhost:8901"
FED = "http://localhost:8909"
MESHMIND = "http://localhost:8899"
THREAT = "http://localhost:8908"

def get_system_metrics():
    """Collect real system metrics."""
    metrics = {}
    
    # CPU
    try:
        load = os.getloadavg()
        metrics["load_1"] = round(load[0], 2)
        metrics["load_5"] = round(load[1], 2)
        metrics["load_15"] = round(load[2], 2)
        with open("/proc/cpuinfo") as f:
            metrics["cpu_count"] = sum(1 for line in f if "processor" in line)
    except:
        pass
    
    # RAM
    try:
        with open("/proc/meminfo") as f:
            info = dict(line.split(":") for line in f if ":" in line)
            total = int(info.get("MemTotal", "0").strip().split()[0])
            available = int(info.get("MemAvailable", "0").strip().split()[0])
            metrics["ram_total_mb"] = round(total / 1024)
            metrics["ram_available_mb"] = round(available / 1024)
            metrics["ram_used_pct"] = round((1 - available / total) * 100, 1) if total else 0
    except:
        pass
    
    # Disk
    try:
        r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        if r.ok:
            parts = r.stdout.strip().split("\n")[1].split()
            metrics["disk_used_pct"] = parts[4].replace("%", "")
            metrics["disk_available"] = parts[3]
    except:
        pass
    
    # Swap
    try:
        with open("/proc/swaps") as f:
            metrics["swap_active"] = len([l for l in f if l.strip() and "Filename" not in l]) > 0
    except:
        metrics["swap_active"] = False
    
    # Services
    try:
        r = subprocess.run(["systemctl", "list-units", "--type=service", "--state=active", "--no-pager"],
                          capture_output=True, text=True, timeout=5)
        metrics["active_services"] = len([l for l in r.stdout.split("\n") if "evez" in l or "openclaw" in l or "caddy" in l])
    except:
        pass
    
    # Uptime
    try:
        with open("/proc/uptime") as f:
            metrics["uptime_hours"] = round(float(f.read().split()[0]) / 3600, 1)
    except:
        pass
    
    metrics["timestamp"] = datetime.now(timezone.utc).isoformat()
    return metrics

def evaluate_scaling_needs(metrics):
    """Determine if we need to scale up or down."""
    alerts = []
    
    ram_pct = metrics.get("ram_used_pct", 0)
    if isinstance(ram_pct, str):
        ram_pct = float(ram_pct)
    
    if ram_pct > 90:
        alerts.append({
            "level": "critical",
            "type": "ram_pressure",
            "message": f"RAM at {ram_pct}% — need to either add resources or kill processes",
            "recommendation": "Deploy to Oracle Cloud ARM (24GB free) to offload services"
        })
    elif ram_pct > 80:
        alerts.append({
            "level": "warning",
            "type": "ram_high",
            "message": f"RAM at {ram_pct}% — approaching limit",
            "recommendation": "Consider offloading Factory/Research to Oracle Cloud"
        })
    
    load = metrics.get("load_1", 0)
    cpu_count = metrics.get("cpu_count", 1)
    if load > cpu_count * 0.8:
        alerts.append({
            "level": "warning",
            "type": "cpu_pressure",
            "message": f"Load {load} on {cpu_count} CPUs — near saturation",
            "recommendation": "Move AI inference to Modal (serverless GPU)"
        })
    
    # Check if failover gateway is up
    try:
        r = requests.get("http://localhost:19789/", timeout=3)
        if r.ok:
            alerts.append({
                "level": "info",
                "type": "rescue_gateway",
                "message": "Rescue gateway healthy — failover available"
            })
    except:
        alerts.append({
            "level": "warning",
            "type": "rescue_gateway",
            "message": "Rescue gateway not responding — failover at risk"
        })
    
    return alerts

# ─── FastAPI ──────────────────────────────────────────────────────
app = FastAPI(title="EVEZ Auto-Scaler", version="1.0.0")

@app.get("/")
async def root():
    metrics = get_system_metrics()
    alerts = evaluate_scaling_needs(metrics)
    
    # Route through PTE
    try:
        pte = requests.post(f"{PTE}/route", json={"action": "scale_check", "context": {"ram": metrics.get("ram_used_pct")}}, timeout=3).json()
        pte_node = pte.get("current_node", "unknown")
    except:
        pte_node = "unavailable"
    
    # Check federation
    try:
        fed = requests.get(f"{FED}/", timeout=3).json()
        active_gw = fed.get("status", {}).get("active_gateway", "unknown")
    except:
        active_gw = "unavailable"
    
    return {
        "service": "EVEZ Auto-Scaler",
        "metrics": metrics,
        "alerts": alerts,
        "pte_node": pte_node,
        "active_gateway": active_gw,
        "scaling_recommendation": {
            "immediate": "Oracle Cloud 24GB ARM (free) for compute offload",
            "near_term": "Modal serverless GPU ($30/mo free) for AI inference",
            "funding": "Google Startup $350K + NVIDIA Inception for H100/A100 access",
        }
    }

@app.get("/metrics")
async def metrics():
    return get_system_metrics()

@app.get("/alerts")
async def alerts():
    return {"alerts": evaluate_scaling_needs(get_system_metrics())}

if __name__ == "__main__":
    port = int(os.getenv("AUTOSCALER_PORT", "8910"))
    print(f"📈 EVEZ Auto-Scaler on port {port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
