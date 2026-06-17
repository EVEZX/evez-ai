from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Header, HTTPException, Request
from slowapi.util import get_remote_address

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
MANIFEST_PATH = BASE_DIR / ".roo" / "archonic-manifest.json"

API_KEY_SALT = os.getenv("API_KEY_SALT")
APP_ENV = os.getenv("APP_ENV", "development").lower()
if not API_KEY_SALT:
    if APP_ENV in ("prod", "production"):
        raise RuntimeError("API_KEY_SALT is required in production environment")
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("Either API_KEY_SALT or SECRET_KEY must be set for local dev")
    API_KEY_SALT = hashlib.pbkdf2_hmac(
        "sha256", secret.encode(), b"evez-api-key-salt", 100000
    ).hex()


def fingerprint_api_key(api_key: str) -> str:
    return hmac.new(
        API_KEY_SALT.encode("utf-8"), api_key.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def load_tier_map() -> dict[str, int]:
    if not MANIFEST_PATH.exists():
        return {}
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    api_keys = manifest.get("api_keys", {})
    return {key: int(value.get("tier", 0)) for key, value in api_keys.items()}


TIER_MAP = load_tier_map()


def rate_limit_key(request: Request) -> str:
    return request.headers.get("X-API-Key") or get_remote_address(request)


def verify_api_key(
    request: Request,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> int:
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "Missing API key",
            },
        )
    tier = TIER_MAP.get(x_api_key)
    if tier is None:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "Invalid API key",
            },
        )
    request.state.api_key = x_api_key
    request.state.tier = tier
    return tier


def rate_limit_for_key(key: str) -> str:
    tier = TIER_MAP.get(key, 0)
    if tier <= 0:
        return "10/minute"
    if tier >= 3:
        return "100/minute"
    return "50/minute"
