"""Analysis routes — AI re-scoring, pattern analysis, and readiness assessment."""
from typing import Optional, List, Dict, Union, Any

import uuid
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, get_redis
from app.models.trade import Trade, TradeStatus
from app.models.trading_rules import TradingRules
from app.models.user import User
from app.schemas.analysis import TradeScore, PatternsResponse, PatternAnalysis
from app.services.ai_service import analyze_pre_trade, analyze_post_trade
from app.services.behavioral_service import run_all_checks
from app.services.market_service import get_market_context
from app.services.stats_service import get_user_history_summary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/rescore/{trade_id}")
async def rescore_trade(
    trade_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-run AI analysis on a specific trade.

    For open trades: re-runs pre-trade scoring with fresh market context.
    For closed trades: re-runs post-trade review.
    Returns the updated AI analysis/review.
    """
    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.id == trade_id,
                Trade.user_id == current_user.id,
            )
        )
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found",
        )

    user_id = str(current_user.id)

    if trade.status == TradeStatus.OPEN:
        # Re-run pre-trade analysis with fresh context
        result = await db.execute(
            select(TradingRules).where(TradingRules.user_id == current_user.id)
        )
        rules = result.scalar_one_or_none()

        # Behavioral checks
        alerts = await run_all_checks(db, user_id, trade, rules)
        trade.behavioral_flags = [a.dict() for a in alerts]

        # Market context + history
        redis_client = await get_redis()
        market = await get_market_context(trade.symbol, redis_client)
        history = await get_user_history_summary(db, user_id)

        trade_dict = {
            "symbol": trade.symbol,
            "direction": trade.direction.value if hasattr(trade.direction, "value") else str(trade.direction),
            "entry_price": trade.entry_price,
            "sl": trade.sl,
            "tp": trade.tp,
            "lot_size": trade.lot_size,
            "rr_ratio": None,
        }
        if trade.sl and trade.tp and trade.entry_price:
            risk = abs(trade.entry_price - trade.sl)
            reward = abs(trade.tp - trade.entry_price)
            trade_Dict["rr_ratio"] = round(reward / risk, 2) if risk > 0 else None

        score = await analyze_pre_trade(
            trade_dict, market, history,
            [a.dict() for a in alerts],
        )
        trade.ai_score = score.score
        trade.ai_analysis = score.dict()
        await db.flush()

        return {
            "trade_id": str(trade.id),
            "status": "OPEN",
            "ai_score": trade.ai_score,
            "ai_analysis": trade.ai_analysis,
            "behavioral_flags": trade.behavioral_flags,
        }

    else:
        # Re-run post-trade review
        trade_dict = {
            "symbol": trade.symbol,
            "direction": trade.direction.value if hasattr(trade.direction, "value") else str(trade.direction),
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "sl": trade.sl,
            "tp": trade.tp,
            "pnl": round(trade.pnl, 2) if trade.pnl else 0,
            "pnl_r": trade.pnl_r,
            "duration_seconds": trade.duration_seconds,
            "behavioral_flags": [
                f.get("flag", "") if isinstance(f, dict) else str(f)
                for f in (trade.behavioral_flags or [])
            ],
        }

        review = await analyze_post_trade(trade_dict, trade.ai_analysis)
        trade.ai_review = review.dict()
        await db.flush()

        return {
            "trade_id": str(trade.id),
            "status": "CLOSED",
            "ai_review": trade.ai_review,
        }


@router.get("/patterns", response_model=PatternsResponse)
async def get_patterns(
    days: int = Query(30, ge=7, le=180, description="Analysis period in days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get behavioral patterns detected across the user's trading history.

    Analyzes trades over the specified period and identifies recurring
    behavioral patterns (positive, negative, and neutral).
    """
    user_id = str(current_user.id)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.user_id == current_user.id,
                Trade.status == TradeStatus.CLOSED,
                Trade.close_time >= cutoff,
            )
        ).order_by(Trade.close_time.desc())
    )
    trades = result.scalars().all()

    if not trades:
        return PatternsResponse(
            patterns=[],
            analysis_period_days=days,
            total_trades_analyzed=0,
        )

    # Aggregate behavioral flags across all trades
    flag_counter: Dict[str, dict] = {}
    for t in trades:
        if not t.behavioral_flags:
            continue
        for flag_data in t.behavioral_flags:
            if isinstance(flag_data, dict):
                flag_name = flag_data.get("flag", "unknown")
                severity = flag_data.get("severity", "medium")
                message = flag_data.get("message", "")
            else:
                flag_name = str(flag_data)
                severity = "medium"
                message = str(flag_data)

            if flag_name not in flag_counter:
                flag_counter[flag_name] = {
                    "count": 0,
                    "severity": severity,
                    "message": message,
                }
            flag_counter[flag_name]["count"] += 1

    # Analyze win rate trends
    patterns: List[PatternAnalysis] = []

    # Behavioral flag patterns
    flag_descriptions = {
        "revenge_trading": ("Revenge Trading", "negative", "Trading too soon after a loss, driven by emotion"),
        "overtrading": ("Overtrading", "negative", "Exceeding daily trade limits or trading more than usual"),
        "blocked_session": ("Blocked Session Trading", "negative", "Trading during self-restricted sessions"),
        "weak_session": ("Weak Session Trading", "negative", "Trading during sessions with historically low win rate"),
        "bad_rr": ("Poor Risk/Reward", "negative", "Taking trades below minimum risk/reward ratio"),
        "excessive_risk": ("Excessive Risk", "negative", "Position sizing beyond risk limits"),
        "correlation_stacking": ("Correlation Stacking", "negative", "Multiple correlated positions in same direction"),
        "news_gambling": ("News Gambling", "negative", "Trading around high-impact news events"),
        "winner_cutting": ("Winner Cutting", "negative", "Closing winning trades too early compared to losers"),
    }

    for flag_name, data in flag_counter.items():
        desc_info = flag_descriptions.get(flag_name, (flag_name, "negative", data["message"]))
        patterns.append(PatternAnalysis(
            pattern=desc_info[0],
            frequency=data["count"],
            description=desc_info[2],
            impact=desc_info[1],
            recommendation=f"Occurred {data['count']} times in {len(trades)} trades. "
                          f"Review your {flag_name.replace('_', ' ')} behavior and consider adjusting your rules.",
        ))

    # Positive patterns — consistency checks
    winners = [t for t in trades if t.pnl and t.pnl > 0]
    win_rate = len(winners) / len(trades) * 100 if trades else 0

    if win_rate >= 55:
        patterns.append(PatternAnalysis(
            pattern="Consistent Winning",
            frequency=len(winners),
            description=f"Maintaining {win_rate:.1f}% win rate over {days} days",
            impact="positive",
            recommendation="Keep doing what's working. Document your best setups for replication.",
        ))

    # Check if trader respects SL/TP
    trades_with_sl = [t for t in trades if t.sl is not None]
    if trades_with_sl and len(trades_with_sl) / len(trades) >= 0.9:
        patterns.append(PatternAnalysis(
            pattern="Disciplined Risk Management",
            frequency=len(trades_with_sl),
            description="Consistently setting stop losses on trades",
            impact="positive",
            recommendation="Excellent discipline. Keep protecting your capital.",
        ))

    # Check average AI score trend
    scored_trades = [t for t in trades if t.ai_score is not None]
    if scored_trades:
        avg_score = sum(t.ai_score for t in scored_trades) / len(scored_trades)
        high_score_trades = [t for t in scored_trades if t.ai_score >= 7]

        if avg_score >= 7:
            patterns.append(PatternAnalysis(
                pattern="High Quality Setups",
                frequency=len(high_score_trades),
                description=f"Average AI score of {avg_score:.1f}/10 — selecting quality trades",
                impact="positive",
                recommendation="You're selecting good setups. Focus on execution and patience.",
            ))
        elif avg_score <= 4:
            patterns.append(PatternAnalysis(
                pattern="Low Quality Setups",
                frequency=len(scored_trades) - len(high_score_trades),
                description=f"Average AI score of {avg_score:.1f}/10 — taking marginal setups",
                impact="negative",
                recommendation="Be more selective. Wait for higher quality setups scoring 6+.",
            ))

    # Sort: negative patterns first (most impactful), then by frequency
    patterns.sort(key=lambda p: (0 if p.impact == "negative" else 1, -p.frequency))

    return PatternsResponse(
        patterns=patterns,
        analysis_period_days=days,
        total_trades_analyzed=len(trades),
    )


@router.get("/readiness")
async def get_readiness(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current trading readiness score.

    Evaluates the trader's current state based on:
    - Today's performance (P&L, trade count)
    - Recent behavioral flags
    - Rule adherence
    - Current trading session
    - Upcoming news events

    Returns a 0-100 readiness score with detailed breakdown.
    """
    user_id = str(current_user.id)

    # Get rules
    rules_result = await db.execute(
        select(TradingRules).where(TradingRules.user_id == current_user.id)
    )
    rules = rules_result.scalar_one_or_none()

    # Get today's trades
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    trades_result = await db.execute(
        select(Trade).where(
            and_(
                Trade.user_id == current_user.id,
                Trade.open_time >= today_start,
            )
        ).order_by(Trade.open_time.desc())
    )
    today_trades = trades_result.scalars().all()

    # Get recent history
    history = await get_user_history_summary(db, user_id, days=7)

    # Calculate readiness components
    score = 100
    factors: List[dict] = []

    # 1. Daily trade count check
    max_trades = rules.max_trades_per_day if rules else 5
    today_count = len(today_trades)
    if today_count >= max_trades:
        score -= 40
        factors.append({
            "factor": "trade_limit",
            "impact": -40,
            "message": f"Daily trade limit reached ({today_count}/{max_trades})",
        })
    elif today_count >= max_trades * 0.8:
        score -= 15
        factors.append({
            "factor": "trade_limit",
            "impact": -15,
            "message": f"Approaching daily limit ({today_count}/{max_trades})",
        })

    # 2. Daily P&L check
    today_pnl = sum(t.pnl or 0 for t in today_trades if t.status == TradeStatus.CLOSED)
    max_daily_loss = rules.max_daily_loss_percent if rules else 5.0
    # Approximate check (we don't have account balance, so use absolute threshold)
    if today_pnl < -500:  # Major loss
        score -= 30
        factors.append({
            "factor": "daily_pnl",
            "impact": -30,
            "message": f"Significant daily loss: ${today_pnl:.2f}. Consider stopping for the day.",
        })
    elif today_pnl < -200:
        score -= 15
        factors.append({
            "factor": "daily_pnl",
            "impact": -15,
            "message": f"Notable daily loss: ${today_pnl:.2f}. Trade cautiously.",
        })

    # 3. Recent loss check (revenge trading risk)
    closed_today = [t for t in today_trades if t.status == TradeStatus.CLOSED]
    if closed_today:
        last_trade = closed_today[0]  # Most recent
        if last_trade.pnl and last_trade.pnl < 0:
            minutes_since = (datetime.now(timezone.utc) - (last_trade.close_time or datetime.now(timezone.utc))).total_seconds() / 60
            min_time = rules.min_time_between_trades if rules else 10
            if minutes_since < min_time:
                score -= 25
                factors.append({
                    "factor": "revenge_risk",
                    "impact": -25,
                    "message": f"Recent loss {minutes_since:.0f} min ago. Wait {min_time - minutes_since:.0f} more minutes.",
                })

    # 4. Losing streak check
    streak_text = history.get("streak", "")
    if "losing" in streak_text:
        try:
            streak_num = int(streak_text.split()[0])
            if streak_num >= 3:
                penalty = min(30, streak_num * 10)
                score -= penalty
                factors.append({
                    "factor": "losing_streak",
                    "impact": -penalty,
                    "message": f"On a {streak_num}-trade losing streak. Consider taking a break.",
                })
        except (ValueError, IndexError):
            pass

    # 5. Current session check
    from app.services.behavioral_service import get_current_session
    session = get_current_session()
    if rules and rules.blocked_sessions and session in rules.blocked_sessions:
        score -= 30
        factors.append({
            "factor": "blocked_session",
            "impact": -30,
            "message": f"Currently in blocked session: {session}",
        })

    # 6. News check
    try:
        redis_client = await get_redis()
        from app.services.news_service import get_upcoming_high_impact_events
        news_events = await get_upcoming_high_impact_events(
            within_minutes=30, redis_client=redis_client
        )
        if news_events:
            score -= 20
            event_names = [e.get("title", "Unknown") for e in news_events[:3]]
            factors.append({
                "factor": "news_risk",
                "impact": -20,
                "message": f"High-impact news within 30 min: {', '.join(event_names)}",
            })
    except Exception as e:
        logger.warning(f"News check failed in readiness: {e}")

    # Clamp score
    score = max(0, min(100, score))

    # Determine readiness level
    if score >= 80:
        level = "ready"
        emoji = "🟢"
    elif score >= 60:
        level = "caution"
        emoji = "🟡"
    elif score >= 40:
        level = "warning"
        emoji = "🟠"
    else:
        level = "stop"
        emoji = "🔴"

    return {
        "readiness_score": score,
        "level": level,
        "emoji": emoji,
        "message": f"{emoji} Readiness: {score}/100 — {level.upper()}",
        "factors": factors,
        "today_trades": today_count,
        "today_pnl": round(today_pnl, 2),
        "current_session": session,
    }
