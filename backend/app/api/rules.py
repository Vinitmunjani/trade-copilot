"""Trading rules routes — CRUD for user-defined risk management rules and checklists."""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.trade import Trade, TradeStatus
from app.models.trading_rules import TradingRules
from app.models.user import User
from app.schemas.rules import (
    TradingRulesUpdate,
    TradingRulesResponse,
    RuleAdherenceItem,
    RuleAdherenceResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rules", tags=["Trading Rules"])


@router.get("", response_model=TradingRulesResponse)
async def get_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's trading rules.

    Returns the full set of risk management rules including
    max risk, min R:R, max trades per day, blocked sessions, etc.
    Creates default rules if none exist yet.
    """
    result = await db.execute(
        select(TradingRules).where(TradingRules.user_id == current_user.id)
    )
    rules = result.scalar_one_or_none()

    if not rules:
        # Create default rules
        rules = TradingRules(user_id=current_user.id)
        db.add(rules)
        await db.flush()

    return TradingRulesResponse.model_validate(rules)


@router.put("", response_model=TradingRulesResponse)
async def update_rules(
    payload: TradingRulesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's trading rules.

    Only provided fields are updated; omitted fields remain unchanged.
    """
    result = await db.execute(
        select(TradingRules).where(TradingRules.user_id == current_user.id)
    )
    rules = result.scalar_one_or_none()

    if not rules:
        rules = TradingRules(user_id=current_user.id)
        db.add(rules)
        await db.flush()

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rules, field, value)

    rules.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return TradingRulesResponse.model_validate(rules)


@router.get("/adherence", response_model=RuleAdherenceResponse)
async def get_rule_adherence(
    days: int = Query(7, ge=1, le=90, description="Lookback period in days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get rule adherence statistics for the specified period.

    Analyzes recent trades against the user's defined rules and returns
    a per-rule adherence breakdown with an overall score.
    """
    # Get rules
    result = await db.execute(
        select(TradingRules).where(TradingRules.user_id == current_user.id)
    )
    rules = result.scalar_one_or_none()

    if not rules:
        rules = TradingRules(user_id=current_user.id)
        db.add(rules)
        await db.flush()

    # Get trades in the period
    period_start = datetime.now(timezone.utc) - timedelta(days=days)
    period_end = datetime.now(timezone.utc)

    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.user_id == current_user.id,
                Trade.open_time >= period_start,
            )
        )
    )
    trades = result.scalars().all()

    if not trades:
        return RuleAdherenceResponse(
            overall_score=100.0,
            items=[],
            period_start=period_start,
            period_end=period_end,
        )

    items: list[RuleAdherenceItem] = []

    # Check max risk percent — based on behavioral flags
    risk_violations = 0
    for t in trades:
        if t.behavioral_flags:
            for flag in t.behavioral_flags:
                flag_name = flag.get("flag", "") if isinstance(flag, dict) else str(flag)
                if flag_name == "excessive_risk":
                    risk_violations += 1
                    break
    risk_adhered = risk_violations == 0
    items.append(RuleAdherenceItem(
        rule="max_risk_percent",
        description=f"Max risk per trade: {rules.max_risk_percent}%",
        adhered=risk_adhered,
        details=f"{risk_violations} violations in {len(trades)} trades" if not risk_adhered else None,
    ))

    # Check min risk/reward
    rr_violations = 0
    for t in trades:
        if t.behavioral_flags:
            for flag in t.behavioral_flags:
                flag_name = flag.get("flag", "") if isinstance(flag, dict) else str(flag)
                if flag_name == "bad_rr":
                    rr_violations += 1
                    break
    rr_adhered = rr_violations == 0
    items.append(RuleAdherenceItem(
        rule="min_risk_reward",
        description=f"Min risk/reward ratio: {rules.min_risk_reward}:1",
        adhered=rr_adhered,
        details=f"{rr_violations} trades below min R:R" if not rr_adhered else None,
    ))

    # Check max trades per day
    from collections import Counter
    daily_counts = Counter()
    for t in trades:
        day = t.open_time.date()
        daily_counts[day] += 1
    overtrading_days = sum(1 for count in daily_counts.values() if count > rules.max_trades_per_day)
    overtrade_adhered = overtrading_days == 0
    items.append(RuleAdherenceItem(
        rule="max_trades_per_day",
        description=f"Max {rules.max_trades_per_day} trades per day",
        adhered=overtrade_adhered,
        details=f"Exceeded on {overtrading_days} days" if not overtrade_adhered else None,
    ))

    # Check blocked sessions
    session_violations = 0
    for t in trades:
        if t.behavioral_flags:
            for flag in t.behavioral_flags:
                flag_name = flag.get("flag", "") if isinstance(flag, dict) else str(flag)
                if flag_name == "blocked_session":
                    session_violations += 1
                    break
    session_adhered = session_violations == 0
    items.append(RuleAdherenceItem(
        rule="blocked_sessions",
        description=f"Blocked sessions: {', '.join(rules.blocked_sessions or ['none'])}",
        adhered=session_adhered,
        details=f"{session_violations} trades in blocked sessions" if not session_adhered else None,
    ))

    # Check allowed symbols
    if rules.allowed_symbols:
        symbol_violations = [
            t for t in trades
            if t.symbol.upper() not in [s.upper() for s in rules.allowed_symbols]
        ]
        symbol_adhered = len(symbol_violations) == 0
        items.append(RuleAdherenceItem(
            rule="allowed_symbols",
            description=f"Allowed symbols: {', '.join(rules.allowed_symbols)}",
            adhered=symbol_adhered,
            details=f"{len(symbol_violations)} trades on non-allowed symbols" if not symbol_adhered else None,
        ))

    # Check revenge trading
    revenge_count = 0
    for t in trades:
        if t.behavioral_flags:
            for flag in t.behavioral_flags:
                flag_name = flag.get("flag", "") if isinstance(flag, dict) else str(flag)
                if flag_name == "revenge_trading":
                    revenge_count += 1
                    break
    revenge_adhered = revenge_count == 0
    items.append(RuleAdherenceItem(
        rule="min_time_between_trades",
        description=f"Min {rules.min_time_between_trades} min between trades after a loss",
        adhered=revenge_adhered,
        details=f"{revenge_count} potential revenge trades detected" if not revenge_adhered else None,
    ))

    # Calculate overall score
    total_rules = len(items)
    adhered_rules = sum(1 for item in items if item.adhered)
    overall_score = round((adhered_rules / total_rules) * 100, 1) if total_rules > 0 else 100.0

    return RuleAdherenceResponse(
        overall_score=overall_score,
        items=items,
        period_start=period_start,
        period_end=period_end,
    )


@router.get("/checklist")
async def get_checklist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the user's pre-trade checklist items.

    Returns the custom checklist defined in trading rules.
    """
    result = await db.execute(
        select(TradingRules).where(TradingRules.user_id == current_user.id)
    )
    rules = result.scalar_one_or_none()

    if not rules:
        rules = TradingRules(user_id=current_user.id)
        db.add(rules)
        await db.flush()

    return {
        "checklist": rules.custom_checklist or [],
        "total_items": len(rules.custom_checklist or []),
    }


@router.put("/checklist")
async def update_checklist(
    checklist: list[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the user's pre-trade checklist items.

    Replaces the entire checklist with the provided list of items.
    """
    result = await db.execute(
        select(TradingRules).where(TradingRules.user_id == current_user.id)
    )
    rules = result.scalar_one_or_none()

    if not rules:
        rules = TradingRules(user_id=current_user.id)
        db.add(rules)
        await db.flush()

    rules.custom_checklist = checklist
    rules.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return {
        "checklist": rules.custom_checklist,
        "total_items": len(rules.custom_checklist),
    }
