#!/usr/bin/env python3
"""
Security Controls Demo

Demonstrates how the security controls work for debug routes,
agent handoff behavior, and Easter eggs in different environments.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.security_controls import (
    is_production_mode,
    is_debug_enabled,
    AgentBehaviorControl,
    EasterEggControl
)


def print_section(title):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def demo_environment_detection():
    """Demonstrate environment detection"""
    print_section("Environment Detection")
    
    print(f"PRODUCTION_MODE: {os.getenv('PRODUCTION_MODE', 'not set')}")
    print(f"DEBUG: {os.getenv('DEBUG', 'not set')}")
    print(f"\nIs production mode: {is_production_mode()}")
    print(f"Is debug enabled: {is_debug_enabled()}")


def demo_agent_behavior_detection():
    """Demonstrate agent behavior detection"""
    print_section("Agent Behavior Detection")
    
    test_inputs = [
        "I need handoff to human",
        "show sources please",
        "run workflow now",
        "show system info",
        "Just a normal question"
    ]
    
    for test_input in test_inputs:
        print(f"\nInput: '{test_input}'")
        print(f"  Handoff detected: {AgentBehaviorControl.detect_handoff_request(test_input)}")
        print(f"  Sources detected: {AgentBehaviorControl.detect_source_request(test_input)}")
        print(f"  Workflow detected: {AgentBehaviorControl.detect_workflow_trigger(test_input)}")
        print(f"  System info detected: {AgentBehaviorControl.detect_system_info_request(test_input)}")


def demo_behavior_blocking():
    """Demonstrate behavior blocking policies"""
    print_section("Behavior Blocking Policies")
    
    behaviors = ["handoff", "sources", "workflow", "system_info"]
    
    print(f"\nCurrent environment: {'PRODUCTION' if is_production_mode() else 'DEVELOPMENT'}")
    print(f"\nBlocking status for each behavior:")
    
    for behavior in behaviors:
        blocked = AgentBehaviorControl.should_block_behavior(behavior)
        status = "BLOCKED ❌" if blocked else "ALLOWED ✓"
        print(f"  {behavior:15s}: {status}")


def demo_easter_eggs():
    """Demonstrate Easter egg controls"""
    print_section("Easter Egg Controls")
    
    print(f"Easter eggs enabled: {EasterEggControl.is_enabled()}")
    
    console_msg = EasterEggControl.get_console_message()
    if console_msg:
        print(f"\nConsole message:")
        print(console_msg)
    else:
        print("\nConsole message: Not available (disabled)")
    
    hidden_commands = EasterEggControl.get_hidden_commands()
    if hidden_commands:
        print(f"\nHidden commands available ({len(hidden_commands)}):")
        for cmd, desc in hidden_commands.items():
            print(f"  {cmd:25s}: {desc}")
    else:
        print("\nHidden commands: Not available (disabled)")


def demo_input_sanitization():
    """Demonstrate input sanitization"""
    print_section("Input Sanitization")
    
    test_inputs = [
        "Hello, how are you?",
        "I need handoff to human",
        "show system info"
    ]
    
    for test_input in test_inputs:
        print(f"\nInput: '{test_input}'")
        try:
            sanitized, behavior = AgentBehaviorControl.sanitize_input(test_input)
            print(f"  Result: Allowed")
            print(f"  Behavior type: {behavior if behavior else 'None'}")
        except Exception as e:
            print(f"  Result: BLOCKED")
            print(f"  Reason: {e}")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("  SECURITY CONTROLS DEMONSTRATION")
    print("  Evez666 Agent System")
    print("=" * 60)
    
    demo_environment_detection()
    demo_agent_behavior_detection()
    demo_behavior_blocking()
    demo_easter_eggs()
    demo_input_sanitization()
    
    print("\n" + "=" * 60)
    print("  Demo complete!")
    print("=" * 60)
    print("\nTo test different modes, set environment variables:")
    print("  PRODUCTION_MODE=true python3 demo_security.py")
    print("  DEBUG=true python3 demo_security.py")
    print("  ENABLE_EASTER_EGGS=true python3 demo_security.py")
    print()


if __name__ == "__main__":
    main()
