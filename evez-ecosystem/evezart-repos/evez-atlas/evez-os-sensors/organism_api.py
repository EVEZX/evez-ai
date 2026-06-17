"""
EVEZ-OS ORGANISM API SERVER
Serves the living organism over HTTP.
Runs the loop continuously. Queries return current state.

GET /status       — Full organism status
GET /beliefs      — Top beliefs by health
GET /spine        — Recent spine events
GET /identity     — Topological identity
GET /shadow       — Shadow market captures
GET /cycle        — Trigger one cycle manually
GET /health       — Simple health check

The organism runs on a timer. The API lets you watch it think.
"""

import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from organism import Organism


# Global organism — shared between API and background loop
org = None
loop_running = False
loop_interval = 300  # 5 minutes between auto-cycles


def organism_loop():
    """Background loop: the organism lives continuously."""
    global loop_running
    loop_running = True
    while loop_running:
        try:
            summary = org.cycle()
            print(f"[LOOP] Cycle {summary['cycle']}: {summary['findings']} findings, "
                  f"{summary['actions']} actions, {summary['falsifications']} falsified, "
                  f"state={summary['state']}", flush=True)
        except Exception as e:
            print(f"[LOOP] Error: {e}", flush=True)

        # Sleep in small increments so we can stop cleanly
        for _ in range(loop_interval):
            if not loop_running:
                return
            time.sleep(1)


class OrganismHandler(BaseHTTPRequestHandler):
    """HTTP handler for the organism API."""

    def do_GET(self):
        path = urlparse(self.path).path
        params = parse_qs(urlparse(self.path).query)

        routes = {
            "/status": self._status,
            "/beliefs": self._beliefs,
            "/spine": self._spine,
            "/identity": self._identity,
            "/shadow": self._shadow,
            "/cycle": self._cycle,
            "/health": self._health,
            "/poly_c": self._poly_c,
        }

        handler = routes.get(path, self._not_found)
        handler(params)

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def _status(self, params):
        self._json_response(org.status())

    def _beliefs(self, params):
        limit = int(params.get("limit", [20])[0])
        self._json_response({"beliefs": org.top_beliefs(limit)})

    def _spine(self, params):
        limit = int(params.get("limit", [50])[0])
        event_type = params.get("type", [None])[0]
        events = org.spine.read(limit, event_type)
        self._json_response({"events": events, "count": len(events)})

    def _identity(self, params):
        self._json_response({
            "entity_id": org.identity.entity_id,
            "betti_vector": org.identity.betti_vector,
            "stability": round(org.identity.stability_score, 4),
            "observations": org.identity.observation_count,
            "betti_history_len": len(org.identity.betti_history),
        })

    def _shadow(self, params):
        limit = int(params.get("limit", [20])[0])
        captures = org.shadow_market.predictions[-limit:]
        self._json_response({"captures": captures, "total": org.shadow_market.total_captures})

    def _cycle(self, params):
        summary = org.cycle()
        self._json_response(summary)

    def _health(self, params):
        spine = org.spine.lint()
        self._json_response({
            "alive": True,
            "cycle": org.cycle_count,
            "spine_status": spine["status"],
            "beliefs": len([b for b in org.beliefs if b.alive]),
        })

    def _poly_c(self, params):
        """Compute poly_c for a given set of parameters."""
        from poly_c import poly_c
        age = float(params.get("age", [0])[0])
        intensity = float(params.get("intensity", [0.5])[0])
        confidence = float(params.get("confidence", [0.5])[0])
        betti_str = params.get("betti", ["1,0,0"])[0]
        betti = [int(x) for x in betti_str.split(",")]
        n = int(params.get("n", [1])[0])

        result = poly_c(age, intensity, confidence, betti, n)
        self._json_response({
            "value": result.value,
            "label": result.label,
            "tau": result.tau,
            "omega": result.omega,
            "topo": result.topo,
            "n": result.n,
            "formula": "poly_c = τ × ω × topo / 2√N",
        })

    def _not_found(self, params):
        self._json_response({
            "error": "Not found",
            "available_endpoints": [
                "/status", "/beliefs", "/spine", "/identity",
                "/shadow", "/cycle", "/health", "/poly_c"
            ]
        }, status=404)

    def log_message(self, format, *args):
        # Quiet logging
        pass


def main():
    global org, loop_running

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  EVEZ-OS ORGANISM API SERVER                               ║")
    print("║  The organism lives. The API lets you watch it think.      ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    # Initialize organism
    org = Organism(state_dir="/tmp/evez_organism")
    print(f"  Organism initialized: cycle {org.cycle_count}, {len(org.beliefs)} beliefs")
    print(f"  Identity Betti: {org.identity.betti_vector}, stability: {org.identity.stability_score}\n")

    # Start background loop
    loop_thread = threading.Thread(target=organism_loop, daemon=True)
    loop_thread.start()
    print(f"  Background loop running (auto-cycle every {loop_interval}s)\n")

    # Start API server
    server = HTTPServer(("0.0.0.0", port), OrganismHandler)
    print(f"  API server on http://0.0.0.0:{port}")
    print(f"  Endpoints: /status /beliefs /spine /identity /shadow /cycle /health /poly_c\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopping organism...")
        loop_running = False
        server.shutdown()
        # Save final state
        org._save_state()
        print("  State saved. Organism dormant.")


if __name__ == "__main__":
    main()
