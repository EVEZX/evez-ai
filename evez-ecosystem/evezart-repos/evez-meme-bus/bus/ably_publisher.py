"""
bus/ably_publisher.py — evez-meme-bus
Publishes meme events to Ably channel 'evez-ops'.
Resolves: evez-meme-bus#1 Phase 2

Env vars:
  ABLY_API_KEY  — your Ably API key (required for live publish)
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger("ably_publisher")

ABLY_KEY = os.environ.get("ABLY_API_KEY", "")
CHANNEL = "evez-ops"


def publish(event_id: str, meme_hash: str, guard_verdict: str, extra: Optional[dict] = None):
    """
    Publish meme event to Ably evez-ops channel.
    Falls back to HTTP REST if ably-python SDK unavailable.
    """
    payload = {
        "event_id": event_id,
        "meme_hash": meme_hash,
        "guard_verdict": guard_verdict,
        "ts": datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    }
    if not ABLY_KEY:
        log.warning("[ably] ABLY_API_KEY not set — skipping publish.")
        return
    try:
        import ably  # type: ignore
        client = ably.AblyRest(ABLY_KEY)
        channel = client.channels.get(CHANNEL)
        channel.publish("meme_event", payload)
        log.info(f"[ably] Published event_id={event_id} verdict={guard_verdict}")
    except ImportError:
        _publish_http(payload)
    except Exception as e:
        log.error(f"[ably] Publish error: {e}")


def _publish_http(payload: dict):
    """Fallback: Ably REST HTTP publish without SDK."""
    import base64
    import urllib.request
    import urllib.error
    key_parts = ABLY_KEY.split(":")
    if len(key_parts) < 2:
        log.error("[ably_http] Invalid ABLY_API_KEY format")
        return
    token = base64.b64encode(ABLY_KEY.encode()).decode()
    url = f"https://rest.ably.io/channels/{CHANNEL}/messages"
    data = json.dumps({"name": "meme_event", "data": json.dumps(payload)}).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Basic {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            log.info(f"[ably_http] Published {resp.status}")
    except Exception as e:
        log.error(f"[ably_http] Error: {e}")
