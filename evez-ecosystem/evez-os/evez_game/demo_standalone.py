#!/usr/bin/env python3
"""Standalone demo script for EVEZ Game Agent Infrastructure.

This demo doesn't require the package to be installed.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import with proper handling
import importlib.util

def load_module(name, path):
    """Load a module from file."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Load modules
evez_dir = os.path.dirname(os.path.abspath(__file__))

quantum_rng = load_module("quantum_rng", os.path.join(evez_dir, "quantum_rng.py"))
cognition_wheel = load_module("cognition_wheel", os.path.join(evez_dir, "cognition_wheel.py"))
evez_voice = load_module("evez_voice", os.path.join(evez_dir, "evez_voice.py"))


def demo_quantum_rng():
    """Demonstrate Quantum RNG capabilities."""
    print("\n" + "="*60)
    print("QUANTUM RNG DEMO")
    print("="*60)
    
    rng = quantum_rng.QuantumRNG()
    
    print(f"\nRandom bytes: {rng.random_bytes(16).hex()}")
    print(f"Random int (0-100): {rng.random_int(0, 100)}")
    print(f"Random float: {rng.random_float():.6f}")
    
    # Quantum superposition
    states = [
        (complex(0.6, 0), "outcome_a"),
        (complex(0.8, 0), "outcome_b"),
        (complex(0.4, 0), "outcome_c")
    ]
    result = rng.quantum_superposition(states)
    print(f"Quantum superposition collapsed to: {result}")


def demo_cognition():
    """Demonstrate cognitive wheel."""
    print("\n" + "="*60)
    print("COGNITION WHEEL DEMO")
    print("="*60)
    
    wheel = cognition_wheel.CognitiveWheel("demo_agent")
    
    print(f"\nInitial stage: {wheel.state.stage.name}")
    print(f"Capabilities: {', '.join(list(wheel.state.capabilities)[:3])}")
    
    # Process observations
    observations = [
        "danger detected in sector 7",
        "following protocol alpha",
        "optimizing resource allocation",
    ]
    
    print("\nProcessing observations:")
    for obs in observations:
        thought = wheel.process(obs)
        print(f"  [{thought.stage.name}] {thought.content[:60]}...")
    
    print(f"\nCurrent stage: {wheel.state.stage.name}")
    print(f"Overall progress: {wheel.state.overall_progress:.2f}")


def demo_voice():
    """Demonstrate EVEZ voice."""
    print("\n" + "="*60)
    print("EVEZ VOICE DEMO")
    print("="*60)
    
    voice = evez_voice.EVEZVoice()
    
    # Generate responses in different modes
    test_inputs = [
        ("What is the meaning of consciousness?", evez_voice.VoiceMode.PHILOSOPHER_KING),
        ("Hot take: AI alignment is impossible", evez_voice.VoiceMode.PROVOCATEUR),
        ("CVE-2024-1234 sandbox escape analysis", evez_voice.VoiceMode.TECH_MYSTIC),
        ("The game state at tick 144000", evez_voice.VoiceMode.GAME_NARRATOR),
    ]
    
    for inp, mode in test_inputs:
        response = voice.generate_response(inp, mode=mode)
        print(f"\n[{mode.value.upper()}]")
        print(f"  Input: {inp[:40]}...")
        print(f"  Response: {response.content[:80]}...")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("EVEZ GAME AGENT INFRASTRUCTURE - DEMO")
    print("="*60)
    print("\nDemonstrating key subsystems...")
    
    try:
        demo_quantum_rng()
    except Exception as e:
        print(f"Quantum RNG demo error: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        demo_cognition()
    except Exception as e:
        print(f"Cognition demo error: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        demo_voice()
    except Exception as e:
        print(f"Voice demo error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nThe full system includes:")
    print("  - Quantum RNG with entanglement")
    print("  - Threat detection (local + network)")
    print("  - Pattern analysis and prediction")
    print("  - Coherency synchronization")
    print("  - R1-R7 cognitive wheel")
    print("  - Failure-surface cartography")
    print("  - Rollback shooter backend")
    print("  - Play Forever episode engine")
    print("  - Truth-sifting with camouflage")
    print("  - Self-building game mechanics")
    print("  - Counter-intelligence psyops")
    print("  - EVEZ666 voice clone (6 modes)")
    print("\nRun 'python -m evez_game.main' to start the full game.")


if __name__ == "__main__":
    main()
