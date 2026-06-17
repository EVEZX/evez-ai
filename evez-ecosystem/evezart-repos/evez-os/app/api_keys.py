"""WF-06 — Multi-Tenant API Key Middleware: tier-based rate limiting"""
import os
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.db import db

RATE_LIMITS = {
    "free":        100,
    "mcp_access":  10_000,
    "membership":  999_999,
    "consulting":  999_999,
}

PROTECTED = ["/api/mcp", "/api/agents", "/api/spawn", "/api/wormhole"]

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not any(request.url.path.startswith(p) for p in PROTECTED):
            return await call_next(request)

        key = request.headers.get("X-EVEZ-API-KEY")
        if not key:
            raise HTTPException(401, detail="Missing X-EVEZ-API-KEY header")

        row = await db.fetchrow(
            "SELECT tier, usage_count, revoked FROM api_keys WHERE key=$1", key
        )
        if not row:
            raise HTTPException(403, detail="Invalid API key")
        if row["revoked"]:
            raise HTTPException(403, detail="API key revoked")

        limit = RATE_LIMITS.get(row["tier"], 100)
        if row["usage_count"] >= limit:
            raise HTTPException(429, detail=f"Rate limit {limit}/day reached for tier '{row['tier']}'")

        await db.execute(
            "UPDATE api_keys SET usage_count = usage_count + 1 WHERE key=$1", key
        )
        request.state.tier = row["tier"]
        return await call_next(request)
