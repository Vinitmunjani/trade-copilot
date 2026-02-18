"""Statistics aggregation service.

Calculates daily, weekly, monthly P&L, win rate, R expectancy,
and per-symbol / per-session breakdowns.
"""

import logging
from datetime import datetime, timedelta, timezone, date
from typing import Any

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trade import Trade, TradeStatus
from app.models.daily_stats import DailyStats
from app.services.behavioral_service import get_current_session, SESSIONS

logger = logging.getLogger(__name__)


async def get_user_history_summary(
    db: AsyncSession,
    user_id: str,
    days: int = 30,
) -> dict:
    """Get a summary of the user's recent trading history for AI context.

    Args:
        db: Database session.
        user_id: User UUID.
        days: Number of days to look back.

    Returns:
        Dict with win rate, recent P&L, R-expectancy, today stats, streak info.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.user_id == user_id,
                Trade.status == TradeStatus.CLOSED,
                Trade.close_time >= cutoff,
            )
        ).order_by(Trade.close_time.desc())
    )
    trades = result.scalars().all()

    if not trades:
        return {
            "win_rate": 0,
            "last_10_pnl": 0,
            "r_expectancy": 0,
            "today_trades": 0,
            "today_pnl": 0,
            "streak": "N/A",
            "total_trades": 0,
        }

    # Win rate
    winners = [t for t in trades if t.pnl and t.pnl > 0]
    win_rate = (len(winners) / len(trades)) * 100 if trades else 0

    # Last 10 trades P&L
    last_10 = trades[:10]
    last_10_pnl = sum(t.pnl or 0 for t in last_10)

    # R-expectancy
    r_values = [t.pnl_r for t in trades if t.pnl_r is not None]
    r_expectancy = sum(r_values) / len(r_values) if r_values else 0

    # Today stats
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_trades = [t for t in trades if t.close_time and t.close_time >= today_start]
    today_pnl = sum(t.pnl or 0 for t in today_trades)

    # Current streak
    streak = 0
    streak_type = None
    for t in trades:  # Already ordered by close_time desc
        if t.pnl is None:
            continue
        if t.pnl > 0:
            if streak_type is None:
                streak_type = "winning"
            if streak_type == "winning":
                streak += 1
            else:
                break
        elif t.pnl < 0:
            if streak_type is None:
                streak_type = "losing"
            if streak_type == "losing":
                streak += 1
            else:
                break

    streak_text = f"{streak} {streak_type}" if streak_type else "N/A"

    return {
        "win_rate": round(win_rate, 1),
        "last_10_pnl": round(last_10_pnl, 2),
        "r_expectancy": round(r_expectancy, 3),
        "today_trades": len(today_trades),
        "today_pnl": round(today_pnl, 2),
        "streak": streak_text,
        "total_trades": len(trades),
    }


async def calculate_daily_stats(
    db: AsyncSession,
    user_id: str,
    target_date: date | None = None,
) -> dict:
    """Calculate aggregated statistics for a specific day.

    Args:
        db: Database session.
        user_id: User UUID.
        target_date: Date to calculate stats for. Defaults to today.

    Returns:
        Dict with all daily statistics.
    """
    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.user_id == user_id,
                Trade.status == TradeStatus.CLOSED,
                Trade.close_time >= day_start,
                Trade.close_time < day_end,
            )
        )
    )
    trades = result.scalars().all()

    if not trades:
        return {
            "date": target_date.isoformat(),
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "breakeven_trades": 0,
            "total_pnl": 0,
            "total_pnl_r": 0,
            "largest_win": 0,
            "largest_loss": 0,
            "avg_winner": 0,
            "avg_loser": 0,
            "win_rate": 0,
            "avg_rr": 0,
            "r_expectancy": 0,
            "session_breakdown": {},
            "symbol_breakdown": {},
        }

    winners = [t for t in trades if t.pnl and t.pnl > 0]
    losers = [t for t in trades if t.pnl and t.pnl < 0]
    breakeven = [t for t in trades if t.pnl is not None and t.pnl == 0]

    total_pnl = sum(t.pnl or 0 for t in trades)
    total_pnl_r = sum(t.pnl_r or 0 for t in trades)

    win_pnls = [t.pnl for t in winners if t.pnl]
    loss_pnls = [t.pnl for t in losers if t.pnl]
    r_values = [t.pnl_r for t in trades if t.pnl_r is not None]

    # Session breakdown
    session_data: dict[str, dict] = {}
    for t in trades:
        session = get_current_session(t.open_time)
        if session not in session_data:
            session_data[session] = {"trades": 0, "wins": 0, "pnl": 0}
        session_data[session]["trades"] += 1
        if t.pnl and t.pnl > 0:
            session_data[session]["wins"] += 1
        session_data[session]["pnl"] += t.pnl or 0

    for s in session_data:
        session_data[s]["win_rate"] = round(
            (session_data[s]["wins"] / session_data[s]["trades"]) * 100, 1
        ) if session_data[s]["trades"] > 0 else 0
        session_data[s]["pnl"] = round(session_data[s]["pnl"], 2)

    # Symbol breakdown
    symbol_data: dict[str, dict] = {}
    for t in trades:
        sym = t.symbol
        if sym not in symbol_data:
            symbol_data[sym] = {"trades": 0, "wins": 0, "pnl": 0}
        symbol_data[sym]["trades"] += 1
        if t.pnl and t.pnl > 0:
            symbol_data[sym]["wins"] += 1
        symbol_data[sym]["pnl"] += t.pnl or 0

    for s in symbol_data:
        symbol_data[s]["win_rate"] = round(
            (symbol_data[s]["wins"] / symbol_data[s]["trades"]) * 100, 1
        ) if symbol_data[s]["trades"] > 0 else 0
        symbol_data[s]["pnl"] = round(symbol_data[s]["pnl"], 2)

    return {
        "date": target_date.isoformat(),
        "total_trades": len(trades),
        "winning_trades": len(winners),
        "losing_trades": len(losers),
        "breakeven_trades": len(breakeven),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_r": round(total_pnl_r, 3),
        "largest_win": round(max(win_pnls) if win_pnls else 0, 2),
        "largest_loss": round(min(loss_pnls) if loss_pnls else 0, 2),
        "avg_winner": round(sum(win_pnls) / len(win_pnls) if win_pnls else 0, 2),
        "avg_loser": round(sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0, 2),
        "win_rate": round((len(winners) / len(trades)) * 100, 1),
        "avg_rr": 0,  # Calculated if R values available
        "r_expectancy": round(sum(r_values) / len(r_values) if r_values else 0, 3),
        "session_breakdown": session_data,
        "symbol_breakdown": symbol_data,
    }


async def calculate_weekly_stats(
    db: AsyncSession,
    user_id: str,
    weeks_ago: int = 0,
) -> dict:
    """Calculate aggregated statistics for a week.

    Args:
        db: Database session.
        user_id: User UUID.
        weeks_ago: Number of weeks in the past (0 = current week).

    Returns:
        Dict with weekly statistics.
    """
    now = datetime.now(timezone.utc)
    # Start of current week (Monday)
    week_start = (now - timedelta(days=now.weekday() + (weeks_ago * 7))).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = week_start + timedelta(days=7)

    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.user_id == user_id,
                Trade.status == TradeStatus.CLOSED,
                Trade.close_time >= week_start,
                Trade.close_time < week_end,
            )
        ).order_by(Trade.close_time.asc())
    )
    trades = result.scalars().all()

    winners = [t for t in trades if t.pnl and t.pnl > 0]
    total_pnl = sum(t.pnl or 0 for t in trades)
    total_r = sum(t.pnl_r or 0 for t in trades if t.pnl_r is not None)
    ai_scores = [t.ai_score for t in trades if t.ai_score is not None]
    all_flags = []
    for t in trades:
        if t.behavioral_flags:
            all_flags.extend(t.behavioral_flags)

    # Best and worst trades
    best_trade = max(trades, key=lambda t: t.pnl or 0) if trades else None
    worst_trade = min(trades, key=lambda t: t.pnl or 0) if trades else None

    return {
        "period": f"{week_start.date().isoformat()} to {week_end.date().isoformat()}",
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "total_trades": len(trades),
        "winning_trades": len(winners),
        "losing_trades": len(trades) - len(winners),
        "win_rate": round((len(winners) / len(trades)) * 100, 1) if trades else 0,
        "total_pnl": round(total_pnl, 2),
        "total_r": round(total_r, 3),
        "avg_ai_score": round(sum(ai_scores) / len(ai_scores), 1) if ai_scores else None,
        "total_flags": len(all_flags),
        "best_trade": {
            "symbol": best_trade.symbol,
            "pnl": best_trade.pnl,
            "direction": best_trade.direction.value if hasattr(best_trade.direction, 'value') else str(best_trade.direction),
        } if best_trade else None,
        "worst_trade": {
            "symbol": worst_trade.symbol,
            "pnl": worst_trade.pnl,
            "direction": worst_trade.direction.value if hasattr(worst_trade.direction, 'value') else str(worst_trade.direction),
        } if worst_trade else None,
    }


async def get_symbol_stats(
    db: AsyncSession,
    user_id: str,
    symbol: str,
    days: int = 90,
) -> dict:
    """Get performance statistics for a specific symbol.

    Args:
        db: Database session.
        user_id: User UUID.
        symbol: Trading instrument symbol.
        days: Lookback period in days.

    Returns:
        Dict with symbol-specific performance metrics.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.user_id == user_id,
                Trade.status == TradeStatus.CLOSED,
                Trade.symbol == symbol.upper(),
                Trade.close_time >= cutoff,
            )
        )
    )
    trades = result.scalars().all()

    winners = [t for t in trades if t.pnl and t.pnl > 0]
    losers = [t for t in trades if t.pnl and t.pnl < 0]

    return {
        "symbol": symbol.upper(),
        "period_days": days,
        "total_trades": len(trades),
        "winning_trades": len(winners),
        "losing_trades": len(losers),
        "win_rate": round((len(winners) / len(trades)) * 100, 1) if trades else 0,
        "total_pnl": round(sum(t.pnl or 0 for t in trades), 2),
        "avg_pnl": round(sum(t.pnl or 0 for t in trades) / len(trades), 2) if trades else 0,
        "avg_winner": round(sum(t.pnl for t in winners if t.pnl) / len(winners), 2) if winners else 0,
        "avg_loser": round(sum(t.pnl for t in losers if t.pnl) / len(losers), 2) if losers else 0,
        "best_trade": round(max((t.pnl for t in trades if t.pnl), default=0), 2),
        "worst_trade": round(min((t.pnl for t in trades if t.pnl), default=0), 2),
        "avg_duration_min": round(
            sum(t.duration_seconds or 0 for t in trades) / len(trades) / 60, 1
        ) if trades else 0,
    }


async def get_session_stats(
    db: AsyncSession,
    user_id: str,
    days: int = 90,
) -> dict:
    """Get performance statistics broken down by trading session.

    Args:
        db: Database session.
        user_id: User UUID.
        days: Lookback period in days.

    Returns:
        Dict with per-session performance metrics.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.user_id == user_id,
                Trade.status == TradeStatus.CLOSED,
                Trade.close_time >= cutoff,
            )
        )
    )
    trades = result.scalars().all()

    sessions: dict[str, dict] = {
        "asian": {"trades": 0, "wins": 0, "pnl": 0, "r_total": 0},
        "london": {"trades": 0, "wins": 0, "pnl": 0, "r_total": 0},
        "new_york": {"trades": 0, "wins": 0, "pnl": 0, "r_total": 0},
        "off_hours": {"trades": 0, "wins": 0, "pnl": 0, "r_total": 0},
    }

    for t in trades:
        session = get_current_session(t.open_time)
        if session not in sessions:
            sessions[session] = {"trades": 0, "wins": 0, "pnl": 0, "r_total": 0}
        sessions[session]["trades"] += 1
        if t.pnl and t.pnl > 0:
            sessions[session]["wins"] += 1
        sessions[session]["pnl"] += t.pnl or 0
        sessions[session]["r_total"] += t.pnl_r or 0

    # Calculate win rates
    for session_name, data in sessions.items():
        data["win_rate"] = round(
            (data["wins"] / data["trades"]) * 100, 1
        ) if data["trades"] > 0 else 0
        data["pnl"] = round(data["pnl"], 2)
        data["r_total"] = round(data["r_total"], 3)
        data["avg_pnl"] = round(
            data["pnl"] / data["trades"], 2
        ) if data["trades"] > 0 else 0

    return {
        "period_days": days,
        "sessions": sessions,
        "best_session": max(sessions, key=lambda s: sessions[s]["pnl"]) if trades else None,
        "worst_session": min(sessions, key=lambda s: sessions[s]["pnl"]) if trades else None,
    }


async def save_daily_stats(
    db: AsyncSession,
    user_id: str,
    target_date: date | None = None,
) -> DailyStats:
    """Calculate and save/update daily stats to the database.

    Args:
        db: Database session.
        user_id: User UUID.
        target_date: Target date. Defaults to today.

    Returns:
        The saved DailyStats model instance.
    """
    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    stats = await calculate_daily_stats(db, user_id, target_date)

    # Upsert
    import uuid as uuid_mod
    result = await db.execute(
        select(DailyStats).where(
            and_(
                DailyStats.user_id == user_id,
                DailyStats.date == target_date,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        daily = existing
    else:
        daily = DailyStats(user_id=user_id, date=target_date)
        db.add(daily)

    daily.total_trades = stats["total_trades"]
    daily.winning_trades = stats["winning_trades"]
    daily.losing_trades = stats["losing_trades"]
    daily.breakeven_trades = stats["breakeven_trades"]
    daily.total_pnl = stats["total_pnl"]
    daily.total_pnl_r = stats["total_pnl_r"]
    daily.largest_win = stats["largest_win"]
    daily.largest_loss = stats["largest_loss"]
    daily.avg_winner = stats["avg_winner"]
    daily.avg_loser = stats["avg_loser"]
    daily.win_rate = stats["win_rate"]
    daily.avg_rr = stats["avg_rr"]
    daily.r_expectancy = stats["r_expectancy"]
    daily.session_breakdown = stats["session_breakdown"]
    daily.symbol_breakdown = stats["symbol_breakdown"]

    await db.flush()
    return daily
