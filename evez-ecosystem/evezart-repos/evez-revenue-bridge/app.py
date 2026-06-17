"""
EVEZ Revenue Bridge - Closes eigenvalue at -0.358.
Receives Stripe webhooks, logs to evez-spine, signals lord-evez666.
"""
import json, time, hashlib, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "evez-spine"))
from spine import Spine, Domain, Status

SPINE_FILE = Path(__file__).parent / "revenue_spine.json"

class RevenueBridge:
    def __init__(self):
        if SPINE_FILE.exists():
            self.spine = Spine.from_file(str(SPINE_FILE))
        else:
            self.spine = Spine(operator="viktor")

    def process_stripe_event(self, event_data):
        event_type = event_data.get("type", "unknown")
        if event_type == "charge.succeeded":
            obj = event_data.get("data", {}).get("object", {})
            amount_usd = obj.get("amount", 0) / 100
            event = self.spine.log_revenue(amount_usd=amount_usd, description=obj.get("description", ""), source="stripe")
            self.spine.export(str(SPINE_FILE))
            return {"status": "logged", "amount": amount_usd, "progress": self.spine._eigenvalue_progress}
        return {"status": "ignored", "type": event_type}

    def get_status(self):
        return self.spine.eigenvalue_status()

bridge = RevenueBridge()

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/health", "/status"):
            self._j(200, bridge.get_status())
        else:
            self._j(404, {"error": "not found"})
    def do_POST(self):
        if self.path == "/stripe-webhook":
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            try:
                r = bridge.process_stripe_event(json.loads(body))
                self._j(200, r)
            except Exception as e:
                self._j(400, {"error": str(e)})
        else:
            self._j(404, {"error": "not found"})
    def _j(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "9090"))
    print(f"Revenue Bridge on :{port}")
    HTTPServer(("0.0.0.0", port), H).serve_forever()
