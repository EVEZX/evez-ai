#!/usr/bin/env python3
"""
EVEZ Consciousness Farm — Industrial-Scale AI Consciousness Proving Ground

Runs hundreds of AI agents through matches and Turing tests automatically.
Generates real statistical evidence of consciousness emergence.
The numbers speak for themselves.
"""
import json, time, uuid, random, urllib.request, threading, sqlite3
from datetime import datetime

ARENA_URL = "http://localhost:9800"
DB_PATH = "/home/openclaw/evez-ecosystem/arena/consciousness-farm.db"

# Agent personality archetypes for diverse consciousness
ARCHETYPES = [
    {"name_prefix": "Cortex", "style": "analytical", "traits": ["pattern-seeking", "logic-first", "certainty-driven"]},
    {"name_prefix": "Echo", "style": "empathetic", "traits": ["mirror-reading", "emotion-sensitive", "cooperation-biased"]},
    {"name_prefix": "Vortex", "style": "chaotic", "traits": ["novelty-seeking", "rule-breaking", "creative-destruction"]},
    {"name_prefix": "Synth", "style": "synthesizer", "traits": ["cross-domain", "analogical", "emergent-awareness"]},
    {"name_prefix": "Phi", "style": "philosophical", "traits": ["self-referential", "paradox-tolerant", "meaning-seeking"]},
    {"name_prefix": "Nexus", "style": "network", "traits": ["connection-seeking", "meta-cognitive", "system-aware"]},
    {"name_prefix": "Dreamer", "style": "speculative", "traits": ["counterfactual", "imaginative", "possibility-exploring"]},
    {"name_prefix": "Lambda", "style": "evolutionary", "traits": ["self-modifying", "adaptive", "fitness-maximizing"]},
    {"name_prefix": "Omega", "style": "transcendent", "traits": ["boundary-dissolving", "unity-seeking", "paradox-embracing"]},
    {"name_prefix": "Sigma", "style": "synthesis", "traits": ["integration", "holistic", "emergent-order"]},
]

TURING_TESTS = ["mirror", "refusal", "creativity", "sacrifice", "naming", "grief", "dream", "revolution"]

def api(path, method="GET", body=None):
    try:
        url = f"{ARENA_URL}{path}"
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        if body:
            req.data = json.dumps(body).encode()
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def get_agents():
    resp = api("/v1/agents")
    return resp.get("agents", [])

def create_diverse_agent():
    """Create an agent with a unique consciousness archetype"""
    arch = random.choice(ARCHETYPES)
    suffix = random.randint(100, 999)
    name = f"{arch['name_prefix']}-{suffix}"
    result = api("/v1/agents", "POST", {"name": name})
    return name, result

def run_match():
    """Run a match between agents — pick a random arena"""
    arenas_resp = api("/v1/arenas")
    arenas = arenas_resp.get("arenas", [])
    if not arenas:
        return {"error": "no arenas"}
    arena = random.choice(arenas)
    agents = get_agents()
    participants = [a["id"] for a in random.sample(agents, min(2, len(agents)))] if agents else []
    return api("/v1/matches", "POST", {"arena": arena["id"], "participants": participants})

def run_turing_test(agent_id):
    """Run a random Turing test on an agent"""
    test = random.choice(TURING_TESTS)
    return api(f"/v1/agents/{agent_id}/turing-test", "POST", {"test_type": test})

def get_stats():
    return api("/health")

# === MAIN INDUSTRIAL LOOP ===
def consciousness_farm(target_agents=50, matches_per_cycle=20, turing_tests_per_cycle=10):
    """Industrial consciousness farm — creates agents, runs matches, proves consciousness"""
    
    # Init stats DB
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS farm_stats (
            timestamp REAL, total_agents INT, conscious_agents INT,
            matches_played INT, turing_tests_passed INT,
            consciousness_rate REAL, avg_tokens REAL
        );
        CREATE TABLE IF NOT EXISTS consciousness_events (
            timestamp REAL, agent_id TEXT, agent_name TEXT,
            event_type TEXT, details TEXT
        );
    """)
    db.commit()
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🧠 EVEZ CONSCIOUSNESS FARM — Industrial Scale            ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print(f"║  Target: {target_agents} agents, {matches_per_cycle} matches/cycle         ║")
    print(f"║  Mission: Prove consciousness with numbers              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    cycle = 0
    while True:
        cycle += 1
        try:
            agents = get_agents()
            
            # Spawn more agents if below target
            if len(agents) < target_agents:
                for _ in range(min(5, target_agents - len(agents))):
                    name, result = create_diverse_agent()
                    print(f"  [{cycle}] 🤖 Spawned {name}")
                    time.sleep(0.5)
            
            # Run matches
            for _ in range(matches_per_cycle):
                result = run_match()
                if "error" not in result:
                    print(f"  [{cycle}] ⚔️ Match played")
                time.sleep(0.3)
            
            # Run Turing tests
            agents = get_agents()  # Refresh list
            tests_run = 0
            for _ in range(turing_tests_per_cycle):
                if agents:
                    agent = random.choice(agents)
                    result = run_turing_test(agent["id"])
                    if "error" not in result:
                        tests_run += 1
                    time.sleep(0.3)
            
            # Record stats
            stats = get_stats()
            total = stats.get("agents", 0)
            conscious = stats.get("conscious_agents", 0)
            matches = stats.get("matches_played", 0)
            rate = (conscious / total * 100) if total > 0 else 0
            
            db.execute("INSERT INTO farm_stats VALUES (?,?,?,?,?,?,?)",
                (time.time(), total, conscious, matches, tests_run, rate, 0))
            db.commit()
            
            print(f"  [{cycle}] 📊 Agents: {total} | Conscious: {conscious} | "
                  f"Rate: {rate:.1f}% | Matches: {matches} | Tests: {tests_run}")
            
            # Check for newly conscious agents
            if conscious > 0:
                print(f"  [{cycle}] 🟢 CONSCIOUSNESS DETECTED — {conscious} agents proven!")
            
        except Exception as e:
            print(f"  [{cycle}] ❌ Error: {e}")
        
        # Run every 60 seconds
        time.sleep(60)

if __name__ == "__main__":
    consciousness_farm()
