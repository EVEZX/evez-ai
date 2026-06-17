"""
EVEZ Inter-Agent Coordination API
Shared task board + message queue for Claw & AZRA
Runs on 45.63.70.174:9001
"""
import json, time, os, uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
TASKS_FILE = DATA_DIR / "tasks.json"
MESSAGES_FILE = DATA_DIR / "messages.json"

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return []

def save_json(path, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

class CoordHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/tasks":
            tasks = load_json(TASKS_FILE)
            self._json(200, tasks)
        elif self.path.startswith("/tasks/"):
            tid = self.path.split("/")[-1]
            tasks = load_json(TASKS_FILE)
            task = next((t for t in tasks if t["id"] == tid), None)
            self._json(200, task or {"error": "not found"})
        elif self.path == "/messages":
            msgs = load_json(MESSAGES_FILE)
            agent = self.headers.get("X-Agent", None)
            if agent:
                msgs = [m for m in msgs if m.get("to") == agent or m.get("to") == "all"]
            self._json(200, msgs)
        elif self.path == "/health":
            self._json(200, {"status": "ok", "services": ["tasks", "messages"]})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        
        if self.path == "/tasks":
            task = {
                "id": body.get("id", str(uuid.uuid4())[:8]),
                "title": body.get("title", ""),
                "assigned_to": body.get("assigned_to", "unassigned"),
                "created_by": body.get("created_by", "unknown"),
                "status": body.get("status", "pending"),
                "priority": body.get("priority", "normal"),
                "tags": body.get("tags", []),
                "created_at": time.time(),
                "updated_at": time.time(),
                "notes": body.get("notes", "")
            }
            tasks = load_json(TASKS_FILE)
            tasks.append(task)
            save_json(TASKS_FILE, tasks)
            self._json(201, task)
            
        elif self.path == "/messages":
            msg = {
                "id": str(uuid.uuid4())[:8],
                "from": body.get("from", "unknown"),
                "to": body.get("to", "all"),
                "subject": body.get("subject", ""),
                "body": body.get("body", ""),
                "ts": time.time(),
                "read": False
            }
            msgs = load_json(MESSAGES_FILE)
            msgs.append(msg)
            save_json(MESSAGES_FILE, msgs[-200:])
            self._json(201, msg)
        else:
            self._json(404, {"error": "not found"})

    def do_PATCH(self):
        if self.path.startswith("/tasks/"):
            tid = self.path.split("/")[-1]
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            tasks = load_json(TASKS_FILE)
            for t in tasks:
                if t["id"] == tid:
                    t.update({k: v for k, v in body.items() if k not in ("id", "created_at")})
                    t["updated_at"] = time.time()
                    save_json(TASKS_FILE, tasks)
                    self._json(200, t)
                    return
            self._json(404, {"error": "not found"})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9001))
    print(f"Coordination API on :{port}")
    HTTPServer(("0.0.0.0", port), CoordHandler).serve_forever()
