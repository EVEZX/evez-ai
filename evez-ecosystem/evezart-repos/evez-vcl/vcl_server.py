from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="evez-vcl", version="0.3.0")
ARTIFACTS: dict[str, dict[str, Any]] = {}


class RenderRequest(BaseModel):
    manifest_id: str = "default"
    data: dict[str, Any] = {}


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "evez-vcl",
        "time": datetime.now(timezone.utc).isoformat(),
        "artifact_count": len(ARTIFACTS),
    }


@app.get("/skills")
def skills() -> dict[str, Any]:
    return {
        "id": "evez-vcl",
        "name": "Visual Cognition Layer",
        "version": "0.3.0",
        "capabilities": [
            "render_artifact",
            "manifest_load",
            "visual_emit",
            "consciousness_frame",
        ],
    }


@app.get("/manifests")
def manifests() -> dict[str, Any]:
    return {
        "items": [
            {
                "id": "default",
                "name": "Default Visual Cognition Manifest",
                "schema": 1,
                "description": "Minimal VCL fallback manifest for artifact rendering.",
            }
        ]
    }


@app.post("/render")
def render(req: RenderRequest) -> dict[str, Any]:
    artifact_id = str(uuid4())
    artifact = {
        "id": artifact_id,
        "manifest_id": req.manifest_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "rendered",
        "kind": "json_artifact",
        "payload": req.data,
    }
    ARTIFACTS[artifact_id] = artifact
    return artifact


@app.get("/artifacts/{artifact_id}")
def get_artifact(artifact_id: str) -> dict[str, Any]:
    artifact = ARTIFACTS.get(artifact_id)
    if artifact:
        return artifact
    return {
        "id": artifact_id,
        "status": "missing",
        "message": "artifact not found",
    }
