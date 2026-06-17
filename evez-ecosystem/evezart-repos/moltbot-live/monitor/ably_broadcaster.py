"""
monitor/ably_broadcaster.py — moltbot-live
Publishes cognitive cycle completions to Ably 'evez-ops' channel.
Resolves: moltbot-live#1 Phase 2

Env vars:
  ABLY_API_KEY
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger("moltbot.broadcaster")
ABLY_KEY = os.environ.get("ABLY_API_KEY", "")
CHANNEL  = "evez-ops"


def broadcast_cycle(
    cycle_id: str,
    action_taken: str,
    broadcast_content: str,
    viewer_count: int = 0,
    extra: Optional[dict] = None,
):
    """
    Call at the end of every cognitive cycle to publish to evez-ops.
    """
    payload = {
        "cycle_id":          cycle_id,
        "action_taken":      action_taken,
        "broadcast_content": broadcast_content,
        "viewer_count":      viewer_count,
        "ts":                datetime.now(timezone.utc).isoformat(),
        **(extra or {}),
    }
    if not ABLY_KEY:
        log.warning(f"[broadcaster] ABLY_API_KEY not set. Cycle: {cycle_id}")
        print(f"[broadcaster] Cycle event: {json.dumps(payload)}")
        return
    try:
        import ably  # type: ignore
        client = ably.AblyRest(ABLY_KEY)
        client.channels.get(CHANNEL).publish("cognitive_cycle", payload)
        log.info(f"[broadcaster] Published cycle {cycle_id} to {CHANNEL}")
    except ImportError:
        _http_publish(payload)
    except Exception as e:
        log.error(f"[broadcaster] Error: {e}")


def _http_publish(payload: dict):
    import base64, urllib.request
    token = base64.b64encode(ABLY_KEY.encode()).decode()
    url   = f"https://rest.ably.io/channels/{CHANNEL}/messages"
    data  = json.dumps({"name": "cognitive_cycle", "data": json.dumps(payload)}).encode()
    req   = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Basic {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            log.info(f"[broadcaster_http] {r.status}")
    except Exception as e:
        log.error(f"[broadcaster_http] {e}")
