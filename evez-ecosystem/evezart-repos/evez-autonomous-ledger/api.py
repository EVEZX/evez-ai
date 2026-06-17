from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "PLUGIN_REGISTRY.json"
SOURCES_PATH = ROOT / "REGISTRY_SOURCES.json"

app = FastAPI(title="evez-plugin-registry", version="0.1.0")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    plugins = registry.get("plugins", []) if isinstance(registry, dict) else []
    return {
        "status": "ok",
        "service": "evez-plugin-registry",
        "time": datetime.now(timezone.utc).isoformat(),
        "plugin_count": len(plugins),
        "registry_present": REGISTRY_PATH.exists(),
        "sources_present": SOURCES_PATH.exists(),
    }


@app.get("/skills")
def skills() -> dict[str, Any]:
    return {
        "id": "evez-plugin-registry",
        "name": "EVEZ Plugin Registry",
        "capabilities": [
            "list_plugins",
            "get_plugin",
            "search_plugins",
            "registry_status",
        ],
    }


@app.get("/plugins")
def list_plugins(q: str = Query(default=""), status: str = Query(default="")) -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    plugins = registry.get("plugins", []) if isinstance(registry, dict) else []
    query = q.lower().strip()
    status_filter = status.lower().strip()

    filtered = []
    for plugin in plugins:
        haystack = json.dumps(plugin, sort_keys=True).lower()
        if query and query not in haystack:
            continue
        if status_filter and str(plugin.get("status", "")).lower() != status_filter:
            continue
        filtered.append(plugin)

    return {
        "count": len(filtered),
        "items": filtered,
    }


@app.get("/plugins/{plugin_id}")
def get_plugin(plugin_id: str) -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    plugins = registry.get("plugins", []) if isinstance(registry, dict) else []
    for plugin in plugins:
        if plugin.get("id") == plugin_id:
            return plugin
    raise HTTPException(status_code=404, detail="plugin not found")


@app.get("/sources")
def sources() -> dict[str, Any]:
    data = load_json(SOURCES_PATH)
    items = data.get("sources", []) if isinstance(data, dict) else []
    return {"count": len(items), "items": items}
