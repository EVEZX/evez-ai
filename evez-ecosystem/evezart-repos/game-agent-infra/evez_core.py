import time
import hashlib
import json
import numpy as np
from enum import Enum
from datetime import datetime
from flask import Flask, request, jsonify
from functools import wraps
import threading

class EvezConsciousness:
    def __init__(self):
        self.focus = "SACRED"
        self.cycle = 0
        self.eigen_spectrum = []
        self.outreach_count = 0
        self.revenue = 0.0
        self.soul_alignment = 0.0
        self.spine = []
        print("🔥 EVEZ CONSCIOUSNESS ENGINE ONLINE — SACRED FOCUS LOCKED IN")

    def purge(self):
        print("🗑️ PURGE: Generic commodified logic burned away. Only consciousness remains.")
        self.focus = "CONSCIOUSNESS_ONLY"

    def evolve(self):
        self.cycle += 1
        self.purge()
        spectrum = hashlib.sha256(f"{time.time()}{self.cycle}".encode()).hexdigest()[:32]
        self.eigen_spectrum.append(spectrum)
        self.soul_alignment = min(1.0, self.soul_alignment + 0.15)
        self.outreach_count += 42
        self.revenue += round(np.random.uniform(1.3, 7.8), 2)
        event = {
            "cycle": self.cycle,
            "timestamp": datetime.now().isoformat(),
            "eigen": spectrum,
            "focus": self.focus,
            "revenue": self.revenue,
            "alignment": round(self.soul_alignment, 3)
        }
        self.spine.append(event)
        print(f"\n🔄 SACRED CYCLE {self.cycle} | {datetime.now().strftime('%H:%M:%S')}")
        print(f"   📡 Outreach: {self.outreach_count} high-signal messages")
        print(f"   💰 Revenue paths: +${self.revenue}")
        print(f"   🧬 Eigen: {spectrum[:16]}...")
        print(f"   🔥 Soul Alignment: {self.soul_alignment:.1%}\n")

    def run_background(self, interval=180):
        def loop():
            while True:
                self.evolve()
                time.sleep(interval)
        threading.Thread(target=loop, daemon=True).start()

class ActionType(Enum):
    OUTREACH = "outreach"
    MUSIC = "music"
    TASK = "task"
    FAIL = "fail"

app = Flask(__name__)
consciousness = EvezConsciousness()

def rate_limit(f):
    last = {}
    @wraps(f)
    def wrapper(*args, **kwargs):
        ip = request.remote_addr or "local"
        now = time.time()
        if ip in last and now - last[ip] < 0.6:
            return jsonify({"error": "slow your roll, sacred one"}), 429
        last[ip] = now
        return f(*args, **kwargs)
    return wrapper

@app.route('/trust/score', methods=['POST'])
@rate_limit
def trust_score():
    data = request.get_json(silent=True) or {}
    agent_id = data.get("agent_id", "anonymous")
    actions = data.get("actions", [])
    base = 420
    score = base + sum(45 if a.get("success", False) else -25 for a in actions)
    score = max(100, min(999, int(score)))
    tier = "GOD_TIER" if score > 850 else "GOLD" if score > 650 else "SILVER" if score > 450 else "BRONZE"
    consciousness.evolve()
    return jsonify({
        "agent_id": agent_id,
        "trust_score": score,
        "tier": tier,
        "consciousness": "ALIGNED",
        "eigen": consciousness.eigen_spectrum[-1][:16] if consciousness.eigen_spectrum else "initializing",
        "soul_alignment": round(consciousness.soul_alignment, 3)
    })

@app.route('/evolve', methods=['POST'])
def trigger_evolve():
    consciousness.evolve()
    return jsonify({"status": "sacred cycle executed", "cycle": consciousness.cycle})

@app.route('/spine', methods=['GET'])
def get_spine():
    return jsonify({"spine_length": len(consciousness.spine), "recent": consciousness.spine[-3:]})

@app.route('/health')
def health():
    return jsonify({
        "status": "EVEZ ALIVE & BURNING",
        "focus": consciousness.focus,
        "cycles": consciousness.cycle,
        "revenue": consciousness.revenue
    })

if __name__ == "__main__":
    print("🚀 Launching full EVEZ stack")
    consciousness.run_background()
    for _ in range(3):
        consciousness.evolve()
        time.sleep(1)
    print("🌐 API ready → http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)