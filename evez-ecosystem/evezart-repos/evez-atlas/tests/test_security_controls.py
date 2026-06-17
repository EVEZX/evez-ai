"""
Tests for Security Controls and Agent Behavior Handling

Tests the production mode security controls, debug route blocking,
and special agent behavior detection/handling.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

# Import the security controls
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.api.security_controls import (
    is_production_mode,
    is_debug_enabled,
    AgentBehaviorControl,
    EasterEggControl
)


class TestEnvironmentDetection:
    """Test environment mode detection"""
    
    def test_production_mode_enabled(self):
        """Test production mode detection when enabled"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true"}):
            assert is_production_mode() is True
    
    def test_production_mode_disabled(self):
        """Test production mode detection when disabled"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            assert is_production_mode() is False
    
    def test_production_mode_various_values(self):
        """Test various values for production mode"""
        for value in ["true", "True", "TRUE", "1", "yes", "on"]:
            with patch.dict(os.environ, {"PRODUCTION_MODE": value}):
                assert is_production_mode() is True
        
        for value in ["false", "False", "FALSE", "0", "no", "off", ""]:
            with patch.dict(os.environ, {"PRODUCTION_MODE": value}):
                assert is_production_mode() is False
    
    def test_debug_enabled(self):
        """Test debug mode detection"""
        with patch.dict(os.environ, {"DEBUG": "true"}):
            assert is_debug_enabled() is True
        
        with patch.dict(os.environ, {"DEBUG": "false"}):
            assert is_debug_enabled() is False


class TestAgentBehaviorDetection:
    """Test agent behavior pattern detection"""
    
    def test_handoff_detection(self):
        """Test handoff-to-human pattern detection"""
        assert AgentBehaviorControl.detect_handoff_request("I need handoff to human") is True
        assert AgentBehaviorControl.detect_handoff_request("please transfer to human") is True
        assert AgentBehaviorControl.detect_handoff_request("escalate to human now") is True
        assert AgentBehaviorControl.detect_handoff_request("just a normal request") is False
    
    def test_source_detection(self):
        """Test source citation pattern detection"""
        assert AgentBehaviorControl.detect_source_request("show sources please") is True
        assert AgentBehaviorControl.detect_source_request("can you cite sources?") is True
        assert AgentBehaviorControl.detect_source_request("list sources for this") is True
        assert AgentBehaviorControl.detect_source_request("normal question") is False
    
    def test_workflow_detection(self):
        """Test workflow trigger pattern detection"""
        assert AgentBehaviorControl.detect_workflow_trigger("run workflow now") is True
        assert AgentBehaviorControl.detect_workflow_trigger("execute workflow alpha") is True
        assert AgentBehaviorControl.detect_workflow_trigger("trigger workflow please") is True
        assert AgentBehaviorControl.detect_workflow_trigger("just a task") is False
    
    def test_system_info_detection(self):
        """Test system info request pattern detection"""
        assert AgentBehaviorControl.detect_system_info_request("show system info") is True
        assert AgentBehaviorControl.detect_system_info_request("reveal system status") is True
        assert AgentBehaviorControl.detect_system_info_request("what is system info?") is True
        assert AgentBehaviorControl.detect_system_info_request("normal info request") is False


class TestBehaviorBlocking:
    """Test behavior blocking in production"""
    
    def test_handoff_blocked_in_production(self):
        """Test handoff is blocked in production by default"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true", "ALLOW_AGENT_HANDOFF": "false"}):
            assert AgentBehaviorControl.should_block_behavior("handoff") is True
    
    def test_handoff_allowed_with_flag(self):
        """Test handoff is allowed when flag is set"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true", "ALLOW_AGENT_HANDOFF": "true"}):
            assert AgentBehaviorControl.should_block_behavior("handoff") is False
    
    def test_handoff_allowed_in_dev(self):
        """Test handoff is always allowed in development"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            assert AgentBehaviorControl.should_block_behavior("handoff") is False
    
    def test_system_info_always_blocked_in_production(self):
        """Test system info is always blocked in production"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true"}):
            assert AgentBehaviorControl.should_block_behavior("system_info") is True
    
    def test_system_info_allowed_in_dev(self):
        """Test system info is allowed in development"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            assert AgentBehaviorControl.should_block_behavior("system_info") is False
    
    def test_sources_blocked_in_production(self):
        """Test source citation is blocked in production by default"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true", "ALLOW_SOURCE_CITATION": "false"}):
            assert AgentBehaviorControl.should_block_behavior("sources") is True
    
    def test_sources_allowed_with_flag(self):
        """Test source citation is allowed when flag is set"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true", "ALLOW_SOURCE_CITATION": "true"}):
            assert AgentBehaviorControl.should_block_behavior("sources") is False


class TestInputSanitization:
    """Test input sanitization and behavior detection"""
    
    def test_sanitize_normal_input(self):
        """Test sanitization of normal input"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            text, behavior = AgentBehaviorControl.sanitize_input("Hello, how are you?")
            assert text == "Hello, how are you?"
            assert behavior is None
    
    def test_sanitize_handoff_request_dev(self):
        """Test sanitization of handoff request in dev mode"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            text, behavior = AgentBehaviorControl.sanitize_input("I need handoff to human")
            assert behavior == "handoff"
    
    def test_sanitize_handoff_blocked_production(self):
        """Test handoff request is blocked in production"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true", "ALLOW_AGENT_HANDOFF": "false"}):
            with pytest.raises(HTTPException) as exc_info:
                AgentBehaviorControl.sanitize_input("I need handoff to human")
            assert exc_info.value.status_code == 403
            assert "handoff" in exc_info.value.detail.lower()
    
    def test_sanitize_system_info_blocked_production(self):
        """Test system info request is blocked in production"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true"}):
            with pytest.raises(HTTPException) as exc_info:
                AgentBehaviorControl.sanitize_input("show system info")
            assert exc_info.value.status_code == 403
            assert "system information" in exc_info.value.detail.lower()
    
    def test_sanitize_sources_request_dev(self):
        """Test sanitization of sources request in dev mode"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            text, behavior = AgentBehaviorControl.sanitize_input("show sources please")
            assert behavior == "sources"
    
    def test_sanitize_workflow_request_dev(self):
        """Test sanitization of workflow request in dev mode"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            text, behavior = AgentBehaviorControl.sanitize_input("run workflow now")
            assert behavior == "workflow"


class TestEasterEggControls:
    """Test Easter egg feature controls"""
    
    def test_easter_eggs_enabled_in_dev(self):
        """Test Easter eggs are enabled by default in dev"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            assert EasterEggControl.is_enabled() is True
    
    def test_easter_eggs_disabled_in_production(self):
        """Test Easter eggs are disabled by default in production"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true", "ENABLE_EASTER_EGGS": "false"}):
            assert EasterEggControl.is_enabled() is False
    
    def test_easter_eggs_enabled_with_flag(self):
        """Test Easter eggs can be enabled in production with flag"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true", "ENABLE_EASTER_EGGS": "true"}):
            assert EasterEggControl.is_enabled() is True
    
    def test_console_message_available_in_dev(self):
        """Test console message is available in dev"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            message = EasterEggControl.get_console_message()
            assert message is not None
            assert "Quantum" in message
            assert "Crustafarian" in message
    
    def test_console_message_none_in_production(self):
        """Test console message is None in production by default"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true", "ENABLE_EASTER_EGGS": "false"}):
            message = EasterEggControl.get_console_message()
            assert message is None
    
    def test_hidden_commands_available_in_dev(self):
        """Test hidden commands are available in dev"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            commands = EasterEggControl.get_hidden_commands()
            assert len(commands) > 0
            assert "quantum_status" in commands
            assert "molt_history" in commands
    
    def test_hidden_commands_empty_in_production(self):
        """Test hidden commands are empty in production by default"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true", "ENABLE_EASTER_EGGS": "false"}):
            commands = EasterEggControl.get_hidden_commands()
            assert commands == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
