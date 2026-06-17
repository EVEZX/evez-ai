#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "PLUGIN_REGISTRY.json"
HEALTH_PATH = ROOT / "PLUGIN_HEALTH.json"


def probe(url: str) -> dict[str, Any]:
    if not url:
        return {"ok": False, "status_code": 0, "error": "missing_url"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "evez-health-probe/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read(512).decode("utf-8", errors="replace")
            return {
                "ok": 200 <= response.status < 300,
                "status_code": response.status,
                "body_preview": body,
            }
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status_code": exc.code, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "status_code": 0, "error": str(exc)}


def main() -> int:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    checks = []
    for plugin in registry.get("plugins", []):
        plugin_id = plugin.get("id", "unknown")
        health_url = plugin.get("health_endpoint", "")
        skills_url = plugin.get("skills_endpoint", "")
        health_result = probe(health_url)
        skills_result = probe(skills_url)
        checks.append({
            "id": plugin_id,
            "repo": plugin.get("repo", ""),
            "health_endpoint": health_url,
            "skills_endpoint": skills_url,
            "health": health_result,
            "skills": skills_result,
            "overall_status": "ok" if health_result.get("ok") or skills_result.get("ok") else "unreachable",
        })

    payload = {
        "schema": 1,
        "ecosystem": "evez",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
    HEALTH_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote health checks for {len(checks)} plugins to {HEALTH_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
