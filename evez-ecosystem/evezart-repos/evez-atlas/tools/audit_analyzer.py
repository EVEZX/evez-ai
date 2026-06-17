#!/usr/bin/env python3
"""Analyze audit logs for time-order anomalies (local-only, consent-only)."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

import httpx

BASE_DIR = Path(__file__).resolve().parents[1]
AUDIT_LOG_PATH = BASE_DIR / "src" / "memory" / "audit.jsonl"
OUT_DIR = BASE_DIR / "tools" / "out"


@dataclass
class AuditEntry:
    output_id: str
    endpoint: str
    api_key: str
    timestamp: Optional[float]


def _parse_timestamp(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.timestamp()
        except ValueError:
            return None
    return None


def load_audit_entries(path: Path) -> List[AuditEntry]:
    entries: List[AuditEntry] = []
    if not path.exists():
        return entries
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        endpoint = record.get("endpoint", "")
        # Load both /resolve-awareness and /legion-status entries for anomaly detection
        if "/resolve-awareness" not in endpoint and "/legion-status" not in endpoint:
            continue
        output_id = (
            record.get("output_id")
            or record.get("entity_id")
            or record.get("result", {}).get("output_id")
            or "unknown"
        )
        entries.append(
            AuditEntry(
                output_id=output_id,
                endpoint=endpoint,
                api_key=record.get("api_key", "unknown"),
                timestamp=_parse_timestamp(record.get("timestamp")),
            )
        )
    return entries


def summarize(entries: Iterable[AuditEntry]) -> Dict[str, Any]:
    by_api_key = Counter()
    by_endpoint = Counter()
    by_output_id = Counter()
    total = 0
    for entry in entries:
        total += 1
        by_api_key[entry.api_key] += 1
        by_endpoint[entry.endpoint] += 1
        by_output_id[entry.output_id] += 1
    return {
        "total_records": total,
        "by_api_key": dict(by_api_key),
        "by_endpoint": dict(by_endpoint),
        "by_output_id": dict(by_output_id),
    }


def fetch_instantiation_timestamps(api_base: str, api_key: str) -> Dict[str, float]:
    instantiation_map: Dict[str, float] = {}
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                f"{api_base}/legion-status",
                headers={"X-API-Key": api_key},
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.RequestError, httpx.HTTPStatusError, ValueError):
        return instantiation_map

    for entity in payload.get("entities", []):
        output_id = entity.get("output_id")
        metadata = entity.get("metadata", {}) if isinstance(entity, dict) else {}
        for key in ("instantiated_at", "created_at", "timestamp"):
            if key in metadata:
                ts = _parse_timestamp(metadata.get(key))
                if ts is not None and output_id:
                    instantiation_map[output_id] = ts
                    break
    return instantiation_map


def detect_anomalies(
    entries: Iterable[AuditEntry],
    instantiation_map: Dict[str, float],
) -> List[Dict[str, Any]]:
    first_seen: Dict[str, float] = {}
    high_priority_output_ids: Set[str] = set()  # Track entries with high-priority anomalies
    
    for entry in entries:
        if entry.timestamp is None:
            continue
        if entry.output_id not in first_seen or entry.timestamp < first_seen[entry.output_id]:
            first_seen[entry.output_id] = entry.timestamp

    anomalies: List[Dict[str, Any]] = []
    
    # First pass: check for high-priority anomalies per entry
    # These are security-critical checks that should prevent further processing of the same entry
    for entry in entries:
        # High-priority check: tier0 public key accessing sensitive endpoints
        if entry.api_key.endswith("_public") and entry.endpoint == "/legion-status":
            anomalies.append(
                {
                    "output_id": entry.output_id,
                    "api_key": entry.api_key,
                    "endpoint": entry.endpoint,
                    "reason": "tier0_public_access_to_legion_status",
                }
            )
            high_priority_output_ids.add(entry.output_id)
            continue  # prevent duplicate anomaly entries for the same record
        
        # Additional high-priority checks can be added here with continue statements
    
    # Second pass: check for time-based anomalies
    # Skip output_ids that already have high-priority anomalies
    for output_id, first_timestamp in first_seen.items():
        if output_id in high_priority_output_ids:
            continue  # Skip entries already flagged with high-priority anomalies
            
        instantiated_at = instantiation_map.get(output_id)
        if instantiated_at is None:
            anomalies.append(
                {
                    "output_id": output_id,
                    "first_audit_timestamp": first_timestamp,
                    "reason": "no_instantiation_timestamp_available",
                }
            )
            continue
        if instantiated_at > first_timestamp:
            anomalies.append(
                {
                    "output_id": output_id,
                    "first_audit_timestamp": first_timestamp,
                    "instantiated_at": instantiated_at,
                    "delta_seconds": instantiated_at - first_timestamp,
                }
            )
    return anomalies


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default="tier3_director")
    parser.add_argument("--api-base", default="http://localhost:8000")
    parser.add_argument("--audit-log", default=str(AUDIT_LOG_PATH))
    args = parser.parse_args()

    audit_path = Path(args.audit_log)
    entries = load_audit_entries(audit_path)

    summary = summarize(entries)
    write_json(OUT_DIR / "audit_summary.json", summary)

    instantiation_map = fetch_instantiation_timestamps(args.api_base, args.api_key)
    anomalies = detect_anomalies(entries, instantiation_map)
    write_json(OUT_DIR / "anomalies.json", anomalies)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
