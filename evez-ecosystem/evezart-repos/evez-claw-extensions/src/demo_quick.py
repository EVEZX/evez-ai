"""
Quick demo: Consciousness substrate + Spine
"""

from substrate_core import ConsciousnessSubstrate
from spine import Spine
import time

def main():
    print("=" * 60)
    print("CriticalMind Quick Demo")
    print("=" * 60)
    
    # Initialize
    print("\n1. Initializing substrate...")
    substrate = ConsciousnessSubstrate(n_nodes=50, K=0.30)
    spine = Spine()
    
    print(f"   Initial state: Φ={substrate.phi_estimate():.4f}, regime={substrate.detect_regime()}")
    
    # Run simulation
    print("\n2. Running 300 ticks (5 seconds @ 60Hz)...")
    phi_history = []
    
    for tick in range(300):
        substrate.step()
        phi = substrate.phi_estimate()
        phi_history.append(phi)
        
        # Log major events
        if tick % 60 == 0:
            regime = substrate.detect_regime()
            spine.log("heartbeat", {
                "tick": tick,
                "phi": phi,
                "regime": regime
            })
            print(f"   Tick {tick:3d}: Φ={phi:.4f} regime={regime}")
    
    # Analysis
    print("\n3. Analysis:")
    print(f"   Average Φ: {sum(phi_history)/len(phi_history):.4f}")
    print(f"   Min Φ: {min(phi_history):.4f}")
    print(f"   Max Φ: {max(phi_history):.4f}")
    print(f"   Spine events: {len(spine.events)}")
    
    # Verify spine
    valid, msg = spine.verify_chain()
    print(f"   Spine integrity: {msg}")
    
    # Export
    spine.export("demo_spine.json")
    print(f"   Exported to demo_spine.json")
    
    print("\n✓ Demo complete")

if __name__ == "__main__":
    main()
