"""WF-01 — Fulfillment: issue API key + send tier-specific email on FIRE_CHECKOUT_COMPLETE"""
import os, secrets, httpx
from app.fire import on_fire
from app.db import db

PRODUCT_TIERS = {
    os.environ.get("PRICE_MCP_49", "price_mcp_49"): "mcp_access",
    os.environ.get("PRICE_MEMBERSHIP_29", "price_membership_29"): "membership",
    os.environ.get("PRICE_CONSULTING_250", "price_consulting_250"): "consulting",
}

@on_fire("FIRE_CHECKOUT_COMPLETE")
async def fulfill(payload: dict):
    email = payload["customer_email"]
    price_id = payload.get("price_id", "")
    tier = PRODUCT_TIERS.get(price_id, "free")
    api_key = "evez_" + secrets.token_urlsafe(32)
    await db.execute(
        "INSERT INTO api_keys (key, user_email, tier, usage_count, revoked) "
        "VALUES ($1, $2, $3, 0, false)",
        api_key, email, tier,
    )
    await _send_email(email, tier, api_key)

async def _send_email(email: str, tier: str, api_key: str):
    subject, html = _build_email(tier, api_key)
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {os.environ['SENDGRID_API_KEY']}"},
            json={
                "personalizations": [{"to": [{"email": email}]}],
                "from": {"email": os.environ["EVEZ_FROM_EMAIL"]},
                "subject": subject,
                "content": [{"type": "text/html", "value": html}],
            },
        )
        r.raise_for_status()

def _build_email(tier: str, api_key: str):
    base = "https://evez.app"
    if tier == "mcp_access":
        return (
            "Your EVEZ MCP Access — API Key Inside",
            f"""<h2 style='font-family:monospace'>Welcome to EVEZ MCP</h2>
<p>Your API key:</p>
<pre style='background:#111;color:#0f0;padding:12px'>{api_key}</pre>
<p>Add this header to every request:<br>
<code>X-EVEZ-API-KEY: {api_key}</code></p>
<p><a href='{base}/docs'>View MCP Docs &rarr;</a></p>""",
        )
    elif tier == "membership":
        return (
            "EVEZ Membership Active — Dashboard Ready",
            f"""<h2 style='font-family:monospace'>Membership Confirmed</h2>
<p>Your API key: <code>{api_key}</code></p>
<p><a href='{base}/dashboard'>Open Dashboard &rarr;</a></p>""",
        )
    else:
        return (
            "EVEZ Consulting Session — Book Now",
            """<h2 style='font-family:monospace'>Thank You!</h2>
<p>Book your session: <a href='https://calendly.com/evez666'>Calendly &rarr;</a></p>""",
        )
