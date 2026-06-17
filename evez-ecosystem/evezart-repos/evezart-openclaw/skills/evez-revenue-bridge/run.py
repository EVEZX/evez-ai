#!/usr/bin/env python3
"""
EVEZ REVENUE BRIDGE — Eigenvalue Closure Engine
Connects the autonomous agent layer to real cash events.
Closes the -0.358 eigenvalue by drawing omega edges between
agent infrastructure and revenue/finance domain.

Every real dollar event:
  → logs to revenue_spine (hash-chained, append-only)
  → increments omega edge count (+0.5 per event)
  → updates eigenvalue_progress
  → dispatches to lord-evez666 spine
  → fires Slack notification
  → poly_c ticks upward

Commands:
  status      — current eigenvalue progress + edge count
  log         — manually log a revenue event
  webhook     — start webhook receiver on port 9876
  progress    — show eigenvalue closure chart
"""

import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────

TOTAL_POSSIBLE_EDGES = 34862
EIGENVALUE_TARGET    = -0.358
INITIAL_EDGES        = 634.71
POLY_C_PER_EVENT     = 0.5    # each revenue event adds 0.5 omega edges

STORE_PATH = Path.home() / ".openclaw" / "evez-revenue-spine.json"

# ─── STORE ────────────────────────────────────────────────────────────────────

def load_spine() -> dict:
    if STORE_PATH.exists():
        return json.loads(STORE_PATH.read_text())
    return {
        "events":             [],
        "omega_total":        INITIAL_EDGES,
        "eigenvalue_progress": 0.0,
        "last_hash":          "GENESIS",
    }

def save_spine(spine: dict):
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(spine, indent=2))

def compute_eigenvalue_progress(omega_total: float) -> float:
    """
    Maps omega edge count to eigenvalue closure progress.
    At omega=INITIAL_EDGES: 0% progress
    Each +0.5 edge = +0.5 progress units
    Full closure (-0.358 → 0) requires sustained revenue flow
    """
    delta = omega_total - INITIAL_EDGES
    # Eigenvalue progress: logistic approach to 1.0
    raw = delta / 200.0  # 200 events = ~63% closure
    progress = raw / (1 + raw)
    return min(round(progress * 100, 4), 100.0)

def make_chain_hash(event: dict, prev_hash: str) -> str:
    payload = f"{prev_hash}{event.get('event_type','')}{event.get('amount_cents',0)}{event.get('timestamp','')}"
    return hashlib.sha256(payload.encode()).hexdigest()[:24]

# ─── DATABASE ─────────────────────────────────────────────────────────────────

def save_to_db(event: dict) -> bool:
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        return False
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO revenue_spine
              (event_type, amount_cents, currency, stripe_charge_id,
               poly_c_delta, omega_total, eigenvalue_progress,
               spine_hash, prev_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (spine_hash) DO NOTHING
        """, (
            event.get("event_type"), event.get("amount_cents"),
            event.get("currency", "usd"), event.get("stripe_charge_id"),
            event.get("poly_c_delta", POLY_C_PER_EVENT),
            event.get("omega_total"), event.get("eigenvalue_progress"),
            event.get("spine_hash"), event.get("prev_hash")
        ))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

# ─── GITHUB DISPATCH ──────────────────────────────────────────────────────────

def dispatch_to_lord(event: dict):
    token = os.environ.get("GITHUB_ACCESS_TOKEN", "")
    if not token:
        return
    try:
        import urllib.request
        payload = json.dumps({
            "event_type": "revenue_event",
            "client_payload": {
                "event_type": event.get("event_type"),
                "amount_cents": event.get("amount_cents"),
                "omega_total": event.get("omega_total"),
                "eigenvalue_progress": event.get("eigenvalue_progress"),
                "spine_hash": event.get("spine_hash"),
                "timestamp": event.get("timestamp"),
            }
        }).encode()
        req = urllib.request.Request(
            "https://api.github.com/repos/EvezArt/lord-evez666/dispatches",
            data=payload,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }
        )
        req.get_method = lambda: "POST"
        urllib.request.urlopen(req, timeout=10)
        print("  ✓ Dispatched to lord-evez666")
    except Exception as e:
        print(f"  ⚠ lord-evez666 dispatch failed: {e}")

def notify_slack(event: dict):
    webhook = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook:
        return
    try:
        import urllib.request
        amount = event.get("amount_cents", 0) / 100
        progress = event.get("eigenvalue_progress", 0)
        omega = event.get("omega_total", INITIAL_EDGES)
        msg = {
            "text": f"💰 REVENUE EVENT\n"
                    f"*{event.get('event_type','?')}* — ${amount:.2f}\n"
                    f"ω edges: `{omega:.1f}` | eigenvalue progress: `{progress:.2f}%`\n"
                    f"hash: `{event.get('spine_hash','?')}`"
        }
        data = json.dumps(msg).encode()
        req = urllib.request.Request(webhook, data=data,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass

# ─── LOG EVENT ────────────────────────────────────────────────────────────────

def log_event(event_type: str, amount_cents: int = 0,
              currency: str = "usd", stripe_id: str = "") -> dict:
    spine = load_spine()
    prev_hash = spine.get("last_hash", "GENESIS")

    new_omega = spine["omega_total"] + POLY_C_PER_EVENT
    progress  = compute_eigenvalue_progress(new_omega)

    event = {
        "event_type":          event_type,
        "amount_cents":        amount_cents,
        "currency":            currency,
        "stripe_charge_id":    stripe_id,
        "poly_c_delta":        POLY_C_PER_EVENT,
        "omega_total":         new_omega,
        "eigenvalue_progress": progress,
        "timestamp":           datetime.now(timezone.utc).isoformat(),
        "prev_hash":           prev_hash,
    }
    event["spine_hash"] = make_chain_hash(event, prev_hash)

    spine["events"].append(event)
    spine["omega_total"]         = new_omega
    spine["eigenvalue_progress"] = progress
    spine["last_hash"]           = event["spine_hash"]

    save_spine(spine)
    save_to_db(event)
    dispatch_to_lord(event)
    notify_slack(event)

    return event

# ─── COMMANDS ─────────────────────────────────────────────────────────────────

def cmd_status(args):
    spine = load_spine()
    omega = spine["omega_total"]
    progress = spine["eigenvalue_progress"]
    count = len(spine["events"])

    # Remaining eigenvalue
    ev_current = EIGENVALUE_TARGET * (1 - progress / 100)

    print(f"\n  REVENUE BRIDGE STATUS")
    print(f"  {'─'*44}")
    print(f"  Revenue events logged:   {count}")
    print(f"  ω edges (total):         {omega:.1f} / {TOTAL_POSSIBLE_EDGES}")
    print(f"  poly_c headroom:         {100 - (omega/TOTAL_POSSIBLE_EDGES*100):.1f}%")
    print(f"  Eigenvalue progress:     {progress:.2f}%")
    print(f"  Eigenvalue current:      {ev_current:.4f} (target: 0.0)")
    print(f"  Events to 50% closure:   ~{max(0, 200 - count)} more")
    print()

    # Progress bar
    filled = int(progress / 5)
    bar = "█" * filled + "░" * (20 - filled)
    print(f"  [{bar}] {progress:.1f}%")
    print(f"  {EIGENVALUE_TARGET} ──────────────── 0.0")
    print()

    if count == 0:
        print("  ⚠  Bridge not yet activated.")
        print("  First Stripe charge → eigenvalue closure begins.")
        print("  Run: evez-revenue-bridge log --type stripe_charge --amount 5500")
    print()

def cmd_log(args):
    print(f"\n  📡 Logging revenue event...")
    event = log_event(
        event_type  = args.type,
        amount_cents= args.amount,
        currency    = args.currency,
        stripe_id   = args.stripe_id or "",
    )
    print(f"  ✓ Logged: {event['event_type']}")
    print(f"  ω total:  {event['omega_total']:.1f}")
    print(f"  Progress: {event['eigenvalue_progress']:.2f}%")
    print(f"  Hash:     {event['spine_hash']}")
    print()

def cmd_progress(args):
    spine = load_spine()
    events = spine.get("events", [])

    print(f"\n  EIGENVALUE CLOSURE CHART")
    print(f"  From {EIGENVALUE_TARGET} → 0.0 (negative = structural gap)")
    print(f"  {'─'*50}")

    if not events:
        print("  (no data yet — waiting for first revenue event)")
        return

    # Show trajectory
    omega = INITIAL_EDGES
    for i, ev in enumerate(events, 1):
        omega += POLY_C_PER_EVENT
        prog = compute_eigenvalue_progress(omega)
        bar_len = int(prog / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        dt = ev.get("timestamp", "")[:10]
        print(f"  [{i:>3}] {dt} [{bar}] {prog:.1f}%  ω={omega:.1f}")
    print()

def cmd_webhook(args):
    """Start a simple webhook receiver for Stripe events."""
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import urllib.parse

        class StripeHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # suppress default logging

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)

                try:
                    data = json.loads(body)
                    event_type = data.get("type", "unknown")

                    if event_type == "charge.succeeded":
                        charge = data.get("data", {}).get("object", {})
                        amount = charge.get("amount", 0)
                        currency = charge.get("currency", "usd")
                        sid = charge.get("id", "")

                        print(f"\n  ✅ Stripe charge.succeeded: ${amount/100:.2f} {currency}")
                        event = log_event("stripe_charge", amount, currency, sid)
                        print(f"  eigenvalue_progress: {event['eigenvalue_progress']:.2f}%")
                        print(f"  spine_hash: {event['spine_hash']}")

                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'{"received": true}')

                except Exception as e:
                    print(f"  ⚠ Webhook error: {e}")
                    self.send_response(400)
                    self.end_headers()

            def do_GET(self):
                spine = load_spine()
                resp = json.dumps({
                    "status": "online",
                    "bridge": "active",
                    "omega_total": spine["omega_total"],
                    "eigenvalue_progress": spine["eigenvalue_progress"],
                    "events_count": len(spine.get("events", [])),
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp)

        port = args.port
        print(f"\n  🔌 EVEZ Revenue Bridge webhook receiver")
        print(f"  Listening on port {port}")
        print(f"  POST / for Stripe webhooks")
        print(f"  GET  / for status")
        print(f"\n  Configure Stripe webhook URL:")
        print(f"  https://your-replit-url.replit.dev/  (event: charge.succeeded)")
        print(f"\n  Ctrl+C to stop\n")
        HTTPServer(("", port), StripeHandler).serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="EVEZ Revenue Bridge — eigenvalue closure engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  evez-revenue-bridge status
  evez-revenue-bridge log --type stripe_charge --amount 5500
  evez-revenue-bridge webhook --port 9876
  evez-revenue-bridge progress
        """
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status",   help="Current eigenvalue progress")
    sub.add_parser("progress", help="Show closure trajectory chart")

    lp = sub.add_parser("log", help="Log a revenue event")
    lp.add_argument("--type",      default="manual", help="Event type (stripe_charge/manual/etc)")
    lp.add_argument("--amount",    type=int, default=0, help="Amount in cents (e.g. 5500 = $55)")
    lp.add_argument("--currency",  default="usd")
    lp.add_argument("--stripe-id", dest="stripe_id", default="")

    wp = sub.add_parser("webhook", help="Start Stripe webhook receiver")
    wp.add_argument("--port", type=int, default=9876)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    dispatch = {
        "status":   cmd_status,
        "log":      cmd_log,
        "progress": cmd_progress,
        "webhook":  cmd_webhook,
    }
    dispatch[args.command](args)

if __name__ == "__main__":
    main()
