"""
Test suite for Semantic Possibility Space module
Tests the multi-interpretation quantum semantic engine
"""

import pytest
import asyncio
from pathlib import Path
import json
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mastra.semantics.semantic_possibility_space import SemanticPossibilitySpace


class TestSemanticPossibilitySpace:
    """Test the semantic possibility space implementation"""
    
    def test_initialization(self):
        """Test that SemanticPossibilitySpace initializes correctly"""
        space = SemanticPossibilitySpace("@TestCreator")
        
        assert space.creator == "@TestCreator"
        assert space.entity_id is not None
        assert len(space.entity_id) > 0
        assert space.data_dir.exists()
        assert space.events_log.parent.exists()
    
    def test_generate_interpretations(self):
        """Test interpretation generation"""
        space = SemanticPossibilitySpace()
        
        test_input = "test input text"
        interpretations = space.generate_interpretations(test_input)
        
        assert len(interpretations) == 8
        assert all(isinstance(i, str) for i in interpretations)
        assert all(len(i) > 0 for i in interpretations)
    
    def test_generate_interpretations_custom_count(self):
        """Test interpretation generation with custom count"""
        space = SemanticPossibilitySpace()
        
        test_input = "test input"
        interpretations = space.generate_interpretations(test_input, n_candidates=5)
        
        assert len(interpretations) == 5
    
    @pytest.mark.asyncio
    async def test_score_semantic_similarity(self):
        """Test semantic similarity scoring"""
        space = SemanticPossibilitySpace()
        
        interpretations = ["test one", "test two", "test three"]
        result = await space.score_semantic_similarity(interpretations)
        
        assert "scores" in result
        assert "probabilities" in result
        assert "top_interpretation" in result
        assert "top_probability" in result
        assert "collapse_entropy" in result
        
        assert len(result["scores"]) == 3
        assert len(result["probabilities"]) == 3
        assert 0 <= result["top_interpretation"] < 3
        assert 0.0 <= result["top_probability"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_score_with_context(self):
        """Test scoring with context sequence"""
        space = SemanticPossibilitySpace()
        
        interpretations = ["interp one", "interp two"]
        context = ["context one", "context two"]
        result = await space.score_semantic_similarity(interpretations, context)
        
        assert "scores" in result
        assert len(result["scores"]) == 2
    
    @pytest.mark.asyncio
    async def test_recursive_meaning_exploration(self):
        """Test recursive meaning exploration"""
        space = SemanticPossibilitySpace()
        
        test_input = "explore this meaning"
        history = await space.recursive_meaning_exploration(test_input, steps=3)
        
        assert len(history) == 3
        assert all("scores" in h for h in history)
        assert all("probabilities" in h for h in history)
    
    @pytest.mark.asyncio
    async def test_recursive_exploration_with_context(self):
        """Test recursive exploration with initial context"""
        space = SemanticPossibilitySpace()
        
        test_input = "test input"
        initial_context = ["initial context"]
        history = await space.recursive_meaning_exploration(
            test_input, steps=2, context=initial_context
        )
        
        assert len(history) == 2
    
    @pytest.mark.asyncio
    async def test_transcend_semantic_void(self):
        """Test the full transcendence pipeline"""
        space = SemanticPossibilitySpace()
        
        test_input = "optimal states of procession"
        result = await space.transcend_semantic_void(test_input)
        
        assert "witness_fact" in result
        assert "plausibility_violation" in result
        assert "manifold_entropy" in result
        assert "self_explanation" in result
        
        assert isinstance(result["witness_fact"], str)
        assert isinstance(result["plausibility_violation"], bool)
        assert isinstance(result["manifold_entropy"], float)
        assert isinstance(result["self_explanation"], str)
    
    def test_softmax_computation(self):
        """Test softmax probability computation"""
        space = SemanticPossibilitySpace()
        
        scores = [1.0, 2.0, 3.0]
        probabilities = space._softmax(scores)
        
        assert len(probabilities) == 3
        assert abs(sum(probabilities) - 1.0) < 1e-6  # Sum to 1
        assert all(0.0 <= p <= 1.0 for p in probabilities)
        assert probabilities[2] > probabilities[1] > probabilities[0]  # Higher scores = higher prob
    
    def test_softmax_empty(self):
        """Test softmax with empty input"""
        space = SemanticPossibilitySpace()
        
        probabilities = space._softmax([])
        assert probabilities == []
    
    def test_entropy_computation(self):
        """Test entropy computation"""
        space = SemanticPossibilitySpace()
        
        # Uniform distribution has maximum entropy
        uniform_probs = [0.25, 0.25, 0.25, 0.25]
        entropy_uniform = space._compute_entropy(uniform_probs)
        
        # Single probability has minimum entropy (zero)
        single_prob = [1.0, 0.0, 0.0, 0.0]
        entropy_single = space._compute_entropy(single_prob)
        
        assert entropy_uniform > entropy_single
        assert entropy_single < 0.1  # Near zero
    
    def test_event_logging(self):
        """Test that events are logged correctly"""
        space = SemanticPossibilitySpace()
        
        # Generate some activity
        interpretations = space.generate_interpretations("test")
        
        # Check that events were logged
        assert space.events_log.exists()
        
        with space.events_log.open("r") as f:
            events = [json.loads(line) for line in f]
        
        assert len(events) > 0
        assert all("type" in e for e in events)
        assert all("timestamp" in e for e in events)
        assert all("entity_id" in e for e in events)
        assert all("data" in e for e in events)
    
    def test_mock_parallel_interp(self):
        """Test mock interpretation generation"""
        space = SemanticPossibilitySpace()
        
        prompt = "Test prompt: sample text"
        interp = space._mock_parallel_interp(prompt)
        
        assert isinstance(interp, str)
        assert "sample text" in interp
        assert "->" in interp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
