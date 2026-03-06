"""Shared helpers for fetching trader data payloads used by dev/admin endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meta_account import MetaAccount
from app.models.trade import Trade, TradeStatus
from app.models.user import User
from app.services.metaapi_service import metaapi_service


def _is_connected_recently(last_heartbeat, minutes: int = 5) -> bool:
    if not last_heartbeat:
        return False
    now = datetime.now(timezone.utc)
    hb = last_heartbeat
    if hb.tzinfo is None:
        hb = hb.replace(tzinfo=timezone.utc)
    return (now - hb).total_seconds() < (minutes * 60)


async def resolve_target_user(
    db: AsyncSession,
    user_id: str | None = None,
    email: str | None = None,
) -> User:
    """Resolve a user from either UUID or email input."""
    user = None
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
            result = await db.execute(select(User).where(User.id == user_uuid))
            user = result.scalar_one_or_none()
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail=f"Invalid user_id format: {exc}")
    elif email:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
    else:
        raise HTTPException(status_code=400, detail="Either user_id or email is required")

    if not user:
        id_str = user_id or email
        raise HTTPException(status_code=404, detail=f"User {id_str} not found")
    return user


async def build_trader_data_payload(db: AsyncSession, user: User) -> dict:
    """Build trader-data diagnostic payload for a given user."""
    result = await db.execute(select(MetaAccount).where(MetaAccount.user_id == user.id))
    accounts = result.scalars().all()

    result = await db.execute(
        select(Trade).where((Trade.user_id == user.id) & (Trade.status == TradeStatus.OPEN))
    )
    trades = result.scalars().all()

    deduped_trades = []
    seen_open_external_ids = set()
    for trade in trades:
        ext_id = trade.external_trade_id
        if ext_id and ext_id in seen_open_external_ids:
            continue
        if ext_id:
            seen_open_external_ids.add(ext_id)
        deduped_trades.append(trade)

    async def _get_or_reconnect_logs(target_account_id: str, last_heartbeat) -> list[str]:
        account_logs = metaapi_service.get_logs(target_account_id)
        if account_logs:
            return account_logs

        user_id_str = str(user.id)
        is_live_connected = metaapi_service.is_account_connected(user_id_str, target_account_id)
        if not is_live_connected:
            try:
                reconnect_result = await metaapi_service.connect(user, account_id=target_account_id)
                if reconnect_result.get("connected"):
                    refreshed_logs = metaapi_service.get_logs(target_account_id)
                    if refreshed_logs:
                        return refreshed_logs
                    return [
                        f"[{datetime.now(timezone.utc).isoformat()}] Auto-reconnect succeeded for account {target_account_id}."
                    ]
                reconnect_error = reconnect_result.get("error") or reconnect_result.get("status")
                if reconnect_error:
                    return [
                        f"[{datetime.now(timezone.utc).isoformat()}] Auto-reconnect failed: {reconnect_error}."
                    ]
            except Exception as reconnect_error:
                return [
                    f"[{datetime.now(timezone.utc).isoformat()}] Auto-reconnect exception: {reconnect_error}."
                ]

        status_label = "connected" if _is_connected_recently(last_heartbeat) else "disconnected"
        hb = last_heartbeat.isoformat() if last_heartbeat else "never"
        return [
            f"[{datetime.now(timezone.utc).isoformat()}] No streaming events captured in this backend session. "
            f"Status: {status_label}. Last heartbeat: {hb}."
        ]

    logs_map = {}
    all_service_logs = metaapi_service.get_logs() or {}

    for acc in accounts:
        if acc.metaapi_account_id:
            account_logs = await _get_or_reconnect_logs(acc.metaapi_account_id, acc.mt_last_heartbeat)
            logs_map[acc.metaapi_account_id] = account_logs

    if user.metaapi_account_id and user.metaapi_account_id not in logs_map:
        account_logs = await _get_or_reconnect_logs(user.metaapi_account_id, user.mt_last_heartbeat)
        logs_map[user.metaapi_account_id] = account_logs

    for acc_id, lines in all_service_logs.items():
        if acc_id not in logs_map and lines:
            logs_map[acc_id] = list(lines)

    user_id_str = str(user.id)
    meta_list = []
    for acc in accounts:
        live_connected = bool(
            acc.metaapi_account_id
            and metaapi_service.is_account_connected(user_id_str, acc.metaapi_account_id)
        )
        meta_list.append(
            {
                "id": str(acc.id),
                "metaapi_account_id": acc.metaapi_account_id,
                "mt_login": acc.mt_login,
                "mt_server": acc.mt_server,
                "mt_platform": acc.mt_platform,
                "last_heartbeat": acc.mt_last_heartbeat,
                "connected": live_connected or _is_connected_recently(acc.mt_last_heartbeat),
            }
        )

    if user.metaapi_account_id and not any(
        m["metaapi_account_id"] == user.metaapi_account_id for m in meta_list
    ):
        meta_list.append(
            {
                "id": None,
                "metaapi_account_id": user.metaapi_account_id,
                "mt_login": user.mt_login,
                "mt_server": user.mt_server,
                "mt_platform": user.mt_platform,
                "last_heartbeat": user.mt_last_heartbeat,
                "connected": (
                    metaapi_service.is_account_connected(user_id_str, user.metaapi_account_id)
                    or _is_connected_recently(user.mt_last_heartbeat)
                ),
            }
        )

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "active": user.is_active,
        },
        "meta_accounts": meta_list,
        "open_trades": [
            {
                "id": str(trade.id),
                "external_id": trade.external_trade_id,
                "symbol": trade.symbol,
                "direction": trade.direction.value,
                "entry_price": trade.entry_price,
                "current_price": None,
                "lot_size": trade.lot_size,
                "sl": trade.sl,
                "tp": trade.tp,
                "open_time": trade.open_time,
                "ai_score": trade.ai_score,
                "ai_analysis": trade.ai_analysis,
                "behavioral_flags": trade.behavioral_flags,
            }
            for trade in deduped_trades
        ],
        "summary": {
            "total_accounts": len(accounts),
            "connected_accounts": sum(1 for m in meta_list if m.get("connected")),
            "open_trades_count": len(deduped_trades),
        },
        "streaming_logs": logs_map,
    }
