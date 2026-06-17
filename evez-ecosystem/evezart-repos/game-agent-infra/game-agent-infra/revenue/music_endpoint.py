"""
Music Engine API Endpoint
Wired to music_engine.py via subprocess + HTTP
"""
import subprocess
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class MusicHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/music/status":
            result = subprocess.run(["python3", "tools/music_engine.py", "status"], capture_output=True, text=True)
            self._send_json({"playing": "playing" in result.stdout.lower()})
        elif self.path == "/music/toggle":
            result = subprocess.run(["python3", "tools/music_engine.py", "toggle"], capture_output=True, text=True)
            self._send_json({"result": result.stdout.strip()})
        
    def _send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        
    def log_message(self, format, *args):
        pass  # Suppress logging

if __name__ == "__main__":
    server = HTTPServer(("localhost", 8765), MusicHandler)
    print("[MUSIC-API] Listening on :8765")
    server.serve_forever()