"""EVEZ Credit API — Stripe integration for paid plans."""
import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/billing", tags=["billing"])

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
APP_URL = os.environ.get("APP_URL", "http://localhost:8080")

# Price IDs — set these in your Stripe dashboard, then env vars
PRICES = {
    "pro_monthly": os.environ.get("STRIPE_PRICE_PRO_MONTHLY", "price_pro_monthly_placeholder"),
    "pro_yearly": os.environ.get("STRIPE_PRICE_PRO_YEARLY", "price_pro_yearly_placeholder"),
}


class CheckoutRequest(BaseModel):
    plan: str = "pro"
    interval: str = "monthly"
    email: str
    api_key: Optional[str] = None


@router.post("/checkout")
async def create_checkout(req: CheckoutRequest):
    """Create a Stripe Checkout session for plan upgrade."""
    if not stripe.api_key:
        raise HTTPException(501, "Stripe not configured on this server")

    price_key = f"{req.plan}_{req.interval}"
    price_id = PRICES.get(price_key)
    if not price_id or "placeholder" in price_id:
        raise HTTPException(400, f"Plan '{price_key}' not available yet")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=req.email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{APP_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{APP_URL}/billing/cancel",
            metadata={"api_key": req.api_key or "", "plan": req.plan},
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        raise HTTPException(400, str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (checkout completion, subscription changes)."""
    if not STRIPEWEBHOOK_SECRET:
        raise HTTPException(501, "Webhook secret not configured")

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email", "")
        plan = session.get("metadata", {}).get("plan", "pro")
        existing_key = session.get("metadata", {}).get("api_key", "")

        import credit_db
        if existing_key:
            key_row = credit_db.get_api_key(existing_key)
            if key_row:
                conn = credit_db.get_connection()
                conn.execute(
                    "UPDATE api_keys SET plan = ?, credits_remaining = 999999 WHERE key = ?",
                    (plan, existing_key),
                )
                conn.commit()
                conn.close()

        return {"status": "upgraded", "email": email, "plan": plan}

    return {"status": "ignored", "event_type": event["type"]}


@router.get("/success")
async def checkout_success(session_id: str = ""):
    return {"message": "Payment successful! Your API key has been upgraded.", "session_id": session_id}


@router.get("/cancel")
async def checkout_cancel():
    return {"message": "Payment cancelled."}
