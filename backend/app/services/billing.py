"""Stripe billing helper service.

Provides wrappers around Stripe operations used by the billing API and
persists subscription state into the local database.
"""

import os
import uuid
import stripe
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select

from app.database import async_session_factory
from app.models.user import User
from app.models.subscription import Subscription

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def get_price_id_for_plan(plan: str, interval: str = "monthly") -> Optional[str]:
    """Resolve Stripe price ID from plan+interval using environment variables."""
    plan_key = (plan or "").strip().lower()
    interval_key = "annual" if (interval or "").strip().lower() in {"annual", "yearly"} else "monthly"

    env_key_map = {
        ("operator", "monthly"): "STRIPE_PRICE_OPERATOR_MONTHLY",
        ("operator", "annual"): "STRIPE_PRICE_OPERATOR_ANNUAL",
        ("tactician", "monthly"): "STRIPE_PRICE_TACTICIAN_MONTHLY",
        ("tactician", "annual"): "STRIPE_PRICE_TACTICIAN_ANNUAL",
        ("sovereign", "monthly"): "STRIPE_PRICE_SOVEREIGN_MONTHLY",
        ("sovereign", "annual"): "STRIPE_PRICE_SOVEREIGN_ANNUAL",
    }
    env_key = env_key_map.get((plan_key, interval_key))
    if env_key:
        price_id = os.getenv(env_key)
        if price_id:
            return price_id

    # Backward-compatible fallbacks from older env naming
    if plan_key == "operator":
        return os.getenv("STRIPE_PRICE_STARTER")
    if plan_key == "tactician":
        return os.getenv("STRIPE_PRICE_PRO")
    return None


def infer_plan_from_price_id(price_id: Optional[str]) -> str:
    """Infer logical plan name from a Stripe price ID."""
    if not price_id:
        return "unknown"
    pid = str(price_id)

    for plan in ("operator", "tactician", "sovereign"):
        for interval in ("monthly", "annual"):
            mapped = get_price_id_for_plan(plan, interval)
            if mapped and mapped == pid:
                return plan
    return "unknown"


def infer_plan_from_checkout_session(session_obj: Dict[str, Any]) -> str:
    """Infer plan from checkout session metadata or line item price."""
    metadata = session_obj.get("metadata") or {}
    metadata_plan = metadata.get("plan")
    if metadata_plan:
        return str(metadata_plan).strip().lower()

    line_items = session_obj.get("line_items") or session_obj.get("display_items") or []
    if isinstance(line_items, dict):
        line_items = line_items.get("data") or []

    if isinstance(line_items, list) and line_items:
        first = line_items[0] if isinstance(line_items[0], dict) else {}
        price_obj = first.get("price")
        price_id = price_obj.get("id") if isinstance(price_obj, dict) else price_obj
        inferred = infer_plan_from_price_id(price_id)
        if inferred != "unknown":
            return inferred

    return "unknown"


def create_checkout_session(
    customer_email: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
    user_id: Optional[str] = None,
    plan: Optional[str] = None,
    interval: str = "monthly",
) -> Dict[str, Any]:
    """Create a Stripe Checkout Session for a subscription price."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    metadata: Dict[str, str] = {}
    if user_id:
        metadata["user_id"] = str(user_id)
    if plan:
        metadata["plan"] = str(plan).lower()
    if interval:
        metadata["interval"] = str(interval).lower()

    payload: Dict[str, Any] = {
        "payment_method_types": ["card"],
        "mode": "subscription",
        "customer_email": customer_email,
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
    }
    if metadata:
        payload["metadata"] = metadata
    if user_id:
        payload["client_reference_id"] = str(user_id)

    try:
        return stripe.checkout.Session.create(**payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def create_portal_session(customer_id: str, return_url: str) -> Dict[str, Any]:
    """Create Stripe billing portal session for an existing Stripe customer."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    try:
        return stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def construct_event(payload: bytes, sig_header: str):
    """Verify webhook signature and construct Stripe event."""
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")

    try:
        return stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=webhook_secret)
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {e}")


async def handle_checkout_session_completed(event: Dict[str, Any]):
    """Handle completed checkout.session.completed events by upserting subscription."""
    session_obj = event.get("data", {}).get("object", {})

    customer_id = session_obj.get("customer")
    subscription_id = session_obj.get("subscription")
    email = session_obj.get("customer_email")
    metadata = session_obj.get("metadata") or {}

    # Prefer explicit metadata plan, then infer from line item price mapping
    plan = (metadata.get("plan") or "").strip().lower() or infer_plan_from_checkout_session(session_obj)

    async with async_session_factory() as db:
        user = None

        # 1) metadata.user_id
        metadata_user_id = metadata.get("user_id")
        if metadata_user_id:
            try:
                uid = uuid.UUID(str(metadata_user_id))
                result = await db.execute(select(User).where(User.id == uid))
                user = result.scalar_one_or_none()
            except Exception:
                user = None

        # 2) client_reference_id fallback
        if not user:
            client_ref = session_obj.get("client_reference_id")
            if client_ref:
                try:
                    uid = uuid.UUID(str(client_ref))
                    result = await db.execute(select(User).where(User.id == uid))
                    user = result.scalar_one_or_none()
                except Exception:
                    user = None

        # 3) email fallback
        if not user and email:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

        if not user:
            return {"status": "no_user", "email": email}

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
            sub.plan = plan or sub.plan or "unknown"
            sub.current_period_end = current_period_end
            db.add(sub)
        else:
            db.add(
                Subscription(
                    user_id=user.id,
                    plan=plan or "unknown",
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription_id,
                    status="active",
                    current_period_end=current_period_end,
                )
            )

        await db.commit()

    return {"status": "ok", "user_id": str(user.id), "plan": plan or "unknown"}
