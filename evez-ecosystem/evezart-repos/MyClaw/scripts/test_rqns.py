#!/usr/bin/env python3
"""Test the full RQNS v2 pipeline."""
import sys
sys.path.insert(0, 'src')
from rqns.orchestrator import ConcreteRQNSPipeline
from rqns.core.interfaces import AnomalySignal
import numpy as np
import time

pipeline = ConcreteRQNSPipeline()

print("RQNS v2.0 — Self-Optimizing Neuromorphic-Quantum Sentinel")
print("=" * 60)

for i in range(20):
    # Simulate DVS-like sparse events with occasional anomalies
    raw = np.random.exponential(0.12, 50).tolist()
    if np.random.rand() < 0.25:
        raw[8:18] = [x + np.random.uniform(1.2, 2.8) for x in raw[8:18]]
    
    signal = AnomalySignal(source_id=f"test_{i}", raw_data=raw)
    result = pipeline.process_signal(signal)
    
    anomaly_marker = "⚡" if result["is_anomaly"] else " "
    print(f"  {anomaly_marker} Cpx={result['complexity']:.1f} → "
          f"{result['backend']:16} | {result['latency']:6.1f}ms | "
          f"E={result['energy']:6.1f} | L={result['learning']:.2f} | "
          f"spikes={result['total_spikes']}")
    time.sleep(0.1)

print(f"\nSpine events: {len(pipeline.spine.events)}")
print(f"Steering: {pipeline.steering.state()}")
print("Done.")
