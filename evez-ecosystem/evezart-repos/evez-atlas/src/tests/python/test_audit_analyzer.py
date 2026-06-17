import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools import audit_analyzer


def write_audit_log(path: Path, entries):
    content = "\n".join(json.dumps(entry) for entry in entries)
    path.write_text(content, encoding="utf-8")


def test_summary_and_anomaly_degradation(tmp_path):
    audit_path = tmp_path / "audit.jsonl"
    entries = [
        {
            "timestamp": 1700000000.0,
            "entity_id": "output-001",
            "endpoint": "/resolve-awareness",
            "tier": 3,
            "api_key": "tier3_director",
            "result": {"output_id": "output-001"},
        },
        {
            "timestamp": 1700000010.0,
            "entity_id": "output-002",
            "endpoint": "/resolve-awareness",
            "tier": 1,
            "api_key": "tier1_builder",
            "result": {"output_id": "output-002"},
        },
    ]
    write_audit_log(audit_path, entries)

    audit_entries = audit_analyzer.load_audit_entries(audit_path)
    summary = audit_analyzer.summarize(audit_entries)

    assert summary["total_records"] == 2
    assert summary["by_api_key"]["tier3_director"] == 1
    assert summary["by_output_id"]["output-002"] == 1

    anomalies = audit_analyzer.detect_anomalies(audit_entries, {})
    assert len(anomalies) == 2
    assert all(
        anomaly["reason"] == "no_instantiation_timestamp_available"
        for anomaly in anomalies
    )


def test_tier0_public_access_anomaly(tmp_path):
    """Test that tier0_public accessing /legion-status is flagged as an anomaly."""
    audit_path = tmp_path / "audit.jsonl"
    entries = [
        {
            "timestamp": 1700000000.0,
            "entity_id": "legion",
            "endpoint": "/legion-status",
            "tier": 0,
            "api_key": "tier0_public",
            "result": {},
        },
        {
            "timestamp": 1700000010.0,
            "entity_id": "output-001",
            "endpoint": "/resolve-awareness",
            "tier": 0,
            "api_key": "tier0_public",
            "result": {"output_id": "output-001"},
        },
    ]
    write_audit_log(audit_path, entries)

    audit_entries = audit_analyzer.load_audit_entries(audit_path)
    anomalies = audit_analyzer.detect_anomalies(audit_entries, {})
    
    # Should have one high-priority anomaly for tier0_public accessing /legion-status
    tier0_anomalies = [a for a in anomalies if a.get("reason") == "tier0_public_access_to_legion_status"]
    assert len(tier0_anomalies) == 1
    assert tier0_anomalies[0]["api_key"] == "tier0_public"
    assert tier0_anomalies[0]["endpoint"] == "/legion-status"
    
    # Should also have one time-based anomaly for output-001 (no instantiation timestamp)
    time_anomalies = [a for a in anomalies if a.get("reason") == "no_instantiation_timestamp_available"]
    assert len(time_anomalies) == 1
    assert time_anomalies[0]["output_id"] == "output-001"


def test_no_duplicate_anomalies_for_same_entry(tmp_path):
    """Test that a single entry doesn't generate multiple anomalies."""
    audit_path = tmp_path / "audit.jsonl"
    entries = [
        {
            "timestamp": 1700000000.0,
            "entity_id": "legion",
            "endpoint": "/legion-status",
            "tier": 0,
            "api_key": "tier0_public",
            "result": {},
        },
    ]
    write_audit_log(audit_path, entries)

    audit_entries = audit_analyzer.load_audit_entries(audit_path)
    # Even with both high-priority and time-based checks, should only get one anomaly
    # because continue prevents duplicate processing
    anomalies = audit_analyzer.detect_anomalies(audit_entries, {})
    
    # Should only have the high-priority anomaly
    assert len(anomalies) == 1
    assert anomalies[0]["reason"] == "tier0_public_access_to_legion_status"
