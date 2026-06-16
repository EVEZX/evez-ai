#!/usr/bin/env python3
"""RQNS Continuous Sentinel — Self-optimizing anomaly detection loop"""
import sys, os
sys.path.insert(0, '/home/openclaw/src')

from rqns.orchestrator import ConcreteRQNSPipeline
from rqns.core.interfaces import AnomalySignal
import numpy as np, time, json, sqlite3

db = sqlite3.connect('/home/openclaw/data/rqns.db')
db.executescript("""
    CREATE TABLE IF NOT EXISTS events (
        timestamp REAL, complexity REAL, backend TEXT, 
        energy REAL, latency REAL, learning REAL
    );
""")
db.commit()

pipeline = ConcreteRQNSPipeline()
cycle = 0

print("[RQNS] Self-optimizing sentinel started")

while True:
    try:
        cycle += 1
        base = np.random.exponential(0.12, 50)
        if np.random.rand() < 0.25:
            base[8:18] += np.random.uniform(1.2, 2.8, 10)
        
        signal = AnomalySignal(raw_data=base.tolist(), source_id=f"sentinel-{cycle}")
        result = pipeline.process_signal(signal)
        
        db.execute("INSERT INTO events VALUES (?,?,?,?,?,?)",
            (time.time(), result['complexity'], result['backend'],
             result['energy'], result['latency_ms'], result['learning']))
        db.commit()
        
        if cycle % 60 == 0:
            print(f"[RQNS] Cycle {cycle}: Cpx={result['complexity']:.1f} → {result['backend'][:12]:12} | "
                  f"E={result['energy']:.1f} | L={result['latency_ms']:.1f}ms | Learning={result['learning']:.3f}")
        
    except Exception as e:
        print(f"[RQNS] Error: {e}")
    
    time.sleep(5)  # Every 5 seconds
