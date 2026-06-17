"""WF-01 — Stripe Billing Engine"""
import os, stripe
from fastapi import APIRouter, Request, HTTPException
from app.fire import fire

router = APIRouter()
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

ALLOWED_PRICES = {
    os.environ.get("PRICE_MCP_49", "price_mcp_49"),
    os.environ.get("PRICE_MEMBERSHIP_29", "price_membership_29"),
    os.environ.get("PRICE_CONSULTING_250", "price_consulting_250"),
}

@router.post("/api/billing/checkout")
async def create_checkout(request: Request):
    body = await request.json()
    price_id = body.get("price_id")
    if price_id not in ALLOWED_PRICES:
        raise HTTPException(400, detail=f"Invalid price_id: {price_id}")
    is_sub = os.environ.get("PRICE_MEMBERSHIP_29", "price_membership_29") == price_id
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription" if is_sub else "payment",
        success_url=os.environ["EVEZ_SUCCESS_URL"] + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=os.environ["EVEZ_CANCEL_URL"],
        metadata={"price_id": price_id},
    )
    return {"url": session.url}

@router.post("/api/billing/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, os.environ["STRIPE_WEBHOOK_SECRET"]
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, detail="Invalid Stripe signature")
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await fire("FIRE_CHECKOUT_COMPLETE", {
            "session_id": session["id"],
            "customer_email": session.get("customer_details", {}).get("email"),
            "amount_total": session.get("amount_total"),
            "price_id": session.get("metadata", {}).get("price_id"),
        })
    return {"status": "ok"}
