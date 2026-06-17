"""
bus/guard_reporter.py — evez-meme-bus
Emails rubikspubes69@gmail.com when constitutional guard triggers REJECT.
Resolves: evez-meme-bus#1 Phase 3

Env vars:
  GMAIL_USER   — sending Gmail address
  GMAIL_PASS   — Gmail app password
  NOTIFY_EMAIL — override recipient (default: rubikspubes69@gmail.com)
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from datetime import datetime, timezone

log = logging.getLogger("guard_reporter")

NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "rubikspubes69@gmail.com")
GMAIL_USER   = os.environ.get("GMAIL_USER", "")
GMAIL_PASS   = os.environ.get("GMAIL_PASS", "")


def report_violation(event_id: str, event_details: dict, reason: str):
    """
    Call this when constitutional guard returns REJECT.
    Sends an email with event_id, reason, and full event_details.
    """
    ts = datetime.now(timezone.utc).isoformat()
    subject = f"[MEME-BUS] Constitutional REJECT: {event_id}"
    body = (
        f"Constitutional guard triggered REJECT at {ts}\n\n"
        f"Event ID : {event_id}\n"
        f"Reason   : {reason}\n"
        f"Details  : {event_details}\n"
    )
    _send(subject, body)


def _send(subject: str, body: str):
    if not GMAIL_USER or not GMAIL_PASS:
        log.warning(f"[guard_reporter] EMAIL SKIP (no creds): {subject}")
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"]    = GMAIL_USER
        msg["To"]      = NOTIFY_EMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
        log.info(f"[guard_reporter] Email sent: {subject}")
    except Exception as e:
        log.error(f"[guard_reporter] Email error: {e}")
