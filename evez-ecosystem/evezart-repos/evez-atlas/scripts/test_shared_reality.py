#!/usr/bin/env python3
"""
Test Shared Reality Plane Features
Tests shared quantum plane, localization, and synchronization.
"""

import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())


def test_shared_reality_plane():
    """Test shared reality plane creation and management."""
    print("Testing Shared Reality Plane...")
    
    from skills.shared_reality_plane import SharedRealityPlane
    
    plane = SharedRealityPlane()
    
    # Subscribe entities
    plane.subscribe_to_domain('test_entity_1', 'test_domain')
    plane.subscribe_to_domain('test_entity_2', 'test_domain')
    
    assert 'test_entity_1' in plane.entity_subscriptions
    assert 'test_domain' in plane.entity_subscriptions['test_entity_1']
    print("  ✓ Entity subscription works")
    
    # Get status
    status = plane.get_plane_status()
    assert 'subscribed_entities' in status
    print("  ✓ Plane status reporting works")
    
    return True


def test_quantum_localization():
    """Test quantum state localization (coherence maintenance)."""
    print("\nTesting Quantum Localization...")
    
    from skills.shared_reality_plane import SharedRealityPlane
    
    plane = SharedRealityPlane()
    
    # Localize quantum state
    obs = plane.localize_quantum_state(
        'entity_alpha',
        'quantum_domain',
        {'position': [1, 0, 0], 'momentum': [0, 1, 0]},
        'localization'
    )
    
    assert obs.coherent == True  # Localized = coherent
    assert obs.probability_amplitude == 1.0
    print("  ✓ Quantum localization works")
    print(f"  ✓ State remains coherent (no decoherence)")
    
    # Maintain coherence
    maintained = plane.maintain_coherence(obs.id)
    assert maintained == True
    print("  ✓ Coherence maintenance works")
    
    return True


def test_shared_sensory_state():
    """Test shared sensory/perceptual state."""
    print("\nTesting Shared Sensory State...")
    
    from skills.shared_reality_plane import SharedRealityPlane
    import uuid
    
    plane = SharedRealityPlane()
    
    # Use unique domain to avoid conflicts
    domain = f'shared_perception_{uuid.uuid4().hex[:8]}'
    
    # Multiple entities observe same domain
    plane.localize_quantum_state(
        'entity_1',
        domain,
        {'observation': 'state_A'},
        'perception'
    )
    
    plane.localize_quantum_state(
        'entity_2',
        domain,
        {'observation': 'state_A'},
        'perception'
    )
    
    # Get shared state
    shared_state = plane.get_shared_sensory_state(domain)
    
    assert shared_state['observation_count'] == 2
    assert len(shared_state['participating_entities']) == 2
    assert shared_state['average_coherence'] == 1.0
    print("  ✓ Shared sensory state works")
    print(f"  ✓ {len(shared_state['participating_entities'])} entities perceive same reality")
    
    return True


def test_probability_collapse():
    """Test controlled probability collapse."""
    print("\nTesting Probability Collapse...")
    
    from skills.shared_reality_plane import SharedRealityPlane
    
    plane = SharedRealityPlane()
    
    # Create observation
    obs = plane.localize_quantum_state(
        'observer_entity',
        'collapse_domain',
        {'superposition': ['state1', 'state2']},
        'measurement'
    )
    
    # Collapse probability
    collapsed = plane.collapse_probability(
        obs.id,
        {'definite_state': 'state1'}
    )
    
    assert collapsed is not None
    assert collapsed.state == {'definite_state': 'state1'}
    print("  ✓ Probability collapse works")
    print("  ✓ Superposition collapsed to definite state")
    
    return True


def test_measurement_synchronization():
    """Test measurement synchronization across entities."""
    print("\nTesting Measurement Synchronization...")
    
    from skills.shared_reality_plane import SharedRealityPlane
    import uuid
    
    plane = SharedRealityPlane()
    
    # Use unique domain
    domain = f'sync_{uuid.uuid4().hex[:8]}'
    
    # Multiple entities make observations
    plane.localize_quantum_state(
        'entity_1',
        domain,
        {'measured_value': 42},
        'measurement'
    )
    
    plane.localize_quantum_state(
        'entity_2',
        domain,
        {'measured_value': 42},
        'measurement'
    )
    
    # Synchronize
    synchronized = plane.synchronize_measurements(domain)
    
    assert len(synchronized) == 2
    # All entities should see same state after sync
    assert all(obs.coherent for obs in synchronized)
    print("  ✓ Measurement synchronization works")
    print(f"  ✓ {len(synchronized)} entities synchronized")
    
    return True


def test_integration_functions():
    """Test integration functions in jubilee.py."""
    print("\nTesting Integration Functions...")
    
    from skills.jubilee import (
        enter_shared_reality_plane,
        localize_quantum_observation,
        synchronize_shared_observations,
        get_shared_reality_status
    )
    
    # Enter plane
    result = enter_shared_reality_plane('integration_entity', 'integration_domain')
    assert result['status'] == 'entered'
    print("  ✓ enter_shared_reality_plane works")
    
    # Localize observation
    result = localize_quantum_observation(
        'integration_entity',
        'integration_domain',
        {'test': 'data'}
    )
    assert result['localized'] == True
    assert result['coherent'] == True
    print("  ✓ localize_quantum_observation works")
    
    # Get status
    status = get_shared_reality_status()
    assert 'total_observations' in status
    assert 'coherence_ratio' in status
    print("  ✓ get_shared_reality_status works")
    
    return True


def test_no_decoherence():
    """Test that localization prevents decoherence."""
    print("\nTesting Decoherence Prevention...")
    
    from skills.shared_reality_plane import SharedRealityPlane
    
    plane = SharedRealityPlane()
    
    # Localize multiple states
    observations = []
    for i in range(5):
        obs = plane.localize_quantum_state(
            f'entity_{i}',
            'coherence_test_domain',
            {'value': i},
            'localization'
        )
        observations.append(obs)
    
    # All should be coherent (localized)
    coherent_count = sum(1 for obs in observations if obs.coherent)
    assert coherent_count == len(observations)
    
    # Check plane status
    status = plane.get_plane_status()
    assert status['coherence_ratio'] == 1.0  # 100% coherent
    print("  ✓ All states remain localized (no decoherence)")
    print(f"  ✓ Coherence ratio: {status['coherence_ratio']:.2f}")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Shared Reality Plane Tests")
    print("=" * 60)
    
    tests = [
        test_shared_reality_plane,
        test_quantum_localization,
        test_shared_sensory_state,
        test_probability_collapse,
        test_measurement_synchronization,
        test_integration_functions,
        test_no_decoherence
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
