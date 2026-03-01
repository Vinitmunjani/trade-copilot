import time
import pytest
from sqlalchemy import select

from app.database import init_db, async_session_factory
from app.models.user import User
from app.models.subscription import Subscription
from app.services.billing import handle_checkout_session_completed


@pytest.mark.asyncio
async def test_handle_checkout_session_creates_subscription():
    # Ensure DB tables exist
    await init_db()

    # Create a test user
    async with async_session_factory() as db:
        user = User(email="webhook-test@example.com", hashed_password="x")
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Ensure no subscription exists initially
        res = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        assert res.scalar_one_or_none() is None

    # Simulated Stripe event
    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_test_123",
                "subscription": "sub_test_123",
                "customer_email": "webhook-test@example.com",
                "current_period_end": int(time.time()) + 3600,
            }
        },
    }

    result = await handle_checkout_session_completed(event)
    assert result.get("status") == "ok"

    # Verify subscription was created
    async with async_session_factory() as db:
        res = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        sub = res.scalar_one_or_none()
        assert sub is not None
        assert sub.stripe_subscription_id == "sub_test_123"
        assert sub.stripe_customer_id == "cus_test_123"
        assert sub.status == "active"
