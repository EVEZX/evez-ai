"""EVEZ Logic Module - Symbolic Reasoning"""
import hashlib
import json

def compute_hash(data):
    """Compute canonical hash of any data structure"""
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]

def validate_schema(event, schema):
    """Validate event against constitutional schema"""
    required = schema.get("required", [])
    return all(k in event for k in required)
