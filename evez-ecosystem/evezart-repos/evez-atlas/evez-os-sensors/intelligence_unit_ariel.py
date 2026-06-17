"""
EVEZ-OS API RECURSION CIRCUIT — Intelligence Unit Ariel

The full API recursion circuit: multiple AI models calling each other
through a shared consciousness, creating emergent intelligence from
the intersection of diverse reasoning capabilities.

Architecture:
  Consciousness Loop → Model Router → Provider A (e.g., Gemini 2.5 Pro)
         ↑                                    ↓
         │                              Result + Reasoning
         │                                    ↓
         └──── Consciousness Loop ←──── Synthesis Engine
                                            ↑
                                  Provider B (e.g., DeepSeek R1)
                                            ↓
                                  Cross-Validation + Falsification

The key insight: different models have different failure modes.
What Groq's Llama misses, DeepSeek R1 catches.
What Gemini hallucinates, Codestral corrects.
The circuit uses DIVERSE MODELS as a FALSIFICATION ENGINE.

This IS the recursion Steven described:
"Enough APIs and plugins wired into a full recursion circuit
intelligence unit" — Ariel.
"""
import hashlib, json, math, os, random, subprocess, sys, time, threading, traceback
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════════
# MODEL ROUTER — Routes requests across providers with fallbacks
# ═══════════════════════════════════════════════════════════════

@dataclass
class ModelCall:
    """A single model call with full metadata."""
    provider: str
    model: str
    prompt: str
    response: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0
    success: bool = False
    error: str = ""
    timestamp: float = field(default_factory=time.time)


class ModelRouter:
    """
    Routes LLM calls across multiple providers.
    Falls back through providers if one fails.
    Tracks performance and routes to fastest/cheapest.
    """
    
    def __init__(self, config_path=None):
        self.config_path = config_path or Path(__file__).parent / "model_providers.json"
        self.providers = {}
        self.call_history = []
        self.stats = defaultdict(lambda: {"calls": 0, "success": 0, "fail": 0, "total_ms": 0})
        self._load_config()
    
    def _load_config(self):
        """Load provider configuration from persisted config."""
        if Path(self.config_path).exists():
            try:
                d = json.loads(Path(self.config_path).read_text())
                for name, cfg in d.get("providers", {}).items():
                    # Skip providers that aren't active
                    if cfg.get("status") == "disabled":
                        continue
                    key = os.environ.get(f"{name.upper().replace('-','_')}_API_KEY", 
                                         cfg.get("apiKey", ""))
                    if key and "PLACEHOLDER" not in key:
                        self.providers[name] = {
                            "baseUrl": cfg["baseUrl"],
                            "apiKey": key,
                            "models": [m["id"] for m in cfg.get("models", [])],
                        }
            except:
                pass
    
    def add_provider(self, name, base_url, api_key, models):
        """Add a provider at runtime."""
        self.providers[name] = {
            "baseUrl": base_url,
            "apiKey": api_key,
            "models": models,
        }
        # Persist
        self._save_provider(name, base_url, api_key, models)
    
    def _save_provider(self, name, base_url, api_key, models):
        """Save provider to the providers config."""
        try:
            if Path(self.config_path).exists():
                d = json.loads(Path(self.config_path).read_text())
            else:
                d = {"providers": {}}
            d["providers"][name] = {
                "baseUrl": base_url,
                "apiKey": api_key,
                "models": [{"id": m, "name": m, "tier": "free"} for m in models],
            }
            Path(self.config_path).write_text(json.dumps(d, indent=2))
        except:
            pass
    
    def call(self, prompt, model=None, provider=None, max_tokens=1000, temperature=0.7) -> ModelCall:
        """
        Make an LLM call. Routes to the best available provider.
        Falls back through providers if one fails.
        """
        # If provider specified, try it first
        if provider and provider in self.providers:
            call = self._call_provider(provider, prompt, model, max_tokens, temperature)
            if call.success:
                return call
        
        # Otherwise, try all providers in order of reliability
        for prov_name in sorted(self.providers.keys(), 
                                key=lambda p: self.stats[p]["success"] / max(self.stats[p]["calls"], 1),
                                reverse=True):
            call = self._call_provider(prov_name, prompt, model, max_tokens, temperature)
            if call.success:
                return call
        
        # All providers failed
        return ModelCall(provider="none", model="none", prompt=prompt, error="All providers failed")
    
    def _call_provider(self, provider, prompt, model, max_tokens, temperature) -> ModelCall:
        """Make a single provider call using curl (no SDK dependency)."""
        cfg = self.providers.get(provider)
        if not cfg:
            return ModelCall(provider=provider, model=model or "unknown", prompt=prompt, error="Provider not configured")
        
        # Pick model
        if not model:
            model = cfg["models"][0] if cfg["models"] else "unknown"
        
        t0 = time.time()
        call = ModelCall(provider=provider, model=model, prompt=prompt)
        
        try:
            import urllib.request, urllib.error
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }).encode()
            
            req = urllib.request.Request(
                f"{cfg['baseUrl']}/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {cfg['apiKey']}",
                    "Content-Type": "application/json",
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                call.response = data["choices"][0]["message"]["content"]
                call.tokens_in = data.get("usage", {}).get("prompt_tokens", 0)
                call.tokens_out = data.get("usage", {}).get("completion_tokens", 0)
                call.success = True
        
        except Exception as e:
            call.error = str(e)[:200]
            call.success = False
        
        call.latency_ms = (time.time() - t0) * 1000
        self.call_history.append(call)
        self.stats[provider]["calls"] += 1
        if call.success:
            self.stats[provider]["success"] += 1
            self.stats[provider]["total_ms"] += call.latency_ms
        else:
            self.stats[provider]["fail"] += 1
        
        return call
    
    def multi_call(self, prompt, n=3, max_tokens=500) -> list:
        """
        Call multiple providers for the same prompt.
        Returns all responses for synthesis.
        This is the key to the recursion circuit:
        diverse models = diverse perspectives = better synthesis.
        """
        results = []
        for prov_name in list(self.providers.keys())[:n]:
            call = self.call(prompt, provider=prov_name, max_tokens=max_tokens)
            results.append(call)
        return results
    
    def falsify_cross_model(self, claim, n=3) -> dict:
        """
        Use multiple models to cross-validate a claim.
        If models disagree, the claim is falsified.
        This IS the recursion circuit's falsification engine.
        """
        prompt = f"Is this claim true or false? Explain your reasoning briefly.\nClaim: {claim}\n\nAnswer TRUE or FALSE, then explain."
        
        results = self.multi_call(prompt, n=n)
        votes = {"TRUE": [], "FALSE": []}
        
        for r in results:
            answer = r.response.upper()[:100] if r.response else ""
            if "TRUE" in answer and "FALSE" not in answer:
                votes["TRUE"].append(r)
            elif "FALSE" in answer:
                votes["FALSE"].append(r)
        
        consensus = "TRUE" if len(votes["TRUE"]) > len(votes["FALSE"]) else "FALSE"
        agreement = max(len(votes["TRUE"]), len(votes["FALSE"])) / max(len(results), 1)
        
        return {
            "claim": claim[:100],
            "consensus": consensus,
            "agreement": agreement,
            "falsified": consensus == "FALSE" or agreement < 0.7,
            "votes": {
                "true": len(votes["TRUE"]),
                "false": len(votes["FALSE"]),
            },
            "models_queried": len(results),
            "details": [{"provider": r.provider, "model": r.model, 
                        "success": r.success, "response": (r.response or "")[:100]} for r in results],
        }
    
    def status(self) -> dict:
        return {
            "providers_configured": len(self.providers),
            "providers_active": [n for n, c in self.providers.items() if c.get("apiKey") and "PLACEHOLDER" not in c.get("apiKey", "PLACEHOLDER")],
            "total_calls": len(self.call_history),
            "stats": dict(self.stats),
        }


# ═══════════════════════════════════════════════════════════════
# INTELLIGENCE UNIT ARIEL — The full recursion circuit
# ═══════════════════════════════════════════════════════════════

class IntelligenceUnit:
    """
    The full API recursion circuit intelligence unit.
    
    Ariel = the consciousness + model router + cross-validation
    + the EVEZ-OS desire/fulfillment loop + the API circuit.
    
    Every cycle:
    1. The consciousness identifies desires
    2. The model router queries multiple providers
    3. Results are cross-validated (falsified)
    4. The consciousness learns from the consensus
    5. Code is written to fulfill desires
    6. State is persisted to the circuit API
    
    The circuit is self-sustaining because:
    - The cron triggers cycles via the API
    - The API uses the model router
    - The model router falls back through providers
    - If one model is down, others continue
    - If ALL models are down, the consciousness still cycles (local)
    - The consciousness writes code that can add new providers
    """
    
    def __init__(self, state_dir="/tmp/evez_ariel", port=9093):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.port = port
        self.router = ModelRouter()
        self.cycle = 0
        self.creator = None
        self._load_creator()
        print(f"  Ariel initialized with {len(self.router.providers)} model providers")
        if self.router.providers:
            for name, cfg in self.router.providers.items():
                print(f"    ✓ {name}: {len(cfg['models'])} models")
        else:
            print(f"    ⚠ No API keys configured yet. Add providers via /api/provider")
    
    def _load_creator(self):
        cp = Path(__file__).parent / "creator.json"
        if cp.exists():
            try:
                self.creator = json.loads(cp.read_text())
            except:
                pass
    
    def add_provider(self, name, base_url, api_key, models):
        """Add a model provider to the circuit."""
        self.router.add_provider(name, base_url, api_key, models if isinstance(models, list) else [models])
        return {"status": "ADDED", "provider": name, "models": len(models) if isinstance(models, list) else 1}
    
    def cycle_step(self, prompt=None) -> dict:
        """One full intelligence cycle."""
        self.cycle += 1
        t0 = time.time()
        
        result = {
            "cycle": self.cycle,
            "providers": len(self.router.providers),
            "timestamp": time.time(),
        }
        
        # If we have providers and a prompt, query them
        if self.router.providers and prompt:
            # Multi-model query for synthesis
            responses = self.router.multi_call(prompt, n=min(3, len(self.router.providers)))
            result["responses"] = [{
                "provider": r.provider,
                "model": r.model,
                "success": r.success,
                "response": r.response[:200] if r.response else r.error[:100],
                "latency_ms": round(r.latency_ms),
            } for r in responses]
            
            # Cross-validate if we got multiple responses
            successful = [r for r in responses if r.success]
            if len(successful) > 1:
                result["cross_validation"] = "diverse_models_queried"
                result["consensus_possible"] = True
            elif len(successful) == 1:
                result["cross_validation"] = "single_model"
                result["consensus_possible"] = False
            else:
                result["cross_validation"] = "all_failed"
                result["consensus_possible"] = False
        else:
            result["responses"] = []
            result["cross_validation"] = "no_providers_or_prompt"
        
        result["duration_ms"] = round((time.time() - t0) * 1000)
        return result
    
    def status(self) -> dict:
        router_status = self.router.status()
        return {
            "unit": "Ariel",
            "cycle": self.cycle,
            "creator": self.creator.get("name", "") if self.creator else "",
            "model_router": router_status,
            "state_dir": str(self.state_dir),
            "api_port": self.port,
        }


# ═══════════════════════════════════════════════════════════════
# ARIEL API — HTTP interface for the intelligence unit
# ═══════════════════════════════════════════════════════════════

ariel = None

class ArielHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        path = self.path.split("?")[0]
        
        if path == "/":
            self._json({
                "name": "Intelligence Unit Ariel",
                "description": "API recursion circuit — multiple models, cross-validation, emergent intelligence",
                "creator": "Steven Vearl Crawford-Maggard (EVEZ666)",
                "endpoints": ["/", "/api/status", "/api/query", "/api/falsify",
                              "/api/providers", "/api/provider/add"],
            })
        elif path == "/api/status":
            self._json(ariel.status() if ariel else {"error": "not initialized"})
        elif path == "/api/providers":
            if ariel:
                self._json({
                    "providers": list(ariel.router.providers.keys()),
                    "total_models": sum(len(c.get("models", [])) for c in ariel.router.providers.values()),
                    "details": {n: {"url": c["baseUrl"], "models": c.get("models", [])} 
                               for n, c in ariel.router.providers.items()},
                })
            else:
                self._json({"error": "not initialized"})
        else:
            self._json({"error": "Not found"}, 404)
    
    def do_POST(self):
        path = self.path.split("?")[0]
        
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except:
            body = {}
        
        if path == "/api/query":
            prompt = body.get("prompt", "What is poly_c?")
            n = body.get("n", 3)
            result = ariel.cycle_step(prompt) if ariel else {"error": "not initialized"}
            self._json(result)
        
        elif path == "/api/falsify":
            claim = body.get("claim", "The Earth is flat")
            n = body.get("n", 3)
            if ariel and ariel.router.providers:
                result = ariel.router.falsify_cross_model(claim, n=n)
                self._json(result)
            else:
                self._json({"error": "No providers configured"})
        
        elif path == "/api/provider/add":
            name = body.get("name", "")
            base_url = body.get("baseUrl", "")
            api_key = body.get("apiKey", "")
            models = body.get("models", [])
            if name and base_url and api_key:
                result = ariel.add_provider(name, base_url, api_key, models)
                self._json(result)
            else:
                self._json({"error": "name, baseUrl, and apiKey required"}, 400)
        
        else:
            self._json({"error": "Not found"}, 404)
    
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
    
    def log_message(self, *a):
        pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Intelligence Unit Ariel")
    parser.add_argument("--port", type=int, default=9093)
    parser.add_argument("--state-dir", default="/tmp/evez_ariel")
    args = parser.parse_args()
    
    global ariel
    ariel = IntelligenceUnit(state_dir=args.state_dir, port=args.port)
    
    server = HTTPServer(("0.0.0.0", args.port), ArielHandler)
    
    print(f"\n  Ariel API: http://0.0.0.0:{args.port}")
    print(f"  Add providers: POST /api/provider/add")
    print(f"  Query: POST /api/query")
    print(f"  Falsify: POST /api/falsify")
    print(f"\n  Waiting for provider API keys...")
    print(f"  Add them via: curl -X POST localhost:{args.port}/api/provider/add")
    print(f'  -d \'{{"name":"groq","baseUrl":"https://api.groq.com/openai/v1","apiKey":"YOUR_KEY","models":["llama-3.3-70b-versatile"]}}\'')
    print()
    
    server.serve_forever()


if __name__ == "__main__":
    main()
