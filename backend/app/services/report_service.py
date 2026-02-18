"""Weekly AI report generation service.

Aggregates a week's trades and stats, sends to AI service for
comprehensive performance report generation.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trade import Trade, TradeStatus
from app.services.ai_service import generate_weekly_report
from app.services.stats_service import calculate_weekly_stats
from app.schemas.analysis import WeeklyReport

logger = logging.getLogger(__name__)


async def generate_report(
    db: AsyncSession,
    user_id: str,
    weeks_ago: int = 0,
) -> WeeklyReport:
    """Generate a comprehensive weekly trading performance report.

    Gathers all trades and statistics for the specified week,
    then sends them to the AI service for analysis.

    Args:
        db: Database session.
        user_id: User UUID string.
        weeks_ago: Number of weeks in the past (0 = current week).

    Returns:
        WeeklyReport with AI-generated insights and grades.
    """
    # Get weekly stats
    stats = await calculate_weekly_stats(db, user_id, weeks_ago)

    # Get all trades for the week
    now = datetime.now(timezone.utc)
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

    # Convert trades to dicts for the AI service
    trade_dicts = [
        {
            "symbol": t.symbol,
            "direction": t.direction.value if hasattr(t.direction, 'value') else str(t.direction),
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "sl": t.sl,
            "tp": t.tp,
            "pnl": t.pnl,
            "pnl_r": t.pnl_r,
            "duration_seconds": t.duration_seconds,
            "ai_score": t.ai_score,
            "behavioral_flags": t.behavioral_flags or [],
            "open_time": t.open_time.isoformat() if t.open_time else None,
            "close_time": t.close_time.isoformat() if t.close_time else None,
        }
        for t in trades
    ]

    # Generate AI report
    report = await generate_weekly_report(str(user_id), trade_dicts, stats)

    return report
