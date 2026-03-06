"""Admin API routes."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_admin_user, get_db
from app.core.security import hash_password
from app.models.admin_audit_log import AdminAuditLog
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.user import AdminUserUpdateRequest, AdminUserUpdateResponse, AdminSubscriptionResponse, UserResponse
from app.services.trader_data_service import build_trader_data_payload, resolve_target_user

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)


def _normalize_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _serialize_dt(value: datetime | None) -> str | None:
    normalized = _normalize_utc(value)
    return normalized.isoformat() if normalized else None


def _user_snapshot(user: User) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "email": user.email,
        "is_active": user.is_active,
        "settings": user.settings,
        "mt_login": user.mt_login,
        "mt_server": user.mt_server,
        "mt_platform": user.mt_platform,
        "mt_last_heartbeat": _serialize_dt(user.mt_last_heartbeat),
    }


def _subscription_snapshot(sub: Subscription | None) -> dict[str, Any] | None:
    if sub is None:
        return None
    return {
        "id": str(sub.id),
        "plan": sub.plan,
        "status": sub.status,
        "current_period_end": _serialize_dt(sub.current_period_end),
        "cancel_at_period_end": bool(sub.cancel_at_period_end),
    }


@router.get("/trader-data")
async def admin_get_trader_data(
    user_id: str = Query(None, description="User ID (UUID)"),
    email: str = Query(None, description="User email to lookup"),
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint: fetch detailed trader data for any user."""
    user = await resolve_target_user(db=db, user_id=user_id, email=email)
    return await build_trader_data_payload(db=db, user=user)


@router.patch("/users/{user_id}", response_model=AdminUserUpdateResponse)
async def admin_update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdateRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint: partially update user, secrets, and subscription fields.

    `settings` is merged into existing JSON settings (partial merge).
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updates = payload.model_dump(exclude_unset=True)
    subscription_updates = updates.pop("subscription", None)

    if not updates and not subscription_updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No changes requested",
        )

    subscription_result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .order_by(Subscription.updated_at.desc())
    )
    sub = subscription_result.scalars().first()

    before_data = {
        "user": _user_snapshot(user),
        "subscription": _subscription_snapshot(sub),
    }

    changed_fields: dict[str, list[str]] = {
        "user": [],
        "secrets": [],
        "subscription": [],
    }

    if "email" in updates and updates["email"] is not None:
        new_email = updates["email"].strip().lower()
        existing = await db.execute(select(User).where(User.email == new_email, User.id != user_id))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use by another user",
            )
        user.email = new_email
        changed_fields["user"].append("email")

    if "is_active" in updates:
        user.is_active = updates["is_active"]
        changed_fields["user"].append("is_active")

    if "password" in updates and updates["password"] is not None:
        user.hashed_password = hash_password(updates["password"])
        changed_fields["secrets"].append("password")

    if "metaapi_token" in updates:
        user.metaapi_token = updates["metaapi_token"]
        changed_fields["secrets"].append("metaapi_token")

    if "settings" in updates and updates["settings"] is not None:
        existing_settings = user.settings or {}
        if not isinstance(existing_settings, dict):
            existing_settings = {}
        user.settings = {**existing_settings, **updates["settings"]}
        changed_fields["user"].append("settings")

    if "mt_login" in updates:
        user.mt_login = updates["mt_login"]
        changed_fields["user"].append("mt_login")

    if "mt_server" in updates:
        user.mt_server = updates["mt_server"]
        changed_fields["user"].append("mt_server")

    if "mt_platform" in updates:
        user.mt_platform = updates["mt_platform"]
        changed_fields["user"].append("mt_platform")

    if "mt_last_heartbeat" in updates:
        user.mt_last_heartbeat = _normalize_utc(updates["mt_last_heartbeat"])
        changed_fields["user"].append("mt_last_heartbeat")

    if subscription_updates is not None:
        if sub is None:
            sub = Subscription(
                user_id=user.id,
                plan=(subscription_updates.get("plan") or "unknown"),
                status=(subscription_updates.get("status") or "inactive"),
                current_period_end=_normalize_utc(subscription_updates.get("current_period_end")),
                cancel_at_period_end=bool(subscription_updates.get("cancel_at_period_end") or False),
            )
            db.add(sub)
            changed_fields["subscription"].append("created")
        else:
            if "plan" in subscription_updates and subscription_updates["plan"] is not None:
                sub.plan = subscription_updates["plan"]
                changed_fields["subscription"].append("plan")
            if "status" in subscription_updates and subscription_updates["status"] is not None:
                sub.status = subscription_updates["status"]
                changed_fields["subscription"].append("status")
            if "current_period_end" in subscription_updates:
                sub.current_period_end = _normalize_utc(subscription_updates.get("current_period_end"))
                changed_fields["subscription"].append("current_period_end")
            if "cancel_at_period_end" in subscription_updates and subscription_updates["cancel_at_period_end"] is not None:
                sub.cancel_at_period_end = bool(subscription_updates["cancel_at_period_end"])
                changed_fields["subscription"].append("cancel_at_period_end")

        sub.updated_at = datetime.now(timezone.utc)

    user.updated_at = datetime.now(timezone.utc)
    await db.flush()

    after_data = {
        "user": _user_snapshot(user),
        "subscription": _subscription_snapshot(sub),
    }

    if "password" in updates:
        before_data["user"]["password"] = "[redacted]"
        after_data["user"]["password"] = "[updated]"
    if "metaapi_token" in updates:
        before_data["user"]["metaapi_token"] = "[redacted]"
        after_data["user"]["metaapi_token"] = "[updated]"

    audit = AdminAuditLog(
        admin_user_id=admin_user.id,
        target_user_id=user.id,
        action="admin_user_update",
        changed_fields=changed_fields,
        before_data=before_data,
        after_data=after_data,
    )
    db.add(audit)
    await db.flush()

    logger.info(
        "Admin user update by %s for target_user_id=%s fields=%s",
        admin_user.email,
        str(user.id),
        changed_fields,
    )

    subscription_response = None
    if sub is not None:
        subscription_response = AdminSubscriptionResponse(
            plan=sub.plan,
            status=sub.status,
            current_period_end=sub.current_period_end,
            cancel_at_period_end=bool(sub.cancel_at_period_end),
        )

    return AdminUserUpdateResponse(
        user=UserResponse.model_validate(user),
        subscription=subscription_response,
        changed_fields=changed_fields,
    )
