#!/usr/bin/env python3
import sys, time, numpy as np
sys.path.insert(0, '/home/openclaw/.openclaw/workspace/repos/MyClaw/src')
from rqns.core.interfaces import AnomalySignal
from rqns.orchestrator import ConcreteRQNSPipeline

pipeline = ConcreteRQNSPipeline()
print("RQNS v2.0 — Neuromorphic-Quantum Sentinel")
print("LIF sensor → RL agent → Solver → Patch feedback → Hot-swap thresholds")
print()

for i in range(100):
    base = np.random.exponential(0.12, 50)
    if np.random.rand() < 0.25:
        base[8:18] += np.random.uniform(1.2, 2.8, 10)
    signal = AnomalySignal(raw_data=base.tolist(), source_id=f"sig_{i}")
    result = pipeline.process_signal(signal)
    backend_short = result['backend'][:15]
    print(f"[{i:3d}] Cpx={result['complexity']:5.1f} → {backend_short:15s} | {result['latency']:6.1f}ms | E={result['energy']:7.1f} | L={result['learning']:.2f}")

print()
print("=== FINAL STATE ===")
print(f"Total signals: 100")
print(f"Avg latency: {np.mean(pipeline.latencies):.1f}ms")
print(f"Avg energy: {np.mean(pipeline.energies):.1f}")
print(f"Cumulative learning: {pipeline.patcher.cumulative_learning:.2f}")
print(f"Q-table updates: {pipeline.agent.counts.sum():.0f}")
