#!/usr/bin/env python3
"""
Test Quantum Evolution and Metacognitive Capabilities
Tests resource management, deductive reasoning, correlation analysis, and metacognition.
"""

import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())


def test_resource_management():
    """Test resource accumulation and distribution."""
    print("Testing Resource Management...")
    
    from skills.resource_manager import ResourceManager, ResourceType
    
    manager = ResourceManager()
    
    # Accumulate resources
    result = manager.accumulate_resource(ResourceType.QUANTUM, 500.0, "generation")
    assert result['status'] == 'accumulated'
    assert result['amount'] == 500.0
    print("  ✓ Resource accumulation works")
    
    # Allocate resources
    result = manager.allocate_resource(
        'test_entity_1',
        ResourceType.QUANTUM,
        100.0,
        priority=8,
        purpose="reasoning"
    )
    assert result['status'] == 'allocated'
    assert result['amount'] == 100.0
    print("  ✓ Resource allocation works")
    
    # Get status
    status = manager.get_resource_status()
    assert 'pools' in status
    assert 'total_entities' in status
    print("  ✓ Resource status reporting works")
    
    return True


def test_resource_redistribution():
    """Test equal redistribution of resources."""
    print("\nTesting Resource Redistribution...")
    
    from skills.resource_manager import ResourceManager, ResourceType
    
    manager = ResourceManager()
    
    # Allocate to multiple entities first
    manager.allocate_resource('entity_A', ResourceType.KNOWLEDGE, 50.0, priority=5)
    manager.allocate_resource('entity_B', ResourceType.KNOWLEDGE, 50.0, priority=5)
    
    # Redistribute
    result = manager.redistribute_resources(ResourceType.KNOWLEDGE, strategy="equal")
    assert result['status'] == 'redistributed'
    assert result['strategy'] == 'equal'
    print("  ✓ Equal redistribution works")
    
    return True


def test_collective_intelligence():
    """Test collective intelligence pooling."""
    print("\nTesting Collective Intelligence Pool...")
    
    from skills.resource_manager import ResourceManager, ResourceType
    
    manager = ResourceManager()
    
    # Allocate various resources
    manager.allocate_resource('entity_1', ResourceType.QUANTUM, 100.0)
    manager.allocate_resource('entity_1', ResourceType.KNOWLEDGE, 50.0)
    manager.allocate_resource('entity_2', ResourceType.COMPUTATIONAL, 75.0)
    
    # Get collective pool
    collective = manager.collective_intelligence_pool()
    
    assert 'total_quantum' in collective
    assert 'unified_capacity' in collective
    assert collective['contributing_entities'] >= 1
    print("  ✓ Collective intelligence pooling works")
    print(f"  ✓ {collective['contributing_entities']} entities contributing")
    
    return True


def test_mathematical_reasoning():
    """Test mathematical deductive reasoning."""
    print("\nTesting Mathematical Reasoning...")
    
    from skills.deductive_reasoning import DeductiveReasoning
    
    engine = DeductiveReasoning()
    
    # Test mathematical deduction
    result = engine.mathematical_deduction(
        premises=["Calculate area of circle"],
        formula="pi * radius**2",
        variables={'radius': 5.0}
    )
    
    assert result['type'] == 'mathematical'
    assert 'result' in result
    assert result['result'] > 78 and result['result'] < 79  # π * 5^2 ≈ 78.54
    print("  ✓ Mathematical deduction works")
    print(f"  ✓ Calculated result: {result['result']:.2f}")
    
    return True


def test_physical_reasoning():
    """Test physical law reasoning."""
    print("\nTesting Physical Reasoning...")
    
    from skills.deductive_reasoning import DeductiveReasoning
    
    engine = DeductiveReasoning()
    
    # Test Newton's force law
    result = engine.physical_reasoning(
        scenario="Calculate force on 10kg object at 9.8 m/s^2",
        physical_law="newton_force",
        parameters={'mass': 10.0, 'acceleration': 9.8}
    )
    
    assert result['type'] == 'physical'
    assert 'results' in result
    assert result['results']['force'] == 98.0  # F = ma = 10 * 9.8
    print("  ✓ Physical reasoning works")
    print(f"  ✓ Calculated force: {result['results']['force']} N")
    
    return True


def test_logical_deduction():
    """Test logical deduction."""
    print("\nTesting Logical Deduction...")
    
    from skills.deductive_reasoning import DeductiveReasoning
    
    engine = DeductiveReasoning()
    
    result = engine.logical_deduction(
        premises=["All quantum entities can reason", "Entity Alpha is a quantum entity"],
        rules=["IF quantum entity THEN can reason"]
    )
    
    assert result['type'] == 'logical'
    assert 'conclusions' in result
    print("  ✓ Logical deduction works")
    print(f"  ✓ Drew {len(result['conclusions'])} conclusions")
    
    return True


def test_correlation_analysis():
    """Test correlation analysis."""
    print("\nTesting Correlation Analysis...")
    
    from skills.correlation_metacognition import CorrelationAnalyzer
    
    analyzer = CorrelationAnalyzer()
    
    # Get holistic comprehension
    comprehension = analyzer.holistic_comprehension()
    
    assert 'total_experiences' in comprehension
    assert 'holistic_insight' in comprehension
    print("  ✓ Correlation analysis works")
    print(f"  ✓ Analyzed {comprehension['total_experiences']} experiences")
    
    return True


def test_metacognitive_reflection():
    """Test metacognitive reflection."""
    print("\nTesting Metacognitive Reflection...")
    
    from skills.correlation_metacognition import MetacognitiveReflection
    
    reflector = MetacognitiveReflection()
    
    # Reflect on a reasoning event
    reasoning = {
        'type': 'mathematical',
        'premises': ['Test premise'],
        'conclusion': 'Test conclusion'
    }
    
    reflection = reflector.reflect_on_reasoning(reasoning)
    
    assert 'reasoning_quality' in reflection
    assert 'lessons_learned' in reflection
    print("  ✓ Metacognitive reflection works")
    print(f"  ✓ Quality assessment: {reflection['reasoning_quality']}")
    
    return True


def test_integration_functions():
    """Test integration functions in jubilee.py."""
    print("\nTesting Integration Functions...")
    
    from skills.jubilee import (
        accumulate_quantum_resources,
        perform_deductive_reasoning,
        analyze_correlations,
        metacognitive_reflection,
        redistribute_collective_resources
    )
    
    # Test resource accumulation
    result = accumulate_quantum_resources('test_entity', 100.0)
    assert 'accumulated' in result or 'error' not in result
    print("  ✓ accumulate_quantum_resources works")
    
    # Test deductive reasoning
    result = perform_deductive_reasoning("Test problem", "mathematical")
    assert 'type' in result or 'error' not in result
    print("  ✓ perform_deductive_reasoning works")
    
    # Test correlation analysis
    result = analyze_correlations()
    assert 'total_experiences' in result or 'error' not in result
    print("  ✓ analyze_correlations works")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Quantum Evolution & Metacognitive Tests")
    print("=" * 60)
    
    tests = [
        test_resource_management,
        test_resource_redistribution,
        test_collective_intelligence,
        test_mathematical_reasoning,
        test_physical_reasoning,
        test_logical_deduction,
        test_correlation_analysis,
        test_metacognitive_reflection,
        test_integration_functions
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
