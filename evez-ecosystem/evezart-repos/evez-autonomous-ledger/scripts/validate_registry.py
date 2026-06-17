#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys

REQUIRED_PLUGIN_KEYS = {
    "id",
    "repo",
    "manifest_path",
    "health_endpoint",
    "skills_endpoint",
    "status",
}


def main() -> int:
    path = pathlib.Path("PLUGIN_REGISTRY.json")
    if not path.exists():
        print("Missing PLUGIN_REGISTRY.json")
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON: {exc}")
        return 1

    if data.get("schema") != 1:
        print("PLUGIN_REGISTRY.json schema must equal 1")
        return 1

    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        print("PLUGIN_REGISTRY.json must contain a non-empty plugins list")
        return 1

    seen_ids: set[str] = set()
    failures: list[str] = []
    for plugin in plugins:
        if not isinstance(plugin, dict):
            failures.append("plugin entry is not an object")
            continue
        missing = REQUIRED_PLUGIN_KEYS - set(plugin.keys())
        if missing:
            failures.append(f"plugin {plugin.get('id', '<unknown>')} missing keys: {sorted(missing)}")
        plugin_id = plugin.get("id")
        if plugin_id in seen_ids:
            failures.append(f"duplicate plugin id: {plugin_id}")
        if isinstance(plugin_id, str):
            seen_ids.add(plugin_id)

    if failures:
        print("Registry validation failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("PLUGIN_REGISTRY.json looks valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
