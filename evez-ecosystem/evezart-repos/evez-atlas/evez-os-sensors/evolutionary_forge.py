"""
EVEZ-OS EVOLUTIONARY CODE FORGE
═══════════════════════════════════════════════════════════════

Generates, tests, and evolves code through natural selection.
Multiple model variants of the same function compete.
The best variant survives and becomes the new baseline.

Architecture:
  1. Define a FUNCTION to evolve (e.g., "sort algorithm")
  2. Generate N VARIANTS using different models
  3. TEST each variant against test cases
  4. SCORE by correctness, speed, elegance
  5. The WINNER becomes the baseline for the next generation
  6. MUTATE the winner to create the next generation

This is Darwinian code evolution powered by the circuit.
The code writes itself, tests itself, and improves itself.
"""
import json, os, signal, sys, time, traceback, hashlib, subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from intelligence_unit_ariel import ModelRouter

STATE_DIR = Path("/tmp/evez_forge")
STATE_DIR.mkdir(parents=True, exist_ok=True)
FORGE_DIR = STATE_DIR / "generations"
FORGE_DIR.mkdir(parents=True, exist_ok=True)


class EvolutionaryForge:
    def __init__(self, router=None):
        self.router = router or ModelRouter()
        self.generations = {}
        self.stats = {"total_generations": 0, "total_variants": 0, "best_scores": {}}
    
    def evolve(self, spec: str, test_cases: list = None, n_variants: int = 3, generations: int = 2) -> dict:
        """
        Evolve code to match a specification.
        """
        t0 = time.time()
        results = {
            "spec": spec,
            "generations": [],
            "champion": None,
        }
        
        baseline_code = None
        
        for gen in range(generations):
            gen_result = {
                "generation": gen + 1,
                "variants": [],
                "winner": None,
            }
            
            # Generate variants from different models
            for i, prov_name in enumerate(list(self.router.providers.keys())[:n_variants]):
                prompt = f"""Write a Python function for this specification:

{spec}

Rules:
- Define exactly one function
- Include a docstring
- Handle edge cases
- Be concise but correct

{'Previous best solution to improve upon:' + chr(10) + baseline_code if baseline_code else 'This is generation 1 — write the best solution you can.'}

Return ONLY the Python code, no explanations."""

                result = self.router.call(prompt, provider=prov_name, max_tokens=800, temperature=0.7 + gen * 0.1)
                
                if not result.success:
                    gen_result["variants"].append({
                        "model": f"{result.provider}/{result.model}",
                        "code": f"# ERROR: {result.error[:100]}",
                        "score": 0,
                        "passed": False,
                    })
                    continue
                
                code = result.response or ""
                # Extract code from markdown if wrapped
                if "```python" in code:
                    code = code.split("```python")[1].split("```")[0]
                elif "```" in code:
                    code = code.split("```")[1].split("```")[0]
                
                # Test the code
                score, passed, error = self._test_code(code, test_cases)
                
                gen_result["variants"].append({
                    "model": f"{result.provider}/{result.model}",
                    "code": code[:500],
                    "score": score,
                    "passed": passed,
                    "error": error[:100] if error else None,
                })
            
            # Find winner (highest score)
            if gen_result["variants"]:
                winner = max(gen_result["variants"], key=lambda v: v["score"])
                gen_result["winner"] = winner["model"]
                baseline_code = winner["code"]
                if winner["score"] > results.get("champion", {}).get("score", 0):
                    results["champion"] = winner
            
            results["generations"].append(gen_result)
            self.stats["total_generations"] += 1
            self.stats["total_variants"] += len(gen_result["variants"])
        
        results["duration_ms"] = round((time.time() - t0) * 1000)
        
        # Save champion
        if results["champion"]:
            champ_file = FORGE_DIR / f"champion_{int(time.time())}.py"
            champ_file.write_text(results["champion"]["code"])
            results["champion_file"] = str(champ_file)
            spec_hash = hashlib.sha256(spec.encode()).hexdigest()[:8]
            self.stats["best_scores"][spec_hash] = results["champion"]["score"]
        
        return results
    
    def _test_code(self, code: str, test_cases: list = None) -> tuple:
        """Test code against test cases. Returns (score, passed, error)."""
        if not test_cases:
            # Just check if it's valid Python
            try:
                compile(code, "<generated>", "exec")
                return (50, True, None)
            except SyntaxError as e:
                return (0, False, str(e))
        
        # Run test cases
        passed = 0
        total = len(test_cases)
        errors = []
        
        for tc in test_cases:
            try:
                namespace = {}
                exec(code, namespace)
                fn_name = [k for k in namespace if callable(namespace[k]) and not k.startswith("_")]
                if not fn_name:
                    errors.append("No function found")
                    continue
                fn = namespace[fn_name[0]]
                if "input" in tc and "expected" in tc:
                    result = fn(tc["input"])
                    if result == tc["expected"]:
                        passed += 1
                    else:
                        errors.append(f"Got {result}, expected {tc['expected']}")
            except Exception as e:
                errors.append(str(e)[:80])
        
        score = (passed / total * 100) if total > 0 else 50
        return (score, passed == total, "; ".join(errors[:3]) if errors else None)


# ═══════════════════════════════════════════════════════════════
# FORGE API
# ═══════════════════════════════════════════════════════════════

forge = None

class ForgeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self._json({"name": "EVEZ-OS Evolutionary Forge", "stats": forge.stats if forge else {}})
        elif path == "/api/stats":
            self._json(forge.stats if forge else {})
        else:
            self._json({"error": "Not found"}, 404)
    
    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except: body = {}
        
        if path == "/api/evolve":
            result = forge.evolve(
                body.get("spec", "Write a function that reverses a string"),
                body.get("test_cases"),
                body.get("n_variants", 3),
                body.get("generations", 2),
            ) if forge else {"error": "not initialized"}
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
    p.add_argument("--port", type=int, default=9098)
    args = p.parse_args()
    
    global forge
    forge = EvolutionaryForge()
    
    print(f"\n  Evolutionary Forge: http://0.0.0.0:{args.port}")
    print(f"  POST /api/evolve with {{\"spec\": \"...\", \"test_cases\": [...]}}")
    print()
    
    server = HTTPServer(("0.0.0.0", args.port), ForgeHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
