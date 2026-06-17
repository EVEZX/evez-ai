#!/usr/bin/env python3
"""
Test script for swarm workflow configuration.
Validates that all necessary files and configurations are in place.
"""

import os
import sys
import json
from pathlib import Path


def test_directory_structure():
    """Test that required directories exist."""
    print("Testing directory structure...")
    
    required_dirs = [
        'skills',
        'data',
        'third_party/jubilee-online',
        'scripts'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✓ {dir_path} exists")
        else:
            print(f"  ✗ {dir_path} missing")
            return False
    
    return True


def test_required_files():
    """Test that required files exist."""
    print("\nTesting required files...")
    
    required_files = [
        'SOUL.md',
        'skills/jubilee.py',
        'scripts/swarm_bootstrap.sh',
        'scripts/jubilee_up.sh',
        'third_party/jubilee-online/docker-compose.yml',
        'third_party/jubilee-online/Dockerfile',
        'third_party/jubilee-online/main.py',
        'third_party/jubilee-online/requirements.txt',
        'docs/swarm-setup.md'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path} exists")
        else:
            print(f"  ✗ {file_path} missing")
            return False
    
    return True


def test_script_permissions():
    """Test that scripts are executable."""
    print("\nTesting script permissions...")
    
    scripts = [
        'scripts/swarm_bootstrap.sh',
        'scripts/jubilee_up.sh'
    ]
    
    for script in scripts:
        if os.path.exists(script) and os.access(script, os.X_OK):
            print(f"  ✓ {script} is executable")
        else:
            print(f"  ✗ {script} not executable")
            return False
    
    return True


def test_jubilee_skills():
    """Test that jubilee skills can be imported."""
    print("\nTesting jubilee skills...")
    
    try:
        sys.path.insert(0, os.getcwd())
        from skills import jubilee
        
        # Check that required functions exist
        required_functions = [
            'forgive',
            'molt_post',
            'quantum_sim',
            'tail_events',
            'swarm_status'
        ]
        
        for func_name in required_functions:
            if hasattr(jubilee, func_name):
                print(f"  ✓ {func_name} function exists")
            else:
                print(f"  ✗ {func_name} function missing")
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ Error importing skills: {e}")
        return False


def test_soul_config():
    """Test SOUL.md configuration."""
    print("\nTesting SOUL.md configuration...")
    
    try:
        with open('SOUL.md', 'r') as f:
            content = f.read()
        
        required_terms = [
            'Pan-Phenomenological',
            'Memory is Sacred',
            'Shell is Mutable',
            'events.jsonl'
        ]
        
        for term in required_terms:
            if term in content:
                print(f"  ✓ '{term}' found in SOUL.md")
            else:
                print(f"  ✗ '{term}' not found in SOUL.md")
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ Error reading SOUL.md: {e}")
        return False


def test_docker_config():
    """Test Docker configuration."""
    print("\nTesting Docker configuration...")
    
    try:
        with open('third_party/jubilee-online/docker-compose.yml', 'r') as f:
            content = f.read()
        
        required_items = [
            'jubilee',
            '8000:8000',
            'JUBILEE_MODE',
            'healthcheck'
        ]
        
        for item in required_items:
            if item in content:
                print(f"  ✓ '{item}' found in docker-compose.yml")
            else:
                print(f"  ✗ '{item}' not found in docker-compose.yml")
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ Error reading docker-compose.yml: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Swarm Workflow Configuration Tests")
    print("=" * 60)
    
    tests = [
        test_directory_structure,
        test_required_files,
        test_script_permissions,
        test_jubilee_skills,
        test_soul_config,
        test_docker_config
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n  ✗ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"✓ All tests passed ({passed}/{total})")
        print("=" * 60)
        return 0
    else:
        print(f"✗ Some tests failed ({passed}/{total} passed)")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
