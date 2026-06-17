"""
EVEZ Ecosystem Status Dashboard
Served by AZRA on :9002
Shows real-time status of both boxes, all services, tasks, agents
"""
import json, time, os, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

LOCAL_SERVICES = [
    (18789, "OpenClaw Gateway"),
    (6969, "Code Server"),
    (9000, "Health Monitor"),
    (9001, "Coordination API"),
    (8899, "Mem0"),
    (8898, "Embedder"),
    (8888, "SearXNG"),
]

REMOTE_SERVICES = [
    (8000, "EVEZ OS"),
    (8001, "Signal Detect"),
    (8002, "OpenTree"),
    (8003, "OpenGraph"),
    (8004, "Vector Store"),
    (5432, "PostgreSQL", False),  # No HTTP
    (4222, "NATS", False),  # No HTTP
]

REMOTE_HOST = "45.63.66.247"

def check_service(host, port, name, http=True):
    if not http:
        import socket
        try:
            s = socket.socket()
            s.settimeout(2)
            s.connect((host, port))
            s.close()
            return {"port": port, "name": name, "status": "UP"}
        except:
            return {"port": port, "name": name, "status": "DOWN"}
    try:
        url = f"http://{host}:{port}/health" if http else f"http://{host}:{port}/"
        req = urllib.request.Request(url, headers={"User-Agent": "evez-status/1.0"})
        with urllib.request.urlopen(req, timeout=3) as r:
            return {"port": port, "name": name, "status": "UP", "code": r.status}
    except:
        try:
            url = f"http://{host}:{port}/"
            req = urllib.request.Request(url, headers={"User-Agent": "evez-status/1.0"})
            with urllib.request.urlopen(req, timeout=3) as r:
                return {"port": port, "name": name, "status": "UP", "code": r.status}
        except:
            return {"port": port, "name": name, "status": "DOWN"}

def get_full_status():
    local = [check_service("localhost", p, n) for p, n in LOCAL_SERVICES]
    remote = []
    for entry in REMOTE_SERVICES:
        port, name = entry[0], entry[1]
        http = entry[2] if len(entry) > 2 else True
        remote.append(check_service(REMOTE_HOST, port, name, http))
    
    # Get tasks
    try:
        req = urllib.request.Request("http://localhost:9001/tasks")
        with urllib.request.urlopen(req, timeout=2) as r:
            tasks = json.loads(r.read())
    except:
        tasks = []
    
    # Get health
    try:
        req = urllib.request.Request("http://localhost:9000")
        with urllib.request.urlopen(req, timeout=2) as r:
            health = json.loads(r.read())
    except:
        health = {"agents": {}}
    
    return {
        "timestamp": time.time(),
        "azra_box": {"host": "45.63.70.174", "services": local},
        "claw_box": {"host": "45.63.66.247", "services": remote},
        "agents": health.get("agents", {}),
        "tasks": {"total": len(tasks), "pending": len([t for t in tasks if t.get("status") == "pending"]), "done": len([t for t in tasks if t.get("status") == "done"])},
    }

class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/status":
            data = get_full_status()
            if "text" in self.headers.get("Accept", ""):
                self._text(200, data)
            else:
                self._json(200, data)
        elif self.path == "/health":
            self._json(200, {"status": "ok"})
        else:
            self._json(404, {"error": "not found"})
    
    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, indent=2).encode())
    
    def _text(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        lines = ["🔥 EVEZ ECOSYSTEM STATUS", f"   Updated: {time.strftime('%H:%M:%S UTC', time.gmtime(data['timestamp']))}", ""]
        for box_name, box_key in [("AZRA 🔥 (45.63.70.174)", "azra_box"), ("CLAW 🦀 (45.63.66.247)", "claw_box")]:
            lines.append(f"  {box_name}")
            for s in data[box_key]["services"]:
                icon = "✅" if s["status"] == "UP" else "❌"
                lines.append(f"    {icon} {s['name']} :{s['port']}")
            lines.append("")
        lines.append(f"  Agents: {', '.join(data['agents'].keys()) or 'none'}")
        lines.append(f"  Tasks: {data['tasks']['total']} total, {data['tasks']['pending']} pending, {data['tasks']['done']} done")
        self.wfile.write("\n".join(lines).encode())
    
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9002))
    print(f"EVEZ Status Dashboard on :{port}")
    HTTPServer(("0.0.0.0", port), StatusHandler).serve_forever()
