#!/usr/bin/env python3
"""Auto-mission generation from multi-vantage disagreements.

Goal
  Turn *disagreements* (probe results that differ across vantages) into
  spine-grade missions with suggested Σf and Ω.

Design principles
  - Read-only analysis of existing spine events.
  - Append-only: missions are emitted as new events; nothing is rewritten.
  - Conservative: only trigger when the same target was probed multiple times
    with different results across distinct vantages.

Event format (kind = mission.disagreement)
  {
    "kind": "mission.disagreement",
    "ts": "...Z",
    "trace_id": "M...",
    "key": { ... },
    "observations": [{"vantage_id": "...", "value": ... , "ts": "..."}, ...],
    "Sigma_f": [...],
    "Omega": "...",
    "recommended_probe": "..."
  }
"""

from __future__ import annotations

import datetime
import hashlib
import json
from typing import Any, Dict, Iterable, List, Tuple


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat() + "Z"


def _stable_hash(obj: Any) -> str:
    b = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def _key_for_probe(ev: Dict[str, Any]) -> Tuple[str, Tuple[Tuple[str, Any], ...]] | None:
    k = ev.get("kind")
    t = ev.get("target") or {}
    if k == "probe.dns":
        return (k, tuple(sorted({"name": t.get("name"), "rrtype": t.get("rrtype"), "resolver": t.get("resolver")}.items())))
    if k == "probe.http":
        return (k, tuple(sorted({"url": t.get("url"), "method": t.get("method")}.items())))
    if k == "probe.tls":
        return (k, tuple(sorted({"host": t.get("host"), "port": t.get("port"), "server_name": t.get("server_name")}.items())))
    if k == "probe.ping":
        return (k, tuple(sorted({"host": t.get("host")}.items())))
    return None


def _value_for_probe(ev: Dict[str, Any]) -> Any:
    k = ev.get("kind")
    if k == "probe.dns":
        return sorted(ev.get("answers") or [])
    if k == "probe.http":
        return {"status": ev.get("status"), "server": (ev.get("headers") or {}).get("Server")}
    if k == "probe.tls":
        cert = ev.get("cert") or {}
        return {"der_sha256": cert.get("der_sha256"), "issuer": cert.get("issuer"), "notAfter": cert.get("notAfter")}
    if k == "probe.ping":
        return {"ok": ev.get("ok"), "latency_ms": ev.get("latency_ms")}
    return None


def find_disagreements(events: Iterable[Dict[str, Any]], min_vantages: int = 2) -> List[Dict[str, Any]]:
    """Return mission events for any probe target with conflicting values across vantages."""

    buckets: Dict[Tuple[str, Tuple[Tuple[str, Any], ...]], List[Dict[str, Any]]] = {}
    for ev in events:
        key = _key_for_probe(ev)
        if not key:
            continue
        v = ev.get("vantage_id") or "default"
        buckets.setdefault(key, []).append({
            "vantage_id": v,
            "ts": ev.get("ts"),
            "value": _value_for_probe(ev),
        })

    missions: List[Dict[str, Any]] = []
    for (kind, key_items), obs in buckets.items():
        # collapse per-vantage to most recent observation
        latest: Dict[str, Dict[str, Any]] = {}
        for o in obs:
            v = o["vantage_id"]
            if v not in latest or (o.get("ts") or "") > (latest[v].get("ts") or ""):
                latest[v] = o
        if len(latest) < min_vantages:
            continue

        values = {json.dumps(o["value"], sort_keys=True, ensure_ascii=False) for o in latest.values()}
        if len(values) <= 1:
            continue

        key_obj = {"probe_kind": kind, "target": dict(key_items)}
        payload = {
            "key": key_obj,
            "observations": list(latest.values()),
        }
        trace_id = "M" + _stable_hash(payload)[:16]

        # Suggested Σf/Ω: keep it generic and reliable.
        sigma_f = [
            "single_vantage_diagnosis",
            "projection_as_canon",
            "pending_vs_final_confusion",
        ]
        omega = "multi-vantage probes + explicit pending labels + append-only witness"

        recommended_probe = {
            "probe.dns": "run probe.dns from 2+ resolvers/vantages; compare TTL and authoritative",
            "probe.http": "run probe.http from 2+ networks; compare status + headers + latency",
            "probe.tls": "run probe.tls from 2+ vantages; compare leaf cert hash + time validity",
            "probe.ping": "run probe.ping + tcp connect from 2+ vantages; compare reachability",
        }.get(kind, "repeat probe from 2+ vantages; isolate divergence")

        missions.append({
            "kind": "mission.disagreement",
            "ts": utc_now(),
            "trace_id": trace_id,
            "truth_plane": "truth",
            **payload,
            "Sigma_f": sigma_f,
            "Omega": omega,
            "recommended_probe": recommended_probe,
        })

    return missions


def mission_trace_ids(events: Iterable[Dict[str, Any]]) -> set[str]:
    """Collect existing mission trace IDs so we don't spam duplicates."""
    out: set[str] = set()
    for ev in events:
        if (ev.get("kind") or "").startswith("mission.") and ev.get("trace_id"):
            out.add(str(ev["trace_id"]))
    return out


def filter_new_missions(missions: List[Dict[str, Any]], existing_trace_ids: set[str]) -> List[Dict[str, Any]]:
    return [m for m in missions if m.get("trace_id") not in existing_trace_ids]
