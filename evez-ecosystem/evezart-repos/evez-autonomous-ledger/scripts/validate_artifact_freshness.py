#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "PLUGIN_REGISTRY.json"
HEALTH_PATH = ROOT / "PLUGIN_HEALTH.json"
MAX_AGE_MINUTES = 90


def parse_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def check_fresh(path: pathlib.Path, label: str) -> list[str]:
    failures: list[str] = []
    if not path.exists():
        return [f"{label} missing: {path.name}"]

    data = json.loads(path.read_text(encoding="utf-8"))
    updated_at = data.get("updated_at")
    if not isinstance(updated_at, str) or not updated_at.strip():
        return [f"{label} missing updated_at"]

    try:
        ts = parse_timestamp(updated_at)
    except Exception as exc:
        return [f"{label} invalid updated_at: {exc}"]

    now = datetime.now(timezone.utc)
    age = now - ts.astimezone(timezone.utc)
    if age > timedelta(minutes=MAX_AGE_MINUTES):
        failures.append(f"{label} stale by {age.total_seconds() / 60:.1f} minutes")
    return failures


def main() -> int:
    failures = []
    failures.extend(check_fresh(REGISTRY_PATH, "PLUGIN_REGISTRY"))
    failures.extend(check_fresh(HEALTH_PATH, "PLUGIN_HEALTH"))

    if failures:
        print("Artifact freshness validation failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("Artifact freshness OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
