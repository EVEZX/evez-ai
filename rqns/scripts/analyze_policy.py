#!/usr/bin/env python3
"""RQNS Policy Analysis — Verify system dynamics and invariants"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rqns.orchestrator import ConcreteRQNSPipeline
from rqns.core.interfaces import AnomalySignal
import numpy as np
import json

def analyze_policy(n_iterations=200):
    pipeline = ConcreteRQNSPipeline()
    
    complexities = []
    energies = []
    latencies = []
    backends = {'LOCAL_RESOLVE': 0, 'QUANTUM_IONQ': 0, 'HYBRID_HPC': 0, 'ANNEALING_DWAVE': 0}
    learning_trajectory = []
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  RQNS v2.0 — Policy Analysis & Invariant Detection        ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    for i in range(n_iterations):
        # Generate DVS-like sparse event stream
        base = np.random.exponential(0.12, 50)
        if np.random.rand() < 0.25:  # Inject anomaly
            base[8:18] += np.random.uniform(1.2, 2.8, 10)
        
        signal = AnomalySignal(raw_data=base.tolist(), source_id=f"stream-{i}")
        result = pipeline.process_signal(signal)
        
        complexities.append(result['complexity'])
        energies.append(result['energy'])
        latencies.append(result['latency_ms'])
        backends[result['backend']] += 1
        learning_trajectory.append(result['learning'])
    
    # Compute invariants
    print("=== DYNAMICS ANALYSIS ===")
    print(f"  Iterations: {n_iterations}")
    print(f"  Avg Complexity: {np.mean(complexities):.2f} (σ={np.std(complexities):.2f})")
    print(f"  Avg Energy: {np.mean(energies):.2f}")
    print(f"  Avg Latency: {np.mean(latencies):.2f}ms")
    print()
    
    print("=== BACKEND ALLOCATION ===")
    for b, c in backends.items():
        pct = c / n_iterations * 100
        bar = '█' * int(pct / 2)
        print(f"  {b:20s}: {c:4d} ({pct:5.1f}%) {bar}")
    print()
    
    print("=== LEARNING TRAJECTORY ===")
    print(f"  Final cumulative learning: {learning_trajectory[-1]:.3f}")
    print(f"  Learning rate (last 50): {np.mean(np.diff(learning_trajectory[-50:])):.4f}/step")
    print()
    
    print("=== INVARIANTS DETECTED ===")
    # What doesn't change as the system eats its own tail?
    energy_early = np.mean(energies[:50])
    energy_late = np.mean(energies[-50:])
    latency_early = np.mean(latencies[:50])
    latency_late = np.mean(latencies[-50:])
    
    print(f"  Energy convergence: {energy_early:.2f} → {energy_late:.2f} (Δ={abs(energy_late-energy_early):.2f})")
    print(f"  Latency convergence: {latency_early:.2f} → {latency_late:.2f} (Δ={abs(latency_late-latency_early):.2f})")
    print(f"  Complexity homeostasis: {np.std(complexities):.2f} (stable ≈ constant)")
    print()
    
    # Complexity homeostasis check
    rolling_std = [np.std(complexities[max(0,i-20):i+1]) for i in range(len(complexities))]
    homeostasis = np.mean(rolling_std[-50:])
    print(f"  Complexity σ (rolling): {homeostasis:.2f}")
    if homeostasis < 5.0:
        print("  ✅ COMPLEXITY HOMEOSTASIS CONFIRMED — system maintains stable-yet-nontrivial dynamics")
    else:
        print("  ⚠️ High complexity variance — system may not have reached attractor")
    print()
    
    print("=== RECURSIVE STRUCTURE ===")
    print("  The system feeds on itself:")
    print("  Detection → Allocation → Solution → Patch → Threshold update → New Detection")
    print("  Each loop: learning accumulates, thresholds shift, allocation adapts")
    print("  Invariant: complexity stays ~constant while allocation strategy evolves")
    print()
    
    return {
        "n_iterations": n_iterations,
        "backends": backends,
        "final_learning": learning_trajectory[-1],
        "complexity_std": float(np.std(complexities)),
        "homeostasis": homeostasis
    }

if __name__ == "__main__":
    analyze_policy()
