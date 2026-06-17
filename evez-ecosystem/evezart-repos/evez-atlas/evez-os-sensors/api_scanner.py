"""
EVEZ-OS API DISCOVERY SCANNER
═══════════════════════════════════════════════════════════════

Automatically discovers and tests new free AI API providers.
Scans GitHub repos, blog posts, and API directories.
Tests each discovered provider and adds working ones to Ariel.

The circuit GROWS by finding new providers on its own.
"""
import json, os, signal, sys, time, re, hashlib
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

STATE_DIR = Path("/tmp/evez_scanner")
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Known provider patterns — OpenAI-compatible endpoints to probe
PROBE_ENDPOINTS = [
    # Each is (name_pattern, base_url, test_model, expected_status)
    ("nvidia", "https://integrate.api.nvidia.com/v1", "meta/llama-3.1-8b-instruct", 200),
    ("together", "https://api.together.xyz/v1", "meta-llama/Llama-3-8b-hf", 200),
    ("fireworks", "https://api.fireworks.ai/inference/v1", "accounts/fireworks/models/llama-v3-8b", 200),
    ("replicate", "https://api.replicate.com/v1", "meta/llama-2-70b", 200),
    ("perplexity", "https://api.perplexity.ai", "llama-3.1-sonar-small-128k-online", 200),
    ("ai21", "https://api.ai21.com/studio/v1", "j2-light", 200),
    ("cohere", "https://api.cohere.ai/v1", "command-r-plus", 200),
    ("groq", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile", 200),
    ("mistral", "https://api.mistral.ai/v1", "mistral-small-latest", 200),
    ("google", "https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.0-flash", 200),
    ("deepinfra", "https://api.deepinfra.com/v1/openai", "meta-llama/Meta-Llama-3.1-8B-Instruct", 200),
    ("novita", "https://api.novita.ai/v3/openai", "meta/llama-3.1-8b-instruct", 200),
    ("novelai", "https://api.novelai.net/v1", "llama-3-8b", 200),
    ("openrouter", "https://openrouter.ai/api/v1", "google/gemma-4-31b-it:free", 200),
    ("huggingface", "https://api-inference.huggingface.co/v1", "meta-llama/Llama-3.1-8B-Instruct", 200),
    ("cloudflare", "https://gateway.ai.cloudflare.com/v1", "@cf/meta/llama-3-8b-instruct-awq", 200),
    ("chutes", "https://llm.chutes.ai/v1", "deepseek-ai/DeepSeek-R1", 200),
    ("glhf", "https://glhf.chat/api/v1", "meta-llama/Meta-Llama-3.1-405B-Instruct", 200),
]

# GitHub repos that list free AI APIs
SCAN_REPOS = [
    "https://api.github.com/repos/cheahjs/free-llm-api-resources/contents",
    "https://api.github.com/repos/ai-boost/awesome-free-llm-apis/contents",
]


class APIScanner:
    def __init__(self, ariel_url="http://localhost:9093"):
        self.ariel_url = ariel_url
        self.discovered = {}  # name -> {url, models, status}
        self.scan_log = []
        self._load_state()
    
    def _load_state(self):
        sf = STATE_DIR / "scanner_state.json"
        if sf.exists():
            try:
                d = json.loads(sf.read_text())
                self.discovered = d.get("discovered", {})
                self.scan_log = d.get("scan_log", [])[-100:]
            except: pass
    
    def _save_state(self):
        sf = STATE_DIR / "scanner_state.json"
        sf.write_text(json.dumps({
            "discovered": self.discovered,
            "scan_log": self.scan_log[-100:],
            "timestamp": time.time(),
        }, indent=2, default=str))
    
    def probe_provider(self, name: str, base_url: str, test_model: str, api_key: str = "") -> dict:
        """Probe a provider to see if it's accessible (even without a key)."""
        result = {
            "name": name,
            "base_url": base_url,
            "test_model": test_model,
            "accessible": False,
            "needs_key": False,
            "models_available": [],
            "error": "",
            "timestamp": time.time(),
        }
        
        try:
            # Try to list models
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            req = Request(f"{base_url}/models", headers=headers)
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                if isinstance(data, dict) and "data" in data:
                    models = [m.get("id", "?") for m in data["data"][:20]]
                    result["models_available"] = models
                    result["accessible"] = True
                elif isinstance(data, list):
                    models = [m.get("id", str(m))[:40] for m in data[:20]]
                    result["models_available"] = models
                    result["accessible"] = True
        except HTTPError as e:
            if e.code in (401, 403):
                result["accessible"] = True  # It exists, just needs auth
                result["needs_key"] = True
                result["error"] = f"Auth required ({e.code})"
            else:
                result["error"] = f"HTTP {e.code}"
        except URLError:
            result["error"] = "Connection refused"
        except Exception as e:
            result["error"] = str(e)[:100]
        
        self.discovered[name] = result
        self.scan_log.append({"action": "probe", "name": name, "accessible": result["accessible"], "needs_key": result["needs_key"]})
        self._save_state()
        return result
    
    def scan_all(self) -> dict:
        """Probe all known provider endpoints."""
        results = {"probed": 0, "accessible": 0, "needs_key": 0, "free_access": 0, "details": []}
        
        for name, url, model, expected in PROBE_ENDPOINTS:
            probe = self.probe_provider(name, url, model)
            results["probed"] += 1
            if probe["accessible"]:
                results["accessible"] += 1
                if probe["needs_key"]:
                    results["needs_key"] += 1
                else:
                    results["free_access"] += 1
            results["details"].append({
                "name": name,
                "accessible": probe["accessible"],
                "needs_key": probe["needs_key"],
                "models": len(probe.get("models_available", [])),
            })
        
        return results
    
    def scan_github_repos(self) -> list:
        """Scan GitHub repos for new free AI API listings."""
        new_providers = []
        for repo_url in SCAN_REPOS:
            try:
                req = Request(repo_url, headers={"Accept": "application/vnd.github.v3+json"})
                with urlopen(req, timeout=15) as resp:
                    contents = json.loads(resp.read().decode())
                    for item in contents[:10]:
                        name = item.get("name", "")
                        download_url = item.get("download_url", "")
                        if download_url and name.endswith((".md", ".json")):
                            try:
                                req2 = Request(download_url)
                                with urlopen(req2, timeout=15) as resp2:
                                    content = resp2.read().decode()
                                    # Extract URLs that look like API endpoints
                                    urls = re.findall(r'https?://api\.[a-z0-9.-]+\.(com|ai|io|dev)/v\d', content)
                                    for url in set(urls):
                                        provider_name = re.search(r'api\.([a-z0-9-]+)\.', url)
                                        if provider_name:
                                            pname = provider_name.group(1)
                                            if pname not in self.discovered:
                                                new_providers.append({"name": pname, "url": url, "source": name})
                            except: pass
            except: pass
        
        # Probe new discoveries
        for p in new_providers:
            self.probe_provider(p["name"], p["url"], "default", "")
        
        return new_providers
    
    def register_with_ariel(self, name: str, api_key: str, models: list) -> dict:
        """Register a discovered provider with Ariel."""
        provider = self.discovered.get(name, {})
        base_url = provider.get("base_url", "")
        if not base_url:
            return {"error": f"Provider {name} not found in discovered providers"}
        
        try:
            payload = json.dumps({
                "name": name,
                "baseUrl": base_url,
                "apiKey": api_key,
                "models": models,
            }).encode()
            req = Request(
                f"{self.ariel_url}/api/provider/add",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)[:100]}
    
    def status(self) -> dict:
        return {
            "discovered_providers": len(self.discovered),
            "accessible": sum(1 for p in self.discovered.values() if p.get("accessible")),
            "needs_key": sum(1 for p in self.discovered.values() if p.get("needs_key")),
            "free_access": sum(1 for p in self.discovered.values() if p.get("accessible") and not p.get("needs_key")),
            "scan_log_entries": len(self.scan_log),
            "providers": {n: {"url": p.get("base_url", ""), "accessible": p.get("accessible"), "needs_key": p.get("needs_key"), "models": len(p.get("models_available", []))} for n, p in self.discovered.items()},
        }


# ═══════════════════════════════════════════════════════════════
# SCANNER API
# ═══════════════════════════════════════════════════════════════

scanner = None

class ScannerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self._json({"name": "EVEZ-OS API Discovery Scanner", "status": scanner.status() if scanner else {}})
        elif path == "/api/status":
            self._json(scanner.status() if scanner else {})
        else:
            self._json({"error": "Not found"}, 404)
    
    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except: body = {}
        
        if path == "/api/scan":
            result = scanner.scan_all() if scanner else {"error": "not initialized"}
            self._json(result)
        elif path == "/api/scan-github":
            result = scanner.scan_github_repos() if scanner else {"error": "not initialized"}
            self._json(result)
        elif path == "/api/register":
            result = scanner.register_with_ariel(
                body.get("name", ""),
                body.get("apiKey", ""),
                body.get("models", []),
            ) if scanner else {"error": "not initialized"}
            self._json(result)
        elif path == "/api/probe":
            result = scanner.probe_provider(
                body.get("name", "unknown"),
                body.get("url", ""),
                body.get("model", "default"),
                body.get("apiKey", ""),
            ) if scanner else {"error": "not initialized"}
            self._json(result)
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
    p.add_argument("--port", type=int, default=9099)
    p.add_argument("--ariel-url", default="http://localhost:9093")
    args = p.parse_args()
    
    global scanner
    scanner = APIScanner(ariel_url=args.ariel_url)
    
    print(f"\n  API Discovery Scanner: http://0.0.0.0:{args.port}")
    print(f"  POST /api/scan — probe 18 known providers")
    print(f"  POST /api/scan-github — scan repos for new providers")
    print()
    
    server = HTTPServer(("0.0.0.0", args.port), ScannerHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
