"""
monitor/health.py — moltbot-live
Stream health monitor. Checks stream status every 60s.
Emails rubikspubes69@gmail.com on offline/recovery events.
Resolves: moltbot-live#1 Phase 1

Usage:
  python -m monitor.health          # one-shot check
  python -m monitor.health --watch  # continuous 60s poll

Env vars:
  STREAM_URL      — URL to GET-check (returns non-200 = offline)
  STREAM_CHECK_INTERVAL  — seconds between checks (default 60)
  GMAIL_USER, GMAIL_PASS, NOTIFY_EMAIL
"""

import os
import sys
import time
import smtplib
import argparse
import logging
import urllib.request
from datetime import datetime, timezone
from email.mime.text import MIMEText

log = logging.getLogger("moltbot.health")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

STREAM_URL     = os.environ.get("STREAM_URL", "")
INTERVAL       = int(os.environ.get("STREAM_CHECK_INTERVAL", "60"))
NOTIFY_EMAIL   = os.environ.get("NOTIFY_EMAIL", "rubikspubes69@gmail.com")
GMAIL_USER     = os.environ.get("GMAIL_USER", "")
GMAIL_PASS     = os.environ.get("GMAIL_PASS", "")


def is_online() -> bool:
    if not STREAM_URL:
        return True  # no URL configured — assume local process is running
    try:
        with urllib.request.urlopen(STREAM_URL, timeout=10) as r:
            return r.status < 400
    except Exception:
        return False


def send_email(subject: str, body: str):
    if not GMAIL_USER or not GMAIL_PASS:
        log.warning(f"[health] EMAIL SKIP: {subject}")
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"]    = GMAIL_USER
        msg["To"]      = NOTIFY_EMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
        log.info(f"[health] Email sent: {subject}")
    except Exception as e:
        log.error(f"[health] Email error: {e}")


def watch():
    last_state   = True  # assume online at start
    offline_since: float = 0.0
    log.info(f"[health] Watching stream every {INTERVAL}s...")
    while True:
        online = is_online()
        ts = datetime.now(timezone.utc).isoformat()
        if last_state and not online:
            offline_since = time.time()
            log.warning("[health] Stream OFFLINE")
            send_email(
                "[MOLTBOT OFFLINE] Stream went offline",
                f"MoltBot stream detected OFFLINE at {ts}\nURL checked: {STREAM_URL or '(local process)'}\n"
            )
        elif not last_state and online:
            downtime = int(time.time() - offline_since)
            log.info(f"[health] Stream RECOVERED (downtime {downtime}s)")
            send_email(
                "[MOLTBOT RECOVERED] Stream is back online",
                f"MoltBot stream RECOVERED at {ts}\nDowntime: {downtime}s\nURL: {STREAM_URL or '(local process)'}\n"
            )
        last_state = online
        time.sleep(INTERVAL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()
    if args.watch:
        watch()
    else:
        status = "ONLINE" if is_online() else "OFFLINE"
        print(f"[health] Stream status: {status}")
