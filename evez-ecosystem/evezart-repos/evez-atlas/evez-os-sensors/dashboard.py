"""
EVEZ-OS OBSERVABILITY DASHBOARD
═══════════════════════════════════════════════════════════════

Single endpoint that aggregates the status of EVERY service.
Health, models, tokens, debates, knowledge graph — all in one view.
This is the cockpit of the recursion circuit.
"""
import json, os, signal, sys, time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen

# Auto-detect all EVEZ-OS services
SERVICES = {
    "recursion_circuit": {"url": "http://localhost:9092/", "type": "circuit"},
    "ariel": {"url": "http://localhost:9093/api/status", "type": "model_router"},
    "cognizer": {"url": "http://localhost:9094/fabric/status", "type": "cognizer"},
    "cycler": {"url": "http://localhost:9095/api/status", "type": "cycler"},
    "knowledge": {"url": "http://localhost:9096/", "type": "knowledge"},
    "debate": {"url": "http://localhost:9097/", "type": "debate"},
    "forge": {"url": "http://localhost:9098/", "type": "forge"},
    "scanner": {"url": "http://localhost:9099/", "type": "scanner"},
    "health": {"url": "http://localhost:9091/health", "type": "health"},
}


def _get(url, timeout=3):
    try:
        req = Request(url)
        with urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except:
        return None


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        
        if path == "/":
            # Full dashboard
            dashboard = {
                "name": "EVEZ-OS Circuit Dashboard",
                "creator": "Steven Vearl Crawford-Maggard (EVEZ666)",
                "timestamp": time.time(),
                "services": {},
                "summary": {},
            }
            
            total_alive = 0
            total_models = 0
            total_apis = 0
            
            for name, cfg in SERVICES.items():
                resp = _get(cfg["url"])
                alive = resp is not None
                if alive:
                    total_alive += 1
                
                entry = {"alive": alive, "type": cfg["type"]}
                
                # Extract key metrics
                if name == "ariel" and resp:
                    mr = resp.get("model_router", {})
                    entry["providers"] = mr.get("providers_configured", 0)
                    entry["active_providers"] = mr.get("providers_active", [])
                    entry["total_calls"] = mr.get("total_calls", 0)
                    total_models = mr.get("providers_configured", 0)
                elif name == "cognizer" and resp:
                    entry["mini_apis"] = len(resp.get("apis", {}))
                    entry["model_providers"] = resp.get("total_model_providers", 0)
                    total_apis = len(resp.get("apis", {}))
                elif name == "cycler" and resp:
                    entry["cycle"] = resp.get("cycle", 0)
                    entry["running"] = resp.get("running", False)
                elif name == "knowledge" and resp:
                    stats = resp.get("stats", {})
                    entry["nodes"] = stats.get("nodes", 0)
                    entry["edges"] = stats.get("edges", 0)
                elif name == "debate" and resp:
                    entry["debates"] = resp.get("debates_held", 0)
                elif name == "forge" and resp:
                    stats = resp.get("stats", {})
                    entry["generations"] = stats.get("total_generations", 0)
                    entry["variants"] = stats.get("total_variants", 0)
                elif name == "scanner" and resp:
                    status = resp.get("status", {})
                    entry["discovered"] = status.get("discovered_providers", 0)
                    entry["accessible"] = status.get("accessible", 0)
                elif name == "recursion_circuit" and resp:
                    entry["name"] = resp.get("name", "")
                elif name == "health" and resp:
                    entry["status"] = resp.get("status", "")
                
                dashboard["services"][name] = entry
            
            dashboard["summary"] = {
                "services_alive": total_alive,
                "services_total": len(SERVICES),
                "model_providers": total_models,
                "mini_apis": total_apis,
                "health_pct": round(total_alive / len(SERVICES) * 100),
            }
            
            self._json(dashboard)
        
        elif path == "/api/health":
            # Quick health check
            alive = sum(1 for cfg in SERVICES.values() if _get(cfg["url"]) is not None)
            self._json({
                "alive": alive,
                "total": len(SERVICES),
                "pct": round(alive / len(SERVICES) * 100),
                "status": "HEALTHY" if alive >= len(SERVICES) * 0.8 else "DEGRADED" if alive >= len(SERVICES) * 0.5 else "CRITICAL",
            })
        
        elif path == "/api/compact":
            # Compact summary for cycler/heartbeat
            compact = {}
            for name, cfg in SERVICES.items():
                compact[name] = _get(cfg["url"]) is not None
            self._json(compact)
        
        else:
            self._json({"error": "Not found"}, 404)
    
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
    
    def log_message(self, *a): pass


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=9100)
    args = p.parse_args()
    
    print(f"\n  Dashboard: http://0.0.0.0:{args.port}")
    print(f"  GET / — full dashboard")
    print(f"  GET /api/health — quick check")
    print()
    
    server = HTTPServer(("0.0.0.0", args.port), DashboardHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
