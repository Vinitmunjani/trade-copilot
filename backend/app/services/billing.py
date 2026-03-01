"""Stripe billing helper service (skeleton).

This module provides thin wrappers around Stripe operations used by the API.
Implementations should handle errors, logging and idempotency in production.
"""

import os
import stripe
from typing import Any, Dict
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select

from app.database import async_session_factory
from app.models.user import User
from app.models.subscription import Subscription

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def create_checkout_session(customer_email: str, price_id: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
    """Create a Stripe Checkout Session for a given price. Returns session object."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=customer_email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def construct_event(payload: bytes, sig_header: str):
    """Verify webhook signature and construct Stripe event."""
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=webhook_secret)
        return event
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {e}")


async def handle_checkout_session_completed(event: Dict[str, Any]):
    """Handle completed checkout.session.completed events.

    This will create or update Subscription records in the DB.
    """
    session_obj = event.get("data", {}).get("object", {})

    customer_id = session_obj.get("customer")
    subscription_id = session_obj.get("subscription")
    email = session_obj.get("customer_email")

    # Determine plan from price env vars if possible
    plan = "unknown"
    try:
        line_items = session_obj.get("display_items") or session_obj.get("line_items") or []
        # Fallback: use price from first listed item
        if isinstance(line_items, list) and line_items:
            price_ref = None
            first = line_items[0]
            # various payload shapes
            price_ref = first.get("price") if isinstance(first, dict) else None
            if not price_ref:
                price_ref = os.getenv("STRIPE_PRICE_STARTER")
            starter = os.getenv("STRIPE_PRICE_STARTER")
            pro = os.getenv("STRIPE_PRICE_PRO")
            if price_ref and starter and price_ref == starter:
                plan = "starter"
            elif price_ref and pro and price_ref == pro:
                plan = "pro"
    except Exception:
        plan = "unknown"

    async with async_session_factory() as db:
        user = None
        if email:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

        if not user:
            # If user not found, cannot attach subscription yet; record is skipped.
            return {"status": "no_user", "email": email}

        # Find existing subscription for user
        result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        sub = result.scalar_one_or_none()

        current_period_end_ts = session_obj.get("current_period_end")
        if current_period_end_ts:
            try:
                current_period_end = datetime.fromtimestamp(int(current_period_end_ts), tz=timezone.utc)
            except Exception:
                current_period_end = None
        else:
            current_period_end = None

        if sub:
            sub.stripe_customer_id = customer_id
            sub.stripe_subscription_id = subscription_id
            sub.status = "active"
            sub.plan = plan
            sub.current_period_end = current_period_end
            db.add(sub)
        else:
            new = Subscription(
                user_id=user.id,
                plan=plan,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                status="active",
                current_period_end=current_period_end,
            )
            db.add(new)

        await db.commit()

    return {"status": "ok", "user_id": str(user.id), "plan": plan}
