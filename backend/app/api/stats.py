from typing import Optional, Union
"""Statistics routes — overview, daily, weekly, symbol, and session performance."""

import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.daily_stats import DailyStats
from app.models.user import User
from app.services.stats_service import (
    calculate_daily_stats,
    calculate_weekly_stats,
    get_symbol_stats,
    get_session_stats,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("/overview")
async def get_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get today's trading overview.

    Returns today's P&L, trade count, win rate, and average R-multiple.
    """
    today = datetime.now(timezone.utc).date()
    stats = await calculate_daily_stats(db, str(current_user.id), today)

    return {
        "date": today.isoformat(),
        "total_pnl": stats["total_pnl"],
        "total_trades": stats["total_trades"],
        "winning_trades": stats["winning_trades"],
        "losing_trades": stats["losing_trades"],
        "win_rate": stats["win_rate"],
        "avg_r": stats["r_expectancy"],
        "largest_win": stats["largest_win"],
        "largest_loss": stats["largest_loss"],
        "session_breakdown": stats["session_breakdown"],
        "symbol_breakdown": stats["symbol_breakdown"],
    }


@router.get("/daily")
async def get_daily_stats(
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily statistics for a date range.

    Defaults to the last 30 days if no range is specified.
    Returns precomputed daily stats from the daily_stats table,
    falling back to live calculation for dates without stored records.
    """
    if date_to is None:
        date_to = datetime.now(timezone.utc).date()
    if date_from is None:
        date_from = date_to - timedelta(days=30)

    # Fetch stored daily stats
    result = await db.execute(
        select(DailyStats)
        .where(
            and_(
                DailyStats.user_id == current_user.id,
                DailyStats.date >= date_from,
                DailyStats.date <= date_to,
            )
        )
        .order_by(DailyStats.date.asc())
    )
    stored = result.scalars().all()
    stored_dates = {s.date for s in stored}

    # Build response — use stored data where available, calculate missing days
    days = []
    current = date_from
    while current <= date_to:
        stored_entry = next((s for s in stored if s.date == current), None)
        if stored_entry:
            days.append({
                "date": current.isoformat(),
                "total_trades": stored_entry.total_trades,
                "winning_trades": stored_entry.winning_trades,
                "losing_trades": stored_entry.losing_trades,
                "total_pnl": stored_entry.total_pnl,
                "total_pnl_r": stored_entry.total_pnl_r,
                "win_rate": stored_entry.win_rate,
                "r_expectancy": stored_entry.r_expectancy,
                "largest_win": stored_entry.largest_win,
                "largest_loss": stored_entry.largest_loss,
                "session_breakdown": stored_entry.session_breakdown,
                "symbol_breakdown": stored_entry.symbol_breakdown,
            })
        else:
            # Calculate on-the-fly for missing dates
            stats = await calculate_daily_stats(db, str(current_user.id), current)
            if stats["total_trades"] > 0:
                days.append(stats)
        current += timedelta(days=1)

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "days": days,
        "total_days_with_trades": len([d for d in days if d.get("total_trades", 0) > 0]),
    }


@router.get("/weekly")
async def get_weekly_stats(
    weeks_ago: int = Query(0, ge=0, le=52, description="Weeks in the past (0 = current)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get weekly trading summary.

    Returns aggregated stats for the specified week including
    total trades, win rate, P&L, best/worst trade.
    """
    stats = await calculate_weekly_stats(db, str(current_user.id), weeks_ago)
    return stats


@router.get("/symbol/{symbol}")
async def get_symbol_performance(
    symbol: str,
    days: int = Query(90, ge=1, le=365, description="Lookback period in days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get performance statistics for a specific trading symbol.

    Provides win rate, average P&L, best/worst trade, and average duration
    for the specified symbol over the lookback period.
    """
    stats = await get_symbol_stats(db, str(current_user.id), symbol, days)
    return stats


@router.get("/sessions")
async def get_session_performance(
    days: int = Query(90, ge=1, le=365, description="Lookback period in days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get performance statistics broken down by trading session.

    Returns metrics for Asian, London, New York, and off-hours sessions
    including win rate, total P&L, and R-total for each.
    """
    stats = await get_session_stats(db, str(current_user.id), days)
    return stats
