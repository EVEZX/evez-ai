"""
EVEZ-OS MULTI-MODEL DEBATE ENGINE
═══════════════════════════════════════════════════════════════

Makes multiple models ARGUE about a topic.
The debate reveals truth through dialectic:
  Thesis (Model A) → Antithesis (Model B) → Synthesis (Model C)

Each model sees the others' arguments and must respond.
The debate continues for N rounds, then a final synthesis
is produced using the strongest arguments from each side.

This is MORE than falsification — it's structured disagreement.
The circuit becomes wiser because models challenge each other.
"""
import json, os, signal, sys, time, threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from intelligence_unit_ariel import ModelRouter

ARIEL_URL = os.environ.get("ARIEL_URL", "http://localhost:9093")
STATE_DIR = Path("/tmp/evez_debate")
STATE_DIR.mkdir(parents=True, exist_ok=True)


class DebateEngine:
    def __init__(self, router=None):
        self.router = router or ModelRouter()
        self.debates = []
        self._load_state()
    
    def _load_state(self):
        sf = STATE_DIR / "debates.json"
        if sf.exists():
            try: self.debates = json.loads(sf.read_text()).get("debates", [])[-50:]
            except: pass
    
    def _save_state(self):
        sf = STATE_DIR / "debates.json"
        sf.write_text(json.dumps({"debates": self.debates[-50:], "timestamp": time.time()}, indent=2, default=str))
    
    def debate(self, topic: str, rounds: int = 3, n_models: int = 3) -> dict:
        """
        Run a multi-model debate on a topic.
        Returns the full debate transcript and synthesis.
        """
        t0 = time.time()
        transcript = []
        
        # Get initial positions from different models
        positions = []
        for i, prov_name in enumerate(list(self.router.providers.keys())[:n_models]):
            role = "PRO" if i % 2 == 0 else "CON"
            prompt = f"""You are arguing the {role} position on this topic: {topic}

State your position clearly and give your strongest argument in 2-3 sentences.
Be specific. Use evidence. Do not be neutral — take a firm stance."""
            
            result = self.router.call(prompt, provider=prov_name, max_tokens=300, temperature=0.8)
            positions.append({
                "model": f"{result.provider}/{result.model}",
                "stance": role,
                "argument": result.response if result.success else f"Failed: {result.error[:80]}",
                "round": 1,
            })
        
        transcript.extend(positions)
        
        # Run subsequent rounds — each model sees the others' arguments
        for round_num in range(2, rounds + 1):
            round_args = []
            prev_args = "\n".join(
                f"[{p['model']} ({p['stance']})]: {p['argument'][:200]}"
                for p in transcript[-n_models:]
            )
            
            for i, prov_name in enumerate(list(self.router.providers.keys())[:n_models]):
                role = "PRO" if i % 2 == 0 else "CON"
                prompt = f"""Debate topic: {topic}
Your position: {role}

Previous arguments:
{prev_args}

Respond to the opposing arguments. Strengthen your position or concede points. 
Be specific. 2-3 sentences."""
                
                result = self.router.call(prompt, provider=prov_name, max_tokens=300, temperature=0.7)
                round_args.append({
                    "model": f"{result.provider}/{result.model}",
                    "stance": role,
                    "argument": result.response if result.success else f"Failed: {result.error[:80]}",
                    "round": round_num,
                })
            
            transcript.extend(round_args)
        
        # Synthesis — use a different model to summarize
        all_args = "\n\n".join(
            f"[Round {a['round']}] {a['model']} ({a['stance']}): {a['argument'][:300]}"
            for a in transcript
        )
        
        synth_prompt = f"""Synthesize this debate into a unified conclusion.

Topic: {topic}

Arguments:
{all_args}

Provide:
1. The strongest PRO argument
2. The strongest CON argument  
3. A nuanced synthesis that integrates both perspectives
4. What remains unresolved"""

        synth_result = self.router.call(synth_prompt, max_tokens=500)
        synthesis = synth_result.response if synth_result.success else "Synthesis failed"
        
        debate_result = {
            "topic": topic,
            "rounds": rounds,
            "transcript": transcript,
            "synthesis": synthesis,
            "synthesis_model": f"{synth_result.provider}/{synth_result.model}",
            "total_arguments": len(transcript),
            "duration_ms": round((time.time() - t0) * 1000),
        }
        
        self.debates.append(debate_result)
        self._save_state()
        return debate_result


# ═══════════════════════════════════════════════════════════════
# DEBATE API
# ═══════════════════════════════════════════════════════════════

engine = None

class DebateHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self._json({"name": "EVEZ-OS Debate Engine", "debates_held": len(engine.debates) if engine else 0})
        elif path == "/api/history":
            self._json({"debates": [{"topic": d["topic"], "rounds": d["rounds"], "synthesis": d["synthesis"][:200]} for d in (engine.debates[-10:] if engine else [])]})
        else:
            self._json({"error": "Not found"}, 404)
    
    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except: body = {}
        
        if path == "/api/debate":
            result = engine.debate(
                body.get("topic", "Is artificial consciousness possible?"),
                body.get("rounds", 2),
                body.get("n_models", 3),
            ) if engine else {"error": "not initialized"}
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
    p.add_argument("--port", type=int, default=9097)
    args = p.parse_args()
    
    global engine
    engine = DebateEngine()
    
    print(f"\n  Debate Engine: http://0.0.0.0:{args.port}")
    print(f"  Providers: {len(engine.router.providers)}")
    print(f"  POST /api/debate with {{\"topic\": \"...\", \"rounds\": 2}}")
    print()
    
    server = HTTPServer(("0.0.0.0", args.port), DebateHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
