"""
Integration tests for API endpoints with security controls

Tests that debug routes are properly protected in production mode
and accessible in development mode.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Import the app
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestDebugRoutesInDevelopment:
    """Test debug routes are accessible in development mode"""
    
    def test_swarm_status_accessible_in_dev(self):
        """Test /swarm-status is accessible in development"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            # Re-import to get the updated environment
            if 'src.api.causal_chain_server' in sys.modules:
                del sys.modules['src.api.causal_chain_server']
            if 'src.api.security_controls' in sys.modules:
                del sys.modules['src.api.security_controls']
            
            from src.api.causal_chain_server import app
            client = TestClient(app)
            
            response = client.get("/swarm-status")
            assert response.status_code != 403
    
    def test_security_info_accessible_in_dev(self):
        """Test /security-info is accessible in development"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            # Re-import to get the updated environment
            if 'src.api.causal_chain_server' in sys.modules:
                del sys.modules['src.api.causal_chain_server']
            if 'src.api.security_controls' in sys.modules:
                del sys.modules['src.api.security_controls']
            
            from src.api.causal_chain_server import app
            client = TestClient(app)
            
            response = client.get("/security-info")
            assert response.status_code != 403
            
            # Verify it shows correct production mode
            if response.status_code == 200:
                data = response.json()
                assert data["production_mode"] is False


class TestDebugRoutesInProduction:
    """Test debug routes are blocked in production mode"""
    
    def test_swarm_status_blocked_in_production(self):
        """Test /swarm-status is blocked in production"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true", "DEBUG": "false"}):
            # Re-import to get the updated environment
            if 'src.api.causal_chain_server' in sys.modules:
                del sys.modules['src.api.causal_chain_server']
            if 'src.api.security_controls' in sys.modules:
                del sys.modules['src.api.security_controls']
            
            from src.api.causal_chain_server import app
            client = TestClient(app)
            
            response = client.get("/swarm-status")
            assert response.status_code == 403
            assert "production" in response.json()["detail"].lower()
    
    def test_security_info_blocked_in_production(self):
        """Test /security-info is blocked in production"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "true", "DEBUG": "false"}):
            # Re-import to get the updated environment
            if 'src.api.causal_chain_server' in sys.modules:
                del sys.modules['src.api.causal_chain_server']
            if 'src.api.security_controls' in sys.modules:
                del sys.modules['src.api.security_controls']
            
            from src.api.causal_chain_server import app
            client = TestClient(app)
            
            response = client.get("/security-info")
            assert response.status_code == 403


class TestSecurityInfoEndpoint:
    """Test the /security-info endpoint returns correct information"""
    
    def test_security_info_shows_correct_status(self):
        """Test security info shows correct status"""
        with patch.dict(os.environ, {"PRODUCTION_MODE": "false"}):
            # Re-import to get the updated environment
            if 'src.api.causal_chain_server' in sys.modules:
                del sys.modules['src.api.causal_chain_server']
            if 'src.api.security_controls' in sys.modules:
                del sys.modules['src.api.security_controls']
            
            from src.api.causal_chain_server import app
            client = TestClient(app)
            
            response = client.get("/security-info")
            if response.status_code == 200:
                data = response.json()
                assert "production_mode" in data
                assert "easter_eggs_enabled" in data
                assert "agent_behaviors" in data
                assert data["production_mode"] is False
                assert data["easter_eggs_enabled"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

