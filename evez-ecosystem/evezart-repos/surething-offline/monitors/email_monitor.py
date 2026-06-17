"""
SureThing Offline — IMAP Email Monitor
"""
from __future__ import annotations
import email, email.header, os
from typing import Optional

IMAP_ENABLED = os.getenv("IMAP_ENABLED","false").lower()=="true"
IMAP_HOST = os.getenv("IMAP_HOST","imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT","993"))
IMAP_USER = os.getenv("IMAP_USER","")
IMAP_PASS = os.getenv("IMAP_PASS","")
IMAP_POLL_INTERVAL = int(os.getenv("IMAP_POLL_INTERVAL","60"))
_last_uid: Optional[int] = None

def _decode(h):
    parts = email.header.decode_header(h)
    return "".join(p.decode(e or "utf-8",errors="replace") if isinstance(p,bytes) else p for p,e in parts)

def fetch_new_emails(since_uid=None):
    if not IMAP_ENABLED: return []
    try:
        import imapclient
        s = imapclient.IMAPClient(IMAP_HOST, port=IMAP_PORT, ssl=True)
        s.login(IMAP_USER, IMAP_PASS); s.select_folder("INBOX", readonly=True)
        if since_uid: uids = s.search([b"UID", f"{since_uid+1}:*".encode()])
        else: all_uids = s.search(["ALL"]); uids = all_uids[-10:] if len(all_uids)>10 else all_uids
        emails = []
        for uid in uids:
            try:
                msg = email.message_from_bytes(s.fetch([uid],["RFC822"])[uid][b"RFC822"])
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type()=="text/plain": body=part.get_payload(decode=True).decode("utf-8",errors="replace"); break
                else: body = msg.get_payload(decode=True).decode("utf-8",errors="replace")
                emails.append({"uid":uid,"subject":_decode(msg.get("Subject","")),"from":_decode(msg.get("From","")),
                               "to":_decode(msg.get("To","")),"date":msg.get("Date",""),"body_preview":body[:500],
                               "message_id":msg.get("Message-ID","")})
            except: pass
        s.logout(); return emails
    except: return []

def poll_once():
    global _last_uid
    from spine.ledger import emit
    emails = fetch_new_emails(since_uid=_last_uid)
    for em in emails:
        emit("observation",{"uid":em["uid"],"from":em["from"],"subject":em["subject"],"preview":em["body_preview"]},
             operator_lane="documentary", subject=f"email:{em.get('message_id',em['uid'])}", tags=["email"])
        if em["uid"] and (not _last_uid or em["uid"]>_last_uid): _last_uid=em["uid"]
    return emails

def start_monitor(scheduler):
    if not IMAP_ENABLED: return
    scheduler.add_job(poll_once,"interval",seconds=IMAP_POLL_INTERVAL,id="imap_monitor",replace_existing=True)
