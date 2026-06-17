"""WF-06 — Multi-Tenant API Key System.

Middleware: checks X-EVEZ-API-KEY on protected routes.
Tiers:      free (100 req/day) | mcp_access (10k req/day) | membership (unlimited)

Routes:
  POST /api/keys/create   (admin)
  GET  /api/keys/validate (middleware helper)
  POST /api/keys/revoke   (admin)
"""
import os, json, time, secrets, logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/keys", tags=["api_keys"])
log = logging.getLogger("api_keys")

DATA_DIR   = Path(os.environ.get("OG_DATA_DIR", Path.home() / "og_data"))
KEYS_FILE  = DATA_DIR / "api_keys.jsonl"

RATE_LIMITS = {
    "free":       100,
    "mcp_access": 10_000,
    "membership": 999_999_999,  # unlimited
}

ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")


def _load_keys() -> dict:
    if not KEYS_FILE.exists(): return {}
    keys = {}
    with KEYS_FILE.open() as f:
        for line in f:
            try:
                rec = json.loads(line)
                keys[rec["key"]] = rec
            except: pass
    return keys


def create_key(email: str, key: str, tier: str = "mcp_access") -> dict:
    KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    rec = {"key": key, "email": email, "tier": tier,
           "usage_count": 0, "revoked": False, "created": time.time()}
    with KEYS_FILE.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def validate_key(key: str) -> dict:
    keys = _load_keys()
    if key not in keys:
        return {"valid": False, "reason": "unknown_key"}
    rec = keys[key]
    if rec.get("revoked"):
        return {"valid": False, "reason": "revoked"}
    tier   = rec.get("tier", "free")
    limit  = RATE_LIMITS.get(tier, 100)
    usage  = rec.get("usage_count", 0)
    if usage >= limit:
        return {"valid": False, "reason": "rate_limit", "tier": tier}
    return {"valid": True, "tier": tier, "email": rec.get("email"),
            "usage_count": usage, "limit": limit}


class KeyCreateRequest(BaseModel):
    email: str
    tier:  Optional[str] = "mcp_access"
    admin_secret: str


class KeyRevokeRequest(BaseModel):
    key: str
    admin_secret: str


@router.post("/create")
def api_key_create(req: KeyCreateRequest):
    if ADMIN_SECRET and req.admin_secret != ADMIN_SECRET:
        raise HTTPException(403, "invalid admin secret")
    new_key = "evez_" + secrets.token_urlsafe(32)
    rec = create_key(email=req.email, key=new_key, tier=req.tier)
    return {"key": new_key, "tier": rec["tier"], "email": rec["email"]}


@router.get("/validate")
def api_key_validate(x_evez_api_key: str = Header(..., alias="X-EVEZ-API-KEY")):
    result = validate_key(x_evez_api_key)
    if not result["valid"]:
        raise HTTPException(403, result.get("reason", "invalid key"))
    return result


@router.post("/revoke")
def api_key_revoke(req: KeyRevokeRequest):
    if ADMIN_SECRET and req.admin_secret != ADMIN_SECRET:
        raise HTTPException(403, "invalid admin secret")
    keys = _load_keys()
    if req.key not in keys:
        raise HTTPException(404, "key not found")
    KEYS_FILE.write_text(
        "\n".join(
            json.dumps({**rec, "revoked": True} if rec["key"] == req.key else rec)
            for rec in keys.values()
        ) + "\n"
    )
    return {"revoked": True, "key": req.key}


@router.get("/list")
def api_key_list(admin_secret: str = ""):
    if ADMIN_SECRET and admin_secret != ADMIN_SECRET:
        raise HTTPException(403, "invalid admin secret")
    keys = _load_keys()
    return {"count": len(keys),
            "keys": [{"key": k[:12]+"...", "tier": v.get("tier"),
                      "email": v.get("email"), "revoked": v.get("revoked")}
                     for k, v in keys.items()]}
