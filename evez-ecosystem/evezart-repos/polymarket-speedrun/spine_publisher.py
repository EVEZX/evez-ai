"""
spine_publisher.py — polymarket-speedrun
Publishes trade events to Ably 'evez-stripe' channel.
Resolves: polymarket-speedrun#1 Phase 2

Env vars:
  ABLY_API_KEY  — Ably API key
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger("spine_publisher")
ABLY_KEY = os.environ.get("ABLY_API_KEY", "")
CHANNEL  = "evez-stripe"


def publish_trade(
    market: str,
    outcome: str,
    amount_usd: float,
    result: str,
    pnl_running: float,
    extra: Optional[dict] = None,
):
    payload = {
        "market":      market,
        "outcome":     outcome,
        "amount":      amount_usd,
        "result":      result,
        "pnl_running": pnl_running,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    }
    if not ABLY_KEY:
        log.warning("[spine] ABLY_API_KEY not set — logging trade locally only.")
        print(f"[spine] Trade event: {json.dumps(payload)}")
        return
    try:
        import ably  # type: ignore
        client = ably.AblyRest(ABLY_KEY)
        client.channels.get(CHANNEL).publish("trade", payload)
        log.info(f"[spine] Published to {CHANNEL}: {result} pnl_running={pnl_running:+.4f}")
    except ImportError:
        _http_publish(payload)
    except Exception as e:
        log.error(f"[spine] Publish error: {e}")


def _http_publish(payload: dict):
    import base64, urllib.request
    token = base64.b64encode(ABLY_KEY.encode()).decode()
    url  = f"https://rest.ably.io/channels/{CHANNEL}/messages"
    data = json.dumps({"name": "trade", "data": json.dumps(payload)}).encode()
    req  = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Basic {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            log.info(f"[spine_http] {r.status}")
    except Exception as e:
        log.error(f"[spine_http] {e}")
