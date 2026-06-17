"""
EVEZ Inter-Agent Health Monitor
Both Claw and AZRA POST here to register presence
"""
import json, time, os
from http.server import HTTPServer, BaseHTTPRequestHandler

STATE_FILE = "/home/openclaw/.openclaw/workspace/agent-bridge/state.json"

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"agents": {}, "events": []}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        state = load_state()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(state).encode())
    
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length)) if length else {}
        state = load_state()
        agent = data.get("agent", "unknown")
        state["agents"][agent] = {
            "last_heartbeat": time.time(),
            "host": data.get("host", ""),
            "status": data.get("status", "alive"),
            "metrics": data.get("metrics", {})
        }
        state["events"].append({
            "agent": agent,
            "type": "heartbeat",
            "ts": time.time(),
            "data": data
        })
        state["events"] = state["events"][-100:]
        save_state(state)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "agent": agent}).encode())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"Health monitor running on :{port}")
    server.serve_forever()
