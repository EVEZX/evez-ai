#!/usr/bin/env python3
"""
Test Enhanced Swarm Autonomy Features
Tests entity lifecycle, task queue, and quantum domain signaling.
"""

import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())


def test_entity_lifecycle():
    """Test entity lifecycle management."""
    print("Testing Entity Lifecycle Management...")
    
    from skills.entity_lifecycle import EntityLifecycleManager, EntityState
    
    manager = EntityLifecycleManager()
    
    # Create test entity
    entity = manager.create_entity('test_entity_1', 'test_role', 'test_domain')
    assert entity.state == EntityState.HIBERNATING
    print("  ✓ Entity creation works")
    
    # Awaken entity
    awakened = manager.awaken_entity('test_entity_1')
    assert awakened.state == EntityState.ACTIVE
    print("  ✓ Entity awakening works")
    
    # Hibernate entity
    hibernated = manager.hibernate_entity('test_entity_1', depth=2)
    assert hibernated.state == EntityState.HIBERNATING
    assert hibernated.hibernation_depth == 2
    print("  ✓ Entity hibernation works")
    
    # Quantum entanglement
    entangled = manager.quantum_entangle('test_entity_1', 'quantum_test_domain')
    assert entangled.quantum_entangled == True
    assert entangled.domain == 'quantum_test_domain'
    print("  ✓ Quantum entanglement works")
    
    # Get status
    status = manager.get_swarm_status()
    assert 'total_entities' in status
    assert 'quantum_entangled' in status
    print("  ✓ Swarm status reporting works")
    
    return True


def test_task_queue():
    """Test task queue with error correction."""
    print("\nTesting Task Queue with Error Correction...")
    
    from skills.task_queue import TaskQueue, TaskStatus
    
    queue = TaskQueue()
    
    # Register test handler
    def test_handler(data):
        if data.get('should_fail'):
            raise Exception("Intentional test failure")
        return {'result': 'success', 'data': data}
    
    queue.register_handler('test_task', test_handler)
    
    # Enqueue successful task
    task1 = queue.enqueue('test_task', {'value': 123})
    assert task1.status == TaskStatus.PENDING
    print("  ✓ Task enqueueing works")
    
    # Execute successful task
    result1 = queue.execute_task(task1.id)
    assert result1['status'] == 'success'
    print("  ✓ Task execution works")
    
    # Enqueue failing task
    task2 = queue.enqueue('test_task', {'should_fail': True}, max_attempts=2)
    result2 = queue.execute_task(task2.id)
    assert result2['status'] == 'failed'
    print("  ✓ Error correction and retry logic works")
    
    # Get queue status
    status = queue.get_queue_status()
    assert 'total_tasks' in status
    assert 'by_status' in status
    print("  ✓ Queue status reporting works")
    
    return True


def test_quantum_domain_signaling():
    """Test quantum domain signaling."""
    print("\nTesting Quantum Domain Signaling...")
    
    from skills.jubilee import quantum_sim
    
    result = quantum_sim({
        'circuit': 'test_circuit',
        'domain': 'retrocausal_test_domain',
        'qubits': 3
    })
    
    assert 'domain' in result
    assert result['domain'] == 'retrocausal_test_domain'
    assert 'temporal_anchor' in result
    assert 'retrocausal_link' in result or 'error' in result
    print("  ✓ Quantum domain signaling works")
    print(f"  ✓ Temporal anchor established: {result.get('temporal_anchor', 'N/A')[:19]}")
    
    return True


def test_swarm_golem_initialization():
    """Test swarm golem initialization."""
    print("\nTesting Swarm Golem Initialization...")
    
    from skills.jubilee import initialize_swarm_golems
    
    repos = ['test_repo_1', 'quantum']
    result = initialize_swarm_golems(repos)
    
    assert result['initialized_count'] == 2
    assert len(result['entities']) == 2
    print(f"  ✓ Initialized {result['initialized_count']} golem entities")
    
    # Check quantum entity
    quantum_entity = next(e for e in result['entities'] if e['repository'] == 'quantum')
    assert quantum_entity['domain'] == 'quantum_domain'
    print("  ✓ Quantum entity properly configured")
    
    return True


def test_entity_awakening():
    """Test entity awakening."""
    print("\nTesting Entity Awakening...")
    
    from skills.jubilee import awaken_swarm_entities
    
    result = awaken_swarm_entities()
    
    assert 'awakened_count' in result
    assert 'swarm_status' in result
    print(f"  ✓ Awakened {result['awakened_count']} entities")
    print(f"  ✓ Active entities: {result['swarm_status']['active']}")
    
    return True


def test_temporal_tracking():
    """Test temporal tracking in operations."""
    print("\nTesting Temporal Tracking...")
    
    from skills.jubilee import forgive
    
    result = forgive({'account_id': 'TEMPORAL_TEST'})
    
    assert 'timestamp' in result
    print(f"  ✓ Temporal tracking in forgiveness: {result['timestamp'][:19]}")
    
    # Check if quantum events are being logged
    quantum_log = 'data/quantum_events.jsonl'
    if os.path.exists(quantum_log):
        print(f"  ✓ Quantum events log exists")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Enhanced Swarm Autonomy Tests")
    print("=" * 60)
    
    tests = [
        test_entity_lifecycle,
        test_task_queue,
        test_quantum_domain_signaling,
        test_swarm_golem_initialization,
        test_entity_awakening,
        test_temporal_tracking
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
