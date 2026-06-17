"""WF-01 — Stripe Fulfillment Engine.

Routes: POST /api/billing/checkout  POST /api/billing/webhook
Env:    STRIPE_SECRET_KEY  STRIPE_WEBHOOK_SECRET
        SENDGRID_API_KEY   EVEZ_FROM_EMAIL
        GROQ_API_KEY (for MCP key generation)
"""
import os, json, hmac, hashlib, time, secrets, logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/billing", tags=["billing"])
log = logging.getLogger("billing")

STRIPE_SECRET_KEY     = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
SENDGRID_API_KEY      = os.environ.get("SENDGRID_API_KEY", "")
EVEZ_FROM_EMAIL       = os.environ.get("EVEZ_FROM_EMAIL", "rubikspubes69@gmail.com")

PRODUCT_MAP = {
    "price_mcp_49":        {"name": "MCP Access",     "type": "mcp_access"},
    "price_membership_29": {"name": "Membership",     "type": "membership"},
    "price_consulting_250":{"name": "Consulting",     "type": "consulting"},
}


def _fire(event: str, data: dict):
    """Emit a FIRE event to n8n."""
    import httpx
    n8n_url = os.environ.get("N8N_FIRE_URL", "")
    if not n8n_url:
        return
    try:
        httpx.post(n8n_url, json={"event": event, "data": data, "ts": time.time()}, timeout=5)
    except Exception as e:
        log.warning(f"FIRE {event} failed: {e}")


def _generate_api_key() -> str:
    return "evez_" + secrets.token_urlsafe(32)


def _send_email(to: str, subject: str, body: str):
    """Send email via SendGrid."""
    if not SENDGRID_API_KEY:
        log.warning("SENDGRID_API_KEY not set — email skipped")
        return
    import httpx
    resp = httpx.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}",
                 "Content-Type": "application/json"},
        json={
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": EVEZ_FROM_EMAIL},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}]
        },
        timeout=10
    )
    if resp.status_code not in (200, 202):
        log.error(f"SendGrid error {resp.status_code}: {resp.text}")


def fulfill(session: dict):
    """Core fulfillment — called on checkout.session.completed."""
    email      = session.get("customer_details", {}).get("email", "")
    price_id   = (session.get("line_items", {}).get("data") or [{}])[0] \
                         .get("price", {}).get("id", "")
    product    = PRODUCT_MAP.get(price_id, {"name": "Purchase", "type": "unknown"})
    api_key    = None

    if product["type"] in ("mcp_access", "membership"):
        api_key = _generate_api_key()
        _store_api_key(email, api_key, product["type"])

    _send_fulfillment_email(email, product, api_key)
    _fire("FIRE_REVENUE_EVENT", {
        "email": email,
        "product": product["name"],
        "price_id": price_id,
        "api_key_issued": bool(api_key)
    })
    log.info(f"Fulfilled {product['name']} for {email}")


def _store_api_key(email: str, key: str, tier: str):
    """Write key to api_keys table (via api_keys module) or flat file fallback."""
    try:
        from app.api_keys import create_key
        create_key(email=email, key=key, tier=tier)
    except Exception:
        from pathlib import Path
        kf = Path.home() / "og_data" / "api_keys.jsonl"
        kf.parent.mkdir(parents=True, exist_ok=True)
        with kf.open("a") as f:
            f.write(json.dumps({"email": email, "key": key, "tier": tier,
                                "ts": time.time()}) + "\n")


def _send_fulfillment_email(email: str, product: dict, api_key):
    if product["type"] == "mcp_access":
        body = f"""Welcome to EVEZ-OS MCP Access!

Your API key: {api_key}

MCP config JSON:
{{
  "mcpServers": {{
    "evez-os": {{
      "url": "https://evez-os.onrender.com",
      "headers": {{"X-EVEZ-API-KEY": "{api_key}"}}
    }}
  }}
}}

Limit: 10,000 req/day.
Dashboard: https://evez.app/dashboard

— EVEZ-OS (Steven Crawford-Maggard / EVEZ666)
"""
    elif product["type"] == "membership":
        body = f"""Welcome to EVEZ Membership!

Your API key (unlimited): {api_key}
Dashboard: https://evez.app/dashboard
Calendly (consulting): https://calendly.com/evez666

— EVEZ-OS
"""
    elif product["type"] == "consulting":
        body = """Thanks for booking an EVEZ consulting session!

Schedule your call: https://calendly.com/evez666
— EVEZ-OS
"""
    else:
        body = f"Thank you for your purchase ({product['name']})! — EVEZ-OS"

    _send_email(email, f"Your EVEZ-OS {product['name']} — Delivered", body)


@router.post("/checkout")
async def create_checkout(request: Request):
    """Create Stripe checkout session."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "Stripe not configured")
    import httpx
    body = await request.json()
    price_id = body.get("price_id", "price_mcp_49")
    mode = "subscription" if price_id == "price_membership_29" else "payment"
    resp = httpx.post(
        "https://api.stripe.com/v1/checkout/sessions",
        auth=(STRIPE_SECRET_KEY, ""),
        data={
            "mode": mode,
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": "1",
            "success_url": "https://evez.app/success?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": "https://evez.app/cancel",
            "expand[]": "line_items",
        },
        timeout=15
    )
    if resp.status_code != 200:
        raise HTTPException(502, f"Stripe error: {resp.text}")
    return resp.json()


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook — fulfill on checkout.session.completed."""
    payload   = await request.body()
    sig       = request.headers.get("stripe-signature", "")
    if STRIPE_WEBHOOK_SECRET:
        try:
            import stripe as stripe_lib
            event = stripe_lib.Webhook.construct_event(
                payload, sig, STRIPE_WEBHOOK_SECRET)
        except Exception as e:
            raise HTTPException(400, f"Webhook sig invalid: {e}")
    else:
        event = json.loads(payload)

    if event.get("type") == "checkout.session.completed":
        fulfill(event["data"]["object"])

    return {"received": True}
