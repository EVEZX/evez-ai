"""OpenClaw + EVEZ-OS Health Check Server.
Run: python3 openclaw_health.py
Serves health status on port 9091."""
import json, os, subprocess, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

def get_health():
    health = {"timestamp": time.time(), "status": "UNKNOWN"}
    
    # OpenClaw gateway
    try:
        r = subprocess.run(["pgrep", "-f", "openclaw-gateway"], capture_output=True, text=True)
        health["openclaw_gateway"] = {"running": bool(r.stdout.strip()), "pid": r.stdout.strip() or None}
    except: health["openclaw_gateway"] = {"running": False}
    
    # EVEZ-OS daemon
    try:
        r = subprocess.run(["pgrep", "-f", "autonomous_daemon"], capture_output=True, text=True)
        health["evez_os_daemon"] = {"running": bool(r.stdout.strip()), "pid": r.stdout.strip() or None}
    except: health["evez_os_daemon"] = {"running": False}
    
    # EVEZ-OS daemon health
    try:
        dh = Path("/tmp/evez_daemon/daemon_health.json")
        if dh.exists():
            health["evez_os_status"] = json.loads(dh.read_text())
    except: pass
    
    # Crontab
    try:
        r = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        health["crontab_entries"] = len([l for l in r.stdout.strip().split("\n") if l and not l.startswith("#")])
    except: health["crontab_entries"] = 0
    
    # Uptime
    try:
        uptime = float(Path("/proc/uptime").read_text().split()[0])
        health["uptime_seconds"] = uptime
    except: pass
    
    health["status"] = "HEALTHY" if health.get("openclaw_gateway", {}).get("running") else "DEGRADED"
    return health

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            h = get_health()
            self.send_response(200 if h["status"] == "HEALTHY" else 503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(h, indent=2, default=str).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"service": "openclaw+evez-os", "endpoints": ["/health"]}).encode())
    def log_message(self, *a): pass

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 9091), Handler)
    print("Health check on :9091/health")
    server.serve_forever()
