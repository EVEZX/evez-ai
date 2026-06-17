#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re
import urllib.request
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "REGISTRY_SOURCES.json"
REGISTRY_PATH = ROOT / "PLUGIN_REGISTRY.json"


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=15) as response:
        return response.read().decode("utf-8")


def raw_manifest_url(repo: str, branch: str, manifest_path: str) -> str:
    owner, name = repo.split("/", 1)
    return f"https://raw.githubusercontent.com/{owner}/{name}/{branch}/{manifest_path}"


def extract_scalar(content: str, key: str) -> str | None:
    pattern = rf"^{re.escape(key)}:\s*(.+)$"
    match = re.search(pattern, content, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_block_items(content: str, key: str) -> list[str]:
    pattern = rf"^{re.escape(key)}:\s*$([\s\S]*?)(?=^[A-Za-z_][A-Za-z0-9_]*:\s*$|\Z)"
    match = re.search(pattern, content, flags=re.MULTILINE)
    if not match:
        return []
    block = match.group(1)
    items = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def extract_runtime_value(content: str, key: str) -> str | None:
    pattern = rf"^runtime:\s*$([\s\S]*?)(?=^[A-Za-z_][A-Za-z0-9_]*:\s*$|\Z)"
    match = re.search(pattern, content, flags=re.MULTILINE)
    if not match:
        return None
    block = match.group(1)
    submatch = re.search(rf"^\s+{re.escape(key)}:\s*(.+)$", block, flags=re.MULTILINE)
    return submatch.group(1).strip() if submatch else None


def parse_manifest(content: str) -> dict[str, Any]:
    plugin_id = extract_scalar(content, "id") or "unknown"
    base_url = extract_runtime_value(content, "base_url") or ""
    health_endpoint = extract_runtime_value(content, "health_endpoint") or ""
    skills_endpoint = extract_runtime_value(content, "skills_endpoint") or ""
    capabilities = extract_block_items(content, "capabilities")
    fire_events = extract_block_items(content, "fire_events")
    dependencies = extract_block_items(content, "dependencies")
    version = extract_scalar(content, "version") or "0.0.0"
    return {
        "id": plugin_id,
        "name": extract_scalar(content, "name") or plugin_id,
        "version": version,
        "schema": int((extract_scalar(content, "schema") or "2").strip()),
        "base_url": base_url,
        "health_endpoint": f"{base_url}{health_endpoint}" if base_url and health_endpoint.startswith("/") else (health_endpoint or base_url),
        "skills_endpoint": f"{base_url}{skills_endpoint}" if base_url and skills_endpoint.startswith("/") else (skills_endpoint or base_url),
        "capabilities": capabilities,
        "fire_events": fire_events,
        "dependencies": dependencies,
    }


def main() -> int:
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    plugins = []
    for source in sources.get("sources", []):
        repo = source["repo"]
        branch = source.get("branch", "main")
        manifest_path = source.get("manifest_path", "SKILL.md")
        url = raw_manifest_url(repo, branch, manifest_path)
        try:
            content = fetch_text(url)
            parsed = parse_manifest(content)
            parsed["repo"] = repo
            parsed["manifest_path"] = manifest_path
            parsed["status"] = "synced"
            plugins.append(parsed)
        except Exception as exc:
            plugins.append({
                "id": repo.split("/", 1)[1],
                "repo": repo,
                "manifest_path": manifest_path,
                "health_endpoint": "",
                "skills_endpoint": "",
                "status": f"sync_error: {exc}",
            })

    registry = {
        "schema": 1,
        "ecosystem": "evez",
        "updated_at": "2026-03-19",
        "plugins": plugins,
    }
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    print(f"Synced {len(plugins)} plugins into {REGISTRY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
