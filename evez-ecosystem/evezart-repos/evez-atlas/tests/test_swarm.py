"""
Comprehensive test suite for Evez666 quantum entity farm.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.mark.asyncio
async def test_entity_spawn():
    """Test basic entity spawning."""
    from src.mastra.agents.swarm_director import SwarmDirector
    
    director = SwarmDirector()
    entity = await director.spawn_entity("test-1", {"role": "tester"})
    
    assert entity["status"] == "active"
    assert "fingerprint" in entity


@pytest.mark.asyncio
async def test_intelligence_propagation():
    """Test intelligence propagation."""
    from src.mastra.agents.swarm_director import SwarmDirector
    
    director = SwarmDirector()
    await director.spawn_entity("src", {"role": "source"})
    await director.spawn_entity("dst", {"role": "destination"})
    await director.propagate_intelligence("src", ["dst"])
    
    assert director.events_log.exists()


def test_quantum_kernel():
    """Test quantum kernel estimation."""
    from quantum import quantum_kernel_estimation
    
    k = quantum_kernel_estimation([0.5]*10, [0.5]*10)
    assert 0.9 < k <= 1.0


@pytest.mark.asyncio
async def test_forgiveness_api():
    """Test Jubilee forgiveness API."""
    from src.api.jubilee_endpoints import forgive_debt, ForgivenessRequest
    
    req = ForgivenessRequest(account_id="TEST", debt_amount=100, quantum_mode=True)
    result = await forgive_debt(req)
    
    assert result["new_debt"] == 0.0
    assert result["mechanism"] == "quantum_collapse"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
