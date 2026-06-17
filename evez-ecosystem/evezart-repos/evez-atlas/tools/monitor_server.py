#!/usr/bin/env python3
"""Local monitor server for hermetic console (read-only)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, List

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

BASE_DIR = Path(__file__).resolve().parents[1]
AUDIT_LOG_PATH = BASE_DIR / "src" / "memory" / "audit.jsonl"
HTML_PATH = BASE_DIR / "tools" / "hermetic_engine.html"

app = FastAPI()


@app.get("/")
def serve_console() -> FileResponse:
    return FileResponse(HTML_PATH)


@app.get("/audit-tail")
def audit_tail(n: int = Query(200, ge=1, le=1000)) -> JSONResponse:
    if not AUDIT_LOG_PATH.exists():
        return JSONResponse(content=[])
    lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()
    tail = lines[-n:]
    parsed: List[Any] = []
    for line in tail:
        if not line.strip():
            continue
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return JSONResponse(content=parsed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    uvicorn.run(app, host="0.0.0.0", port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
