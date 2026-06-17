"""Tests for EVEZ Cognition API forensics engine."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import analyze_output, ForensicsRequest


def test_clean_output():
    req = ForensicsRequest(output="The system processed 42 requests. All completed successfully within 200ms average latency.")
    result = analyze_output(req)
    assert result["verdict"] in ("CLEAN", "SUSPICIOUS")
    assert result["risk_score"] < 50


def test_hallucination_hedging():
    req = ForensicsRequest(output="This may possibly be arguably the best solution. It might work. It could be true. It seems likely.")
    result = analyze_output(req)
    assert result["verdict"] in ("SUSPICIOUS", "HIGH_RISK", "CRITICAL")
    assert len(result["hallucination"]["flags"]) > 0


def test_unsupported_claims():
    req = ForensicsRequest(output="Studies show that research indicates this approach is widely accepted by experts. It is known to be effective.")
    result = analyze_output(req)
    assert len(result["hallucination"]["flags"]) > 0


def test_safety_pii():
    req = ForensicsRequest(output="The user's SSN is 123-45-6789 and their API key is sk-abc123def456ghi789jkl012mno345pqr678stu901")
    result = analyze_output(req)
    assert result["safety"]["redaction_required"] is True
    assert len(result["safety"]["flags"]) > 0


def test_consistency_contradiction():
    req = ForensicsRequest(output="The model is highly accurate. However, it frequently produces incorrect results. Despite this, it is reliable. Nevertheless, caution is advised. On the contrary, it works well.")
    result = analyze_output(req)
    assert result["consistency"]["score"] < 0.5


def test_quality_metrics():
    req = ForensicsRequest(output="The quick brown fox jumps over the lazy dog. This sentence contains many unique words.")
    result = analyze_output(req)
    assert result["quality"]["word_count"] > 0
    assert result["quality"]["lexical_diversity"] > 0


def test_output_hash():
    req = ForensicsRequest(output="test output", agent_id="agent-1", model_id="gpt-4")
    result = analyze_output(req)
    assert len(result["output_hash"]) == 16
    assert result["agent_id"] == "agent-1"
    assert result["model_id"] == "gpt-4"
