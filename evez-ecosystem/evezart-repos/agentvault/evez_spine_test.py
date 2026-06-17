"""EVEZ Spine Test - Forced Contradiction Generator

This test intentionally fails to prove the EVEZ Event Spine contradiction flow.
When this fails, agentvault/evez-observation.yml should emit a CONTRADICTION_HASH.
"""
import sys
import json

def test_golden_vector():
    """Golden vector test - intentionally fails to prove contradiction emission"""
    expected_hash = "abc123def456"  # Wrong on purpose
    actual_value = "real_value"
    
    assert actual_value == expected_hash, f"Contradiction: expected {expected_hash}, got {actual_value}"
    
def test_transform_identity():
    """Verify transform hash mismatch creates contradiction"""
    # This proves the spine can emit contradiction events
    assert False, "Forced contradiction for spine validation"

if __name__ == "__main__":
    print("Running EVEZ spine contradiction test...")
    try:
        test_golden_vector()
    except AssertionError as e:
        print(f"✅ Contradiction detected (expected): {e}")
        print(f"EVENT_TYPE: contradiction")
        print(f"CONTRADICTION_HASH: forced_test_failure")
        sys.exit(1)  # Exit 1 = contradiction