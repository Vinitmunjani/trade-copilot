"""Billing API endpoints."""

from fastapi import APIRouter, Depends, Request, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import select

from app.services import billing as billing_service
from app.core.dependencies import get_current_user
from app.database import async_session_factory
from app.models.subscription import Subscription

router = APIRouter()


class CheckoutCreate(BaseModel):
    price_id: Optional[str] = None
    plan: Optional[str] = None
    interval: str = "monthly"
    success_url: str
    cancel_url: str


class PortalCreate(BaseModel):
    return_url: str


@router.post("/billing/checkout")
async def create_checkout(payload: CheckoutCreate, user=Depends(get_current_user)):
    """Create Stripe Checkout session from explicit price_id or plan+interval."""
    email = getattr(user, "email", None)
    if not email:
        raise HTTPException(status_code=400, detail="User email is required for checkout")

    price_id = payload.price_id
    if not price_id:
        if not payload.plan:
            raise HTTPException(status_code=400, detail="Either price_id or plan is required")
        price_id = billing_service.get_price_id_for_plan(payload.plan, payload.interval)

    if not price_id:
        raise HTTPException(status_code=400, detail="No Stripe price configured for requested plan")

    session = billing_service.create_checkout_session(
        customer_email=email or "",
        price_id=price_id,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
        user_id=str(getattr(user, "id", "")),
        plan=payload.plan,
        interval=payload.interval,
    )
    return {"session_id": session.id, "url": getattr(session, "url", None)}


@router.get("/billing/subscription")
async def get_current_subscription(user=Depends(get_current_user)):
    """Return current user's subscription summary for dashboard billing view."""
    async with async_session_factory() as db:
        result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        sub = result.scalar_one_or_none()

    if not sub:
        return {
            "has_subscription": False,
            "plan": "free",
            "status": "inactive",
            "is_paid": False,
            "is_trial": False,
            "trial_expired": True,
            "current_period_end": None,
            "stripe_customer_id": None,
        }

    status_value = (sub.status or "").lower()
    is_trial = status_value == "trial"
    is_paid = status_value in {"active", "trialing", "past_due", "unpaid"} and not is_trial
    trial_expired = False
    if is_trial and sub.current_period_end:
        now = datetime.now(timezone.utc)
        period_end = sub.current_period_end
        if period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=timezone.utc)
        trial_expired = period_end < now

    return {
        "has_subscription": True,
        "plan": sub.plan,
        "status": sub.status,
        "is_paid": is_paid,
        "is_trial": is_trial,
        "trial_expired": trial_expired,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "stripe_customer_id": sub.stripe_customer_id,
    }


@router.post("/billing/portal")
async def create_billing_portal(payload: PortalCreate, user=Depends(get_current_user)):
    """Create a Stripe customer portal session for the authenticated user."""
    async with async_session_factory() as db:
        result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        sub = result.scalar_one_or_none()

    customer_id = sub.stripe_customer_id if sub else None
    if not customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found for user")

    session = billing_service.create_portal_session(customer_id=customer_id, return_url=payload.return_url)
    return {"url": getattr(session, "url", None)}


@router.post("/billing/webhook")
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    """Raw webhook entry point for Stripe events."""
    body = await request.body()
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    event = billing_service.construct_event(body, stripe_signature)

    # Handle relevant event types
    if event["type"] == "checkout.session.completed":
        await billing_service.handle_checkout_session_completed(event)

    return {"received": True}
