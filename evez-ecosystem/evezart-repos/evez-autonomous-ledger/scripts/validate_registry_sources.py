#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "REGISTRY_SOURCES.json"
REQUIRED_KEYS = {"repo", "branch", "manifest_path"}


def main() -> int:
    if not SOURCES_PATH.exists():
        print("Missing REGISTRY_SOURCES.json")
        return 1

    data = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        print("REGISTRY_SOURCES.json schema must equal 1")
        return 1

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        print("REGISTRY_SOURCES.json must contain a non-empty sources list")
        return 1

    seen = set()
    failures = []
    for source in sources:
        if not isinstance(source, dict):
            failures.append("source entry is not an object")
            continue
        missing = REQUIRED_KEYS - set(source.keys())
        if missing:
            failures.append(f"source missing keys: {sorted(missing)}")
            continue
        repo = source["repo"]
        if repo in seen:
            failures.append(f"duplicate repo: {repo}")
        seen.add(repo)

    if failures:
        print("Registry source validation failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("REGISTRY_SOURCES.json looks valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
