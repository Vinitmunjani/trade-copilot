"""Trial expiry enforcement service.

Periodically scans for expired trial subscriptions and force-disconnects +
undeploys all linked MetaAPI accounts to control infrastructure costs.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import async_session_factory
from app.models.subscription import Subscription
from app.models.user import User
from app.models.meta_account import MetaAccount
from app.services.metaapi_service import metaapi_service

logger = logging.getLogger(__name__)

ENFORCEMENT_INTERVAL_SECONDS = 180


def _normalize_utc(dt_value):
    if not dt_value:
        return None
    if dt_value.tzinfo is None:
        return dt_value.replace(tzinfo=timezone.utc)
    return dt_value.astimezone(timezone.utc)


async def enforce_expired_trials_once() -> int:
    """Force disconnect+undeploy MetaAPI accounts for expired trial users.

    Returns the number of accounts processed.
    """
    now = datetime.now(timezone.utc)
    processed = 0

    async with async_session_factory() as db:
        trial_subs_result = await db.execute(
            select(Subscription).where(Subscription.status == "trial")
        )
        trial_subs = trial_subs_result.scalars().all()

        expired_user_ids = []
        for sub in trial_subs:
            period_end = _normalize_utc(sub.current_period_end)
            if period_end and period_end < now:
                expired_user_ids.append(sub.user_id)

        if not expired_user_ids:
            return 0

        users_result = await db.execute(select(User).where(User.id.in_(expired_user_ids)))
        users = users_result.scalars().all()
        user_map = {u.id: u for u in users}

        accounts_result = await db.execute(
            select(MetaAccount).where(MetaAccount.user_id.in_(expired_user_ids))
        )
        accounts = [a for a in accounts_result.scalars().all() if a.metaapi_account_id]

    for account in accounts:
        user = user_map.get(account.user_id)
        if not user:
            continue
        try:
            await metaapi_service.disconnect(
                user,
                account_id=account.metaapi_account_id,
                force_undeploy=True,
            )
            processed += 1
        except Exception as e:
            logger.warning(
                f"Trial enforcement failed for user={account.user_id} account={account.metaapi_account_id}: {e}"
            )

    if processed:
        logger.info(f"Trial enforcement processed {processed} MetaAPI account(s)")
    return processed


async def run_trial_enforcement_loop(stop_event: asyncio.Event):
    """Background loop that repeatedly enforces expired trial disconnections."""
    logger.info("Trial enforcement loop started")
    while not stop_event.is_set():
        try:
            await enforce_expired_trials_once()
        except Exception as e:
            logger.error(f"Trial enforcement loop error: {e}")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=ENFORCEMENT_INTERVAL_SECONDS)
        except asyncio.TimeoutError:
            continue

    logger.info("Trial enforcement loop stopped")
