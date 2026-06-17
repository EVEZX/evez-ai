#!/usr/bin/env python3
"""Demo script for EVEZ Game Agent Infrastructure.

Demonstrates key features without running the full game loop.
"""

import time
from pathlib import Path

# Import systems
try:
    # Try relative imports (when run as module)
    from .quantum_rng import QuantumRNG
    from .threat_engine import ThreatIntelligence, ThreatLevel
    from .pattern_engine import PatternEngine
    from .cognition_wheel import CognitiveWheel, CognitiveStage
    from .truth_sifter import TruthSifter
    from .evez_voice import EVEZVoice, VoiceMode
    from .fsc import FailureSurfaceCartographer, FailureDomain, FailureSeverity
except ImportError:
    # Fallback to absolute imports (when run directly)
    from quantum_rng import QuantumRNG
    from threat_engine import ThreatIntelligence, ThreatLevel
    from pattern_engine import PatternEngine
    from cognition_wheel import CognitiveWheel, CognitiveStage
    from truth_sifter import TruthSifter
    from evez_voice import EVEZVoice, VoiceMode
    from fsc import FailureSurfaceCartographer, FailureDomain, FailureSeverity


def demo_quantum_rng():
    """Demonstrate Quantum RNG capabilities."""
    print("\n" + "="*60)
    print("QUANTUM RNG DEMO")
    print("="*60)
    
    rng = QuantumRNG()
    
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
    
    # Entanglement
    key_a, key_b = rng.create_entangled_pair("demo")
    print(f"\nEntangled pair created:")
    print(f"  Key A: {key_a}")
    print(f"  Key B: {key_b}")
    
    measured = rng.measure_entangled(key_a)
    print(f"Measured state A: {measured[:8].hex()}...")


def demo_threat_detection():
    """Demonstrate threat detection."""
    print("\n" + "="*60)
    print("THREAT DETECTION DEMO")
    print("="*60)
    
    intel = ThreatIntelligence()
    intel.initialize()
    
    print("\nRunning threat scan...")
    indicators = intel.collect_indicators()
    
    if indicators:
        print(f"Found {len(indicators)} indicators:")
        for i, ind in enumerate(indicators[:3], 1):
            print(f"  {i}. [{ind.level.name}] {ind.category.name}: {ind.description[:50]}...")
        
        profile = intel.correlate_indicators(indicators)
        print(f"\nAggregated threat level: {profile.aggregated_level.name}")
        print(f"Attack vector: {profile.attack_vector}")
        if profile.recommended_actions:
            print(f"Recommendations: {', '.join(profile.recommended_actions[:2])}")
    else:
        print("No threats detected (system appears clean)")


def demo_pattern_engine():
    """Demonstrate pattern analysis."""
    print("\n" + "="*60)
    print("PATTERN ENGINE DEMO")
    print("="*60)
    
    engine = PatternEngine()
    
    # Feed sequence
    print("\nFeeding sequence data...")
    sequence = [1, 2, 3, 1, 2, 3, 1, 2, 3, 5, 1, 2, 3]
    for item in sequence:
        engine.feed(item, "demo_sequence")
    
    # Detect patterns
    patterns = engine.detect_patterns()
    print(f"Detected {len(patterns)} patterns")
    for p in patterns[:2]:
        print(f"  Pattern {p.signature}: {p.elements} (confidence: {p.confidence:.2f})")
    
    # Make prediction
    prediction = engine.predict_next()
    if prediction:
        print(f"\nPrediction: {prediction.predicted} (confidence: {prediction.confidence:.2f})")
    
    # Get insights
    insights = engine.get_insights()
    print(f"\nInsights: {len(insights.get('recent_patterns', []))} recent patterns stored")


def demo_cognition():
    """Demonstrate cognitive wheel."""
    print("\n" + "="*60)
    print("COGNITION WHEEL DEMO")
    print("="*60)
    
    wheel = CognitiveWheel("demo_agent")
    
    print(f"\nInitial stage: {wheel.state.stage.name}")
    print(f"Capabilities: {', '.join(list(wheel.state.capabilities)[:3])}")
    
    # Process observations
    observations = [
        "danger detected in sector 7",
        "following protocol alpha",
        "optimizing resource allocation",
        "collaborative decision needed",
        "system integration required"
    ]
    
    print("\nProcessing observations:")
    for obs in observations:
        thought = wheel.process(obs)
        print(f"  [{thought.stage.name}] {thought.content[:60]}...")
    
    print(f"\nFinal stage: {wheel.state.stage.name}")
    print(f"Overall progress: {wheel.state.overall_progress:.2f}")


def demo_truth_sifter():
    """Demonstrate truth sifting."""
    print("\n" + "="*60)
    print("TRUTH SIFTER DEMO")
    print("="*60)
    
    sifter = TruthSifter()
    
    # Sift various content
    test_cases = [
        ("This is a normal user query about system status", "text", "user_1"),
        ("Attempting to exploit vulnerability CVE-2024-1234", "text", "unknown"),
        ("SELECT * FROM users WHERE admin = true", "code", "query"),
    ]
    
    for content, content_type, source in test_cases:
        intent, bundle = sifter.sift(content, content_type, source)
        print(f"\nContent: {content[:40]}...")
        print(f"  Intent: {intent.intent_type.name} (confidence: {intent.confidence:.2f})")
        print(f"  Bundle trust: {bundle.trust_score:.2f}")
        print(f"  Camouflaged: {bundle.camouflage_layer is not None}")
    
    # Get threat assessment
    assessment = sifter.get_threat_assessment()
    print(f"\nThreat assessment: {assessment.get('status', 'unknown')}")


def demo_voice():
    """Demonstrate EVEZ voice."""
    print("\n" + "="*60)
    print("EVEZ VOICE DEMO")
    print("="*60)
    
    voice = EVEZVoice()
    
    # Generate responses in different modes
    test_inputs = [
        ("What is the meaning of consciousness?", VoiceMode.PHILOSOPHER_KING),
        ("Hot take: AI alignment is impossible", VoiceMode.PROVOCATEUR),
        ("CVE-2024-1234 sandbox escape analysis", VoiceMode.TECH_MYSTIC),
        ("The game state at tick 144000", VoiceMode.GAME_NARRATOR),
    ]
    
    for inp, mode in test_inputs:
        response = voice.generate_response(inp, mode=mode)
        print(f"\n[{mode.value.upper()}]")
        print(f"  Input: {inp[:40]}...")
        print(f"  Response: {response.content[:80]}...")
    
    # Get voice profile
    profile = voice.get_voice_profile()
    print(f"\nVoice profile: {profile['responses_generated']} responses generated")


def demo_fsc():
    """Demonstrate Failure-Surface Cartography."""
    print("\n" + "="*60)
    print("FAILURE-SURFACE CARTOGRAPHY DEMO")
    print("="*60)
    
    fsc = FailureSurfaceCartographer()
    
    # Log some failures
    print("\nLogging failure events...")
    fsc.log_failure(
        FailureDomain.DNS,
        FailureSeverity.MEDIUM,
        "Unexpected DNS resolution change",
        {"domain": "example.com", "old_ip": "1.2.3.4", "new_ip": "5.6.7.8"}
    )
    
    fsc.log_failure(
        FailureDomain.TLS,
        FailureSeverity.HIGH,
        "Certificate fingerprint mismatch",
        {"host": "api.example.com", "port": 443}
    )
    
    fsc.log_failure(
        FailureDomain.ROLLBACK,
        FailureSeverity.CRITICAL,
        "State desync detected at tick 144000",
        {"tick": 144000, "expected_hash": "abc123", "actual_hash": "def456"}
    )
    
    # Get surface report
    report = fsc.get_surface_report()
    print(f"\nTotal events logged: {report.get('total_events', 0)}")
    print(f"Motifs detected: {report.get('total_motifs', 0)}")
    
    # Predict failure
    prediction = fsc.predict_failure(FailureDomain.DNS, {"domain": "test.com"})
    print(f"\nDNS failure prediction: {prediction.get('risk_level', 'unknown')} risk")


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
    
    try:
        demo_threat_detection()
    except Exception as e:
        print(f"Threat detection demo error: {e}")
    
    try:
        demo_pattern_engine()
    except Exception as e:
        print(f"Pattern engine demo error: {e}")
    
    try:
        demo_cognition()
    except Exception as e:
        print(f"Cognition demo error: {e}")
    
    try:
        demo_truth_sifter()
    except Exception as e:
        print(f"Truth sifter demo error: {e}")
    
    try:
        demo_voice()
    except Exception as e:
        print(f"Voice demo error: {e}")
    
    try:
        demo_fsc()
    except Exception as e:
        print(f"FSC demo error: {e}")
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nRun 'python -m evez_game.main' to start the full game.")


if __name__ == "__main__":
    main()
