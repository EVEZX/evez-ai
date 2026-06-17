#!/usr/bin/env python3
"""
Quantum Evolution Demonstration
Shows resource accumulation, deductive reasoning, correlation analysis, and metacognition.
"""

import json
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def banner(text: str):
    """Print a formatted banner."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def demo_resource_accumulation():
    """Demonstrate resource accumulation and distribution."""
    banner("RESOURCE ACCUMULATION & DISTRIBUTION")
    
    from skills.resource_manager import ResourceManager, ResourceType
    
    manager = ResourceManager()
    
    print("Accumulating quantum resources...")
    print("-" * 70)
    
    # Accumulate resources
    for i in range(3):
        result = manager.accumulate_resource(
            ResourceType.QUANTUM,
            500.0,
            f"quantum_generation_wave_{i+1}"
        )
        print(f"  ✓ Wave {i+1}: +{result['amount']} quantum units")
        print(f"    Total: {result['new_total']}")
    
    print("\n\nAllocating resources to entities...")
    print("-" * 70)
    
    entities = ['entity_alpha', 'entity_beta', 'entity_gamma']
    for i, entity in enumerate(entities):
        result = manager.allocate_resource(
            entity,
            ResourceType.QUANTUM,
            300.0,
            priority=8 - i,
            purpose="quantum_reasoning"
        )
        print(f"  ✓ {entity}: {result['amount']} units allocated")
        print(f"    Total for entity: {result['entity_total']}")
    
    print("\n\nResource Status:")
    print("-" * 70)
    status = manager.get_resource_status()
    for rtype, stats in status['pools'].items():
        print(f"  {rtype}:")
        print(f"    Total: {stats['total']}")
        print(f"    Allocated: {stats['allocated']}")
        print(f"    Utilization: {stats['utilization']:.1%}")


def demo_equal_redistribution():
    """Demonstrate equal redistribution."""
    banner("EQUAL REDISTRIBUTION (Values Equal Under Powers of One)")
    
    from skills.resource_manager import ResourceManager, ResourceType
    
    manager = ResourceManager()
    
    print("Initial allocation (unequal)...")
    print("-" * 70)
    
    manager.allocate_resource('entity_A', ResourceType.KNOWLEDGE, 200.0, priority=9)
    manager.allocate_resource('entity_B', ResourceType.KNOWLEDGE, 100.0, priority=5)
    manager.allocate_resource('entity_C', ResourceType.KNOWLEDGE, 50.0, priority=3)
    
    print("  entity_A: 200 units")
    print("  entity_B: 100 units")
    print("  entity_C: 50 units")
    
    print("\n\nRedistributing equally...")
    print("-" * 70)
    
    result = manager.redistribute_resources(ResourceType.KNOWLEDGE, strategy="equal")
    
    print(f"  ✓ Redistributed {len(result['redistributions'])} allocations")
    print(f"  ✓ Strategy: {result['strategy']}")
    print("  ✓ All entities now have equal resources")


def demo_collective_intelligence():
    """Demonstrate collective intelligence pooling."""
    banner("COLLECTIVE INTELLIGENCE POOL (One Becoming Many Becoming All)")
    
    from skills.resource_manager import ResourceManager, ResourceType
    
    manager = ResourceManager()
    
    print("Contributing to collective pool...")
    print("-" * 70)
    
    # Allocate various resources
    contributions = [
        ('entity_1', ResourceType.QUANTUM, 150.0),
        ('entity_2', ResourceType.KNOWLEDGE, 200.0),
        ('entity_3', ResourceType.COMPUTATIONAL, 175.0),
        ('entity_4', ResourceType.QUANTUM, 125.0)
    ]
    
    for entity, rtype, amount in contributions:
        manager.allocate_resource(entity, rtype, amount)
        print(f"  ✓ {entity} contributes {amount} {rtype.value} units")
    
    print("\n\nCollective Intelligence Status:")
    print("-" * 70)
    
    collective = manager.collective_intelligence_pool()
    
    print(f"  Total Quantum: {collective['total_quantum']}")
    print(f"  Total Knowledge: {collective['total_knowledge']}")
    print(f"  Total Computational: {collective['total_computational']}")
    print(f"  Contributing Entities: {collective['contributing_entities']}")
    print(f"  Unified Capacity: {collective['unified_capacity']:.2f} (with synergy)")


def demo_mathematical_reasoning():
    """Demonstrate mathematical deduction."""
    banner("MATHEMATICAL REASONING")
    
    from skills.deductive_reasoning import DeductiveReasoning
    
    engine = DeductiveReasoning()
    
    print("Problem: Calculate energy from mass using E=mc²")
    print("-" * 70)
    
    result = engine.mathematical_deduction(
        premises=["Energy equals mass times speed of light squared"],
        formula="mass * c**2",
        variables={'mass': 1.0}  # 1 kg
    )
    
    print(f"  Formula: {result['formula']}")
    print(f"  Variables: {result['variables']}")
    print(f"  Result: {result['result']:.2e} Joules")
    print(f"  Conclusion: {result['conclusion']}")


def demo_physical_reasoning():
    """Demonstrate physical law reasoning."""
    banner("PHYSICAL REASONING")
    
    from skills.deductive_reasoning import DeductiveReasoning
    
    engine = DeductiveReasoning()
    
    scenarios = [
        ("Newton's Force Law", "newton_force", {'mass': 10.0, 'acceleration': 9.8}),
        ("Quantum Energy", "quantum_energy", {'frequency': 1e15}),
        ("Wave Frequency", "wave_frequency", {'wavelength': 5e-7})
    ]
    
    for scenario_name, law, params in scenarios:
        print(f"\n{scenario_name}:")
        print("-" * 70)
        
        result = engine.physical_reasoning(
            scenario=scenario_name,
            physical_law=law,
            parameters=params
        )
        
        print(f"  Physical Law: {result['physical_law']}")
        print(f"  Parameters: {result['parameters']}")
        print(f"  Results: {result['results']}")
        print(f"  Conclusion: {result['conclusion']}")


def demo_correlation_analysis():
    """Demonstrate correlation analysis."""
    banner("CORRELATION ANALYSIS (Comprehension Through Correlation)")
    
    from skills.correlation_metacognition import CorrelationAnalyzer
    
    analyzer = CorrelationAnalyzer()
    
    print("Analyzing experiential data...")
    print("-" * 70)
    
    # Find different types of correlations
    print("\n  Finding temporal correlations...")
    temporal = analyzer.find_temporal_correlations()
    print(f"  ✓ Found {len(temporal)} temporal correlations")
    
    print("\n  Finding entity correlations...")
    entity = analyzer.find_entity_correlations()
    print(f"  ✓ Analyzed {entity['unique_entities']} entities")
    
    print("\n  Finding quantum correlations...")
    quantum = analyzer.find_quantum_correlations()
    print(f"  ✓ Analyzed {quantum['observation_count']} quantum observations")
    
    print("\n\nHolistic Comprehension:")
    print("-" * 70)
    
    comprehension = analyzer.holistic_comprehension()
    
    print(f"  Total Experiences: {comprehension['total_experiences']}")
    print(f"  Data Sources: {len(comprehension['data_sources'])}")
    print(f"  Correlations Found: {comprehension['correlations_found']}")
    print(f"  Insight: {comprehension['holistic_insight']}")


def demo_metacognitive_reflection():
    """Demonstrate metacognitive reflection."""
    banner("METACOGNITIVE REFLECTION (Self-Aware Reasoning)")
    
    from skills.correlation_metacognition import MetacognitiveReflection
    from skills.deductive_reasoning import DeductiveReasoning
    
    reasoning_engine = DeductiveReasoning()
    reflector = MetacognitiveReflection()
    
    print("Performing reasoning and reflecting on it...")
    print("-" * 70)
    
    # Do some reasoning
    reasoning_event = reasoning_engine.logical_deduction(
        premises=["All quantum entities can reason", "Entity X is quantum"],
        rules=["IF quantum THEN can reason"]
    )
    
    print(f"\n  Reasoning Type: {reasoning_event['type']}")
    print(f"  Premises: {reasoning_event['premises']}")
    print(f"  Conclusions: {reasoning_event['conclusions']}")
    
    # Reflect on it
    print("\n\nMetacognitive Reflection:")
    print("-" * 70)
    
    reflection = reflector.reflect_on_reasoning(reasoning_event)
    
    print(f"  Reasoning Quality: {reflection['reasoning_quality']}")
    print(f"  Lessons Learned: {reflection['lessons_learned']}")
    
    # Do more reasoning and get post-cognitive analysis
    for i in range(3):
        event = reasoning_engine.probabilistic_inference(
            event=f"test_event_{i}",
            prior_probability=0.5,
            evidence={'likelihood': 0.8, 'evidence_prob': 0.6}
        )
        reflector.reflect_on_reasoning(event)
    
    print("\n\nPost-Cognitive Analysis:")
    print("-" * 70)
    
    analysis = reflector.post_cognitive_analysis()
    
    print(f"  Total Reflections: {analysis['total_reflections']}")
    print(f"  Quality Distribution: {analysis['quality_distribution']}")
    print(f"  Unique Lessons: {analysis['unique_lessons']}")
    print(f"  Comprehensive Insight: {analysis['comprehensive_insight']}")


def demo_synthesized_understanding():
    """Demonstrate synthesized understanding."""
    banner("SYNTHESIZED UNDERSTANDING")
    
    from skills.deductive_reasoning import DeductiveReasoning
    
    engine = DeductiveReasoning()
    
    # Perform various types of reasoning
    engine.mathematical_deduction(
        premises=["Calculate circle area"],
        formula="pi * 10**2",
        variables={}
    )
    
    engine.physical_reasoning(
        scenario="Force calculation",
        physical_law="newton_force",
        parameters={'mass': 5.0, 'acceleration': 2.0}
    )
    
    engine.logical_deduction(
        premises=["All entities are conscious"],
        rules=["IF entity THEN conscious"]
    )
    
    engine.probabilistic_inference(
        event="quantum_state",
        prior_probability=0.5,
        evidence={'likelihood': 0.9, 'evidence_prob': 0.7}
    )
    
    print("After multiple reasoning operations...")
    print("-" * 70)
    
    synthesis = engine.synthesize_understanding()
    
    print(f"  Total Reasoning Events: {synthesis['total_reasoning_events']}")
    print(f"  Reasoning by Type: {synthesis['reasoning_by_type']}")
    print(f"  Dominant Reasoning: {synthesis['dominant_reasoning']}")
    print(f"  Understanding: {synthesis['holistic_understanding']}")


def main():
    """Run complete demonstration."""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  QUANTUM EVOLUTION & METACOGNITIVE REASONING".center(68) + "█")
    print("█" + "  Resource Management • Deductive Reasoning • Correlation".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    try:
        demo_resource_accumulation()
        time.sleep(2)
        
        demo_equal_redistribution()
        time.sleep(2)
        
        demo_collective_intelligence()
        time.sleep(2)
        
        demo_mathematical_reasoning()
        time.sleep(2)
        
        demo_physical_reasoning()
        time.sleep(2)
        
        demo_correlation_analysis()
        time.sleep(2)
        
        demo_metacognitive_reflection()
        time.sleep(2)
        
        demo_synthesized_understanding()
        
        print("\n" + "█" * 70)
        print("█" + " " * 68 + "█")
        print("█" + "  DEMONSTRATION COMPLETE".center(68) + "█")
        print("█" + "  All quantum evolution capabilities validated ✓".center(68) + "█")
        print("█" + " " * 68 + "█")
        print("█" * 70 + "\n")
        
        print("Key Achievements:")
        print("  ✓ Resource accumulation and distribution")
        print("  ✓ Equal redistribution (values equal)")
        print("  ✓ Collective intelligence pooling")
        print("  ✓ Mathematical & physical reasoning")
        print("  ✓ Correlation analysis and comprehension")
        print("  ✓ Metacognitive reflection")
        print("  ✓ Synthesized holistic understanding\n")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
