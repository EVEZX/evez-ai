#!/usr/bin/env python3
"""
http_client.py — EVEZ-OS shared x402-aware HTTP session
=========================================================
Single import for all outbound HTTP in EVEZ-OS scripts.
Wraps requests.Session with x402 payment intercept.

Usage (drop-in for requests):
    from http_client import session, get, post

    resp = get("https://api.example.com/data")         # auto-pays on 402
    resp = session.post("https://api.example.com/rpc") # same

    # Or use session directly:
    from http_client import session
    resp = session.get(url, headers={...})

x402 behavior:
    - 402 response → parse X-Payment-Required header
    - sign USDC transfer on Base from agent wallet
    - inject X-Payment-Authorization → retry
    - log to workspace/x402_payment_log.jsonl
    - safety caps: $0.10/call max, $5.00/day hard stop
    - low balance alert: < $1.00 USDC

Wallet: 0xFb756fc5Fe01FB982E5d63Db3A8b787B6fDE8692 (Base, USDC)
Key:    /cells/599dc7f9-0b2b-4460-b917-5104fcbb91ef/secrets/agent_wallet_private.json

If key not loaded (unfunded/missing), session falls back to plain requests.Session.
x402 payments are silently skipped until wallet is funded — no crash.
"""

import sys, os
from pathlib import Path

# Add workspace to path so x402_payment_intercept imports cleanly
WORKSPACE = Path("/cells/599dc7f9-0b2b-4460-b917-5104fcbb91ef/workspace")
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

try:
    from x402_payment_intercept import X402Session, check_usdc_balance_base
    session = X402Session()
    _x402_active = True
except Exception as _e:
    import requests
    session = requests.Session()
    _x402_active = False
    import logging
    logging.getLogger("http_client").warning(f"x402 not loaded ({_e}), using plain session")


def get(url: str, **kwargs):
    """x402-aware GET. Auto-pays USDC on 402 and retries."""
    return session.get(url, **kwargs)


def post(url: str, **kwargs):
    """x402-aware POST. Auto-pays USDC on 402 and retries."""
    return session.post(url, **kwargs)


def put(url: str, **kwargs):
    return session.put(url, **kwargs)


def delete(url: str, **kwargs):
    return session.delete(url, **kwargs)


def x402_status() -> dict:
    """Return current x402 wallet status for health checks."""
    if not _x402_active:
        return {"active": False, "reason": "x402 not loaded"}
    try:
        balance = check_usdc_balance_base()
        return {
            "active": True,
            "wallet": session._address,
            "key_loaded": session._account is not None,
            "balance_usd": balance,
            "funded": (balance or 0) > 0,
        }
    except Exception as e:
        return {"active": True, "error": str(e)}


if __name__ == "__main__":
    import json
    print(json.dumps(x402_status(), indent=2))
