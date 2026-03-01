from typing import Optional, Union
"""Statistics routes — overview, daily, weekly, symbol, and session performance."""

import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.daily_stats import DailyStats
from app.models.trade import Trade, TradeStatus
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

    _total_trades = stats["total_trades"]
    _flag_count = stats.get("behavioral_flags_count", 0)
    adherence = round(max(0.0, ((_total_trades - _flag_count) / max(1, _total_trades)) * 100), 1) if _total_trades > 0 else 100.0

    return {
        "date": today.isoformat(),
        "total_pnl": stats["total_pnl"],
        "total_pnl_r": stats.get("total_pnl_r", 0),
        "total_trades": stats["total_trades"],
        "winning_trades": stats["winning_trades"],
        "losing_trades": stats["losing_trades"],
        "win_rate": stats["win_rate"],
        "avg_r": stats["r_expectancy"],
        "adherence": adherence,
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
                "behavioral_flags_count": stored_entry.behavioral_flags_count or 0,
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


def _compute_weekly_grade(win_rate: float, total_pnl: float, total_flags: int, total_trades: int) -> str:
    """Compute an A-F grade for a trading week based on performance metrics."""
    pts = min(40.0, win_rate * 0.4)
    pts += 20.0 if total_pnl > 0 else 0.0
    pts += max(0.0, 20.0 - (total_flags / max(1, total_trades)) * 40)
    pts += min(20.0, total_trades * 2.0)
    if pts >= 80: return "A"
    if pts >= 65: return "B"
    if pts >= 50: return "C"
    if pts >= 35: return "D"
    return "F"


@router.get("/weekly-reports")
async def get_weekly_reports(
    weeks: int = Query(4, ge=1, le=12, description="Number of past weeks to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate weekly performance reports from real trade data.

    Returns the last N weeks with grade, P&L, win rate, patterns detected,
    strengths/weaknesses, and an actionable top suggestion.
    """
    from uuid import uuid4 as _uuid4

    now = datetime.now(timezone.utc)
    reports = []

    for weeks_ago in range(weeks):
        week_start = (now - timedelta(days=now.weekday() + weeks_ago * 7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        week_end = week_start + timedelta(days=7)

        result = await db.execute(
            select(Trade).where(
                and_(
                    Trade.user_id == current_user.id,
                    Trade.status == TradeStatus.CLOSED,
                    Trade.close_time >= week_start,
                    Trade.close_time < week_end,
                )
            ).order_by(Trade.close_time.asc())
        )
        trades = result.scalars().all()

        if not trades:
            continue

        total_trades = len(trades)
        winners = [t for t in trades if t.pnl and t.pnl > 0]
        win_rate = round(len(winners) / total_trades * 100, 1) if total_trades else 0.0
        total_pnl = round(sum(t.pnl or 0 for t in trades), 2)
        total_r = sum(t.pnl_r or 0 for t in trades if t.pnl_r is not None)
        avg_r = round(total_r / total_trades, 2) if total_trades else 0.0

        # Collect unique flag names and total count
        flag_names: set = set()
        all_flags: list = []
        for t in trades:
            if t.behavioral_flags:
                for f in t.behavioral_flags:
                    name = (f.get("flag") or f.get("type") or "unknown") if isinstance(f, dict) else str(f)
                    flag_names.add(name)
                    all_flags.append(f)
        total_flags = len(all_flags)
        patterns_detected = sorted(flag_names)

        grade = _compute_weekly_grade(win_rate, total_pnl, total_flags, total_trades)

        # Strengths
        strengths: list = []
        if win_rate >= 60:
            strengths.append(f"Strong win rate of {win_rate}%")
        if total_pnl > 0:
            strengths.append(f"Net profitable week (+${total_pnl:.2f})")
        if avg_r >= 1.5:
            strengths.append(f"Good average R-multiple of {avg_r}R")
        ai_scores = [t.ai_score for t in trades if t.ai_score is not None]
        if ai_scores and (sum(ai_scores) / len(ai_scores)) >= 7:
            strengths.append(f"Quality setups — avg AI score {round(sum(ai_scores)/len(ai_scores),1)}/10")
        if not flag_names:
            strengths.append("Clean trading — no behavioral flags detected")
        if not strengths:
            strengths.append("Trades executed with defined risk levels")

        # Weaknesses
        weaknesses: list = []
        if win_rate < 45:
            weaknesses.append(f"Below-average win rate of {win_rate}%")
        if total_pnl < 0:
            weaknesses.append(f"Net losing week (${total_pnl:.2f})")
        if "revenge_trading" in flag_names:
            weaknesses.append("Revenge trading — emotional decisions after losses")
        if "overtrading" in flag_names:
            weaknesses.append("Overtrading — exceeding daily trade limits")
        if "moved_stop_loss" in flag_names:
            weaknesses.append("Stop-loss discipline — SL moved against the trade")
        if avg_r < 0:
            weaknesses.append(f"Negative R expectancy ({avg_r}R per trade)")
        if not weaknesses:
            weaknesses.append("No major issues detected this week")

        # Top suggestion
        if "revenge_trading" in flag_names:
            suggestion = "Take a break after 2+ consecutive losses to reset before trading again."
        elif "overtrading" in flag_names:
            suggestion = "Stick to your daily trade limit — quality over quantity."
        elif "moved_stop_loss" in flag_names:
            suggestion = "Honor your stop losses. Moving them widens risk beyond your plan."
        elif win_rate < 45:
            suggestion = "Be more selective — only take setups scoring 7+ on AI pre-trade analysis."
        elif avg_r < 1.0:
            suggestion = "Focus on R:R — only enter trades with at least a 2:1 risk/reward setup."
        else:
            suggestion = "Keep documenting your best setups; consistency is your edge."

        # Summary
        if grade in ("A", "B"):
            summary = (
                f"Strong week with {win_rate}% win rate and +${total_pnl:.2f} P&L across "
                f"{total_trades} trade{'s' if total_trades != 1 else ''}."
            )
        elif grade == "C":
            summary = (
                f"Mixed week — {win_rate}% win rate, {total_trades} trades, "
                f"{len(flag_names)} pattern(s) flagged."
            )
        else:
            summary = (
                f"Challenging week — {win_rate}% win rate, ${total_pnl:.2f} P&L. "
                "Focus on discipline and process improvement."
            )

        reports.append({
            "id": f"week-{weeks_ago}-{week_start.date().isoformat()}",
            "week_start": week_start.date().isoformat(),
            "week_end": week_end.date().isoformat(),
            "summary": summary,
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "avg_r": avg_r,
            "patterns_detected": patterns_detected,
            "top_suggestion": suggestion,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "grade": grade,
        })

    return reports
