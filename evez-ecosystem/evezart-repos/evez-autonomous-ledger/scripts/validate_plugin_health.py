#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
HEALTH_PATH = ROOT / "PLUGIN_HEALTH.json"
REQUIRED_CHECK_KEYS = {
    "id",
    "repo",
    "health_endpoint",
    "skills_endpoint",
    "health",
    "skills",
    "overall_status",
}


def main() -> int:
    if not HEALTH_PATH.exists():
        print("Missing PLUGIN_HEALTH.json")
        return 1

    data = json.loads(HEALTH_PATH.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        print("PLUGIN_HEALTH.json schema must equal 1")
        return 1

    checks = data.get("checks")
    if not isinstance(checks, list):
        print("PLUGIN_HEALTH.json checks must be a list")
        return 1

    failures = []
    for check in checks:
        if not isinstance(check, dict):
            failures.append("check entry is not an object")
            continue
        missing = REQUIRED_CHECK_KEYS - set(check.keys())
        if missing:
            failures.append(f"check {check.get('id', '<unknown>')} missing keys: {sorted(missing)}")

    if failures:
        print("Plugin health validation failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("PLUGIN_HEALTH.json looks valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
