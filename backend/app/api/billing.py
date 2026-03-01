"""Billing API endpoints (Stripe integration skeleton)."""

from fastapi import APIRouter, Depends, Request, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services import billing as billing_service
from app.core.dependencies import get_current_user

router = APIRouter()


class CheckoutCreate(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


@router.post("/billing/checkout")
async def create_checkout(payload: CheckoutCreate, user=Depends(get_current_user)):
    """Create a Stripe Checkout session. If user present, prefill email."""
    email = getattr(user, "email", None)
    session = billing_service.create_checkout_session(
        customer_email=email or "",
        price_id=payload.price_id,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
    )
    return {"session_id": session.id, "url": getattr(session, "url", None)}


@router.post("/billing/webhook")
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    """Raw webhook entry point for Stripe events."""
    body = await request.body()
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    event = billing_service.construct_event(body, stripe_signature)

    # Handle relevant event types
    if event["type"] == "checkout.session.completed":
        billing_service.handle_checkout_session_completed(event)

    return {"received": True}
