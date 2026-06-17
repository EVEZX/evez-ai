import os
from typing import Any, Dict
import httpx
from fastapi import HTTPException

EVEZ_OS_BASE_URL = os.getenv("EVEZ_OS_BASE_URL", "http://127.0.0.1:8000")


async def post_isolation_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{EVEZ_OS_BASE_URL}/api/telemetry/isolation"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=5.0)
            resp.raise_for_status()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"EVEZ-OS unreachable: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"EVEZ-OS error: {exc.response.text}",
            )
    return resp.json()
