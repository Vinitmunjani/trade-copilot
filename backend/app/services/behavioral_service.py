"""Behavioral pattern detection service.

Detects trading psychology red flags using rule-based logic:
- Revenge trading
- Overtrading
- Wrong session trading
- Bad risk/reward
- Excessive risk
- Correlation stacking
- News gambling
- Winner cutting
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict,  Optional, Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trade import Trade, TradeStatus, TradeDirection
from app.models.trading_rules import TradingRules
from app.schemas.analysis import BehavioralAlert

# Asset class groupings for correlation detection
ASSET_CLASSES = {
    "USD_PAIRS": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"],
    "EUR_PAIRS": ["EURUSD", "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURCAD", "EURNZD"],
    "GBP_PAIRS": ["GBPUSD", "EURGBP", "GBPJPY", "GBPCHF", "GBPAUD", "GBPCAD", "GBPNZD"],
    "JPY_PAIRS": ["USDJPY", "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "CADJPY", "NZDJPY"],
    "GOLD": ["XAUUSD", "GOLD"],
    "INDICES": ["US30", "US500", "NAS100", "DE40", "UK100", "JP225"],
    "OIL": ["USOIL", "UKOIL", "XTIUSD", "XBRUSD"],
}

# Trading sessions (UTC times)
SESSIONS = {
    "asian": (0, 9),       # 00:00 - 09:00 UTC
    "london": (7, 16),     # 07:00 - 16:00 UTC
    "new_york": (13, 22),  # 13:00 - 22:00 UTC
}


def get_current_session(dt: Optional[datetime] = None) -> str:
    """Determine the current trading session based on UTC hour.

    Args:
        dt: Datetime to check. Defaults to current UTC time.

    Returns:
        Session name: 'asian', 'london', 'new_york', or 'off_hours'.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    hour = dt.hour

    # Check in priority order (overlaps favor later sessions)
    if SESSIONS["new_york"][0] <= hour < SESSIONS["new_york"][1]:
        return "new_york"
    if SESSIONS["london"][0] <= hour < SESSIONS["london"][1]:
        return "london"
    if SESSIONS["asian"][0] <= hour < SESSIONS["asian"][1]:
        return "asian"
    return "off_hours"


def get_asset_class(symbol: str) -> List[str]:
    """Return which asset classes a symbol belongs to.

    Args:
        symbol: Trading instrument symbol.

    Returns:
        List of asset class names the symbol belongs to.
    """
    classes = []
    symbol_upper = symbol.upper().replace(".", "").replace("/", "")
    for cls_name, symbols in ASSET_CLASSES.items():
        if symbol_upper in [s.upper() for s in symbols]:
            classes.append(cls_name)
    return classes


async def detect_revenge_trading(
    db: AsyncSession,
    user_id: str,
    rules: Optional[TradingRules],
) -> Optional[BehavioralAlert]:
    """Detect revenge trading: a loss was closed within the last N minutes.

    Revenge trading occurs when a trader opens a new position shortly after
    a loss, often driven by emotion rather than analysis.

    Args:
        db: Database session.
        user_id: User UUID.
        rules: User's trading rules (for min_time_between_trades).

    Returns:
        BehavioralAlert if revenge trading detected, else None.
    """
    min_minutes = rules.min_time_between_trades if rules else 10
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=min_minutes)

    result = await db.execute(
        select(Trade)
        .where(
            and_(
                Trade.user_id == user_id,
                Trade.status == TradeStatus.CLOSED,
                Trade.close_time >= cutoff,
                Trade.pnl < 0,
            )
        )
        .order_by(Trade.close_time.desc())
        .limit(1)
    )
    recent_loss = result.scalar_one_or_none()

    if recent_loss:
        minutes_ago = (datetime.now(timezone.utc) - recent_loss.close_time.replace(tzinfo=timezone.utc)).total_seconds() / 60
        return BehavioralAlert(
            flag="revenge_trading",
            severity="high",
            message=f"⚠️ Possible revenge trade: You had a loss on {recent_loss.symbol} "
                    f"({recent_loss.pnl:.2f}) just {minutes_ago:.0f} minutes ago. "
                    f"Take a break before trading again.",
            details={
                "recent_loss_symbol": recent_loss.symbol,
                "recent_loss_pnl": recent_loss.pnl,
                "minutes_since_loss": round(minutes_ago, 1),
                "min_required": min_minutes,
            },
        )
    return None


async def detect_overtrading(
    db: AsyncSession,
    user_id: str,
    rules: Optional[TradingRules],
) -> Optional[BehavioralAlert]:
    """Detect overtrading: today's trade count exceeds 2x the 30-day daily average.

    Args:
        db: Database session.
        user_id: User UUID.
        rules: User's trading rules (for max_trades_per_day).

    Returns:
        BehavioralAlert if overtrading detected, else None.
    """
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = today_start - timedelta(days=30)

    # Count today's trades
    result = await db.execute(
        select(func.count(Trade.id)).where(
            and_(
                Trade.user_id == user_id,
                Trade.open_time >= today_start,
            )
        )
    )
    today_count = result.scalar() or 0

    # Count last 30 days average
    result = await db.execute(
        select(func.count(Trade.id)).where(
            and_(
                Trade.user_id == user_id,
                Trade.open_time >= thirty_days_ago,
                Trade.open_time < today_start,
            )
        )
    )
    month_count = result.scalar() or 0
    daily_avg = month_count / 30.0 if month_count > 0 else 2  # Default avg of 2

    max_trades = rules.max_trades_per_day if rules else 5

    # Check both absolute limit and relative overtrading
    alerts = []
    if today_count >= max_trades:
        return BehavioralAlert(
            flag="overtrading",
            severity="critical",
            message=f"🛑 Overtrading: {today_count} trades today (limit: {max_trades}). "
                    f"Your 30-day daily avg is {daily_avg:.1f}. Stop trading for today.",
            details={
                "today_count": today_count,
                "max_trades": max_trades,
                "daily_avg_30d": round(daily_avg, 1),
            },
        )
    elif today_count >= daily_avg * 2 and daily_avg >= 1:
        return BehavioralAlert(
            flag="overtrading",
            severity="high",
            message=f"⚠️ Trading more than usual: {today_count} trades today vs "
                    f"your 30-day avg of {daily_avg:.1f}/day. Are these quality setups?",
            details={
                "today_count": today_count,
                "daily_avg_30d": round(daily_avg, 1),
                "threshold": round(daily_avg * 2, 1),
            },
        )
    return None


async def detect_weak_session(
    db: AsyncSession,
    user_id: str,
    rules: Optional[TradingRules],
) -> Optional[BehavioralAlert]:
    """Detect trading in a session where the user has <35% win rate.

    Args:
        db: Database session.
        user_id: User UUID.
        rules: User's trading rules (for blocked_sessions).

    Returns:
        BehavioralAlert if weak session detected, else None.
    """
    current_session = get_current_session()

    # Check if session is explicitly blocked
    if rules and rules.blocked_sessions and current_session in rules.blocked_sessions:
        return BehavioralAlert(
            flag="blocked_session",
            severity="critical",
            message=f"🛑 You're trading during the {current_session} session, "
                    f"which you've blocked in your rules.",
            details={"session": current_session, "blocked": True},
        )

    # Calculate win rate for this session over last 60 days
    sixty_days_ago = datetime.now(timezone.utc) - timedelta(days=60)
    session_start_hour, session_end_hour = SESSIONS.get(current_session, (0, 24))

    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.user_id == user_id,
                Trade.status == TradeStatus.CLOSED,
                Trade.open_time >= sixty_days_ago,
            )
        )
    )
    trades = result.scalars().all()

    # Filter by session hours
    session_trades = [
        t for t in trades
        if session_start_hour <= t.open_time.hour < session_end_hour
    ]

    if len(session_trades) >= 10:  # Need enough data
        winners = sum(1 for t in session_trades if t.pnl and t.pnl > 0)
        win_rate = winners / len(session_trades)

        if win_rate < 0.35:
            return BehavioralAlert(
                flag="weak_session",
                severity="medium",
                message=f"📊 Your win rate during the {current_session} session is only "
                        f"{win_rate*100:.0f}% ({winners}/{len(session_trades)} trades). "
                        f"Consider avoiding this session.",
                details={
                    "session": current_session,
                    "win_rate": round(win_rate, 3),
                    "total_trades": len(session_trades),
                    "winners": winners,
                },
            )
    return None


def detect_bad_rr(
    trade: Trade,
    rules: Optional[TradingRules],
) -> Optional[BehavioralAlert]:
    """Detect if the trade has a risk/reward ratio below the user's minimum.

    Args:
        trade: Trade to evaluate.
        rules: User's trading rules.

    Returns:
        BehavioralAlert if bad R:R detected, else None.
    """
    if not trade.entry_price:
        return None

    if not trade.sl or not trade.tp:
        return BehavioralAlert(
            flag="bad_rr",
            severity="high",
            message="📉 No SL/TP set — risk/reward ratio is undefined. "
                    "Always define your exit points before entering.",
            details={"rr_ratio": None, "undefined": True},
        )

    min_rr = rules.min_risk_reward if rules else 1.5

    if trade.direction == TradeDirection.BUY:
        risk = abs(trade.entry_price - trade.sl)
        reward = abs(trade.tp - trade.entry_price)
    else:
        risk = abs(trade.sl - trade.entry_price)
        reward = abs(trade.entry_price - trade.tp)

    if risk <= 0:
        return None

    rr_ratio = reward / risk

    if rr_ratio < min_rr:
        return BehavioralAlert(
            flag="bad_rr",
            severity="medium" if rr_ratio >= 1.0 else "high",
            message=f"📉 Risk/Reward ratio is {rr_ratio:.2f}:1 (your minimum: {min_rr:.1f}:1). "
                    f"Risk: {risk:.5f}, Reward: {reward:.5f}.",
            details={
                "rr_ratio": round(rr_ratio, 2),
                "min_required": min_rr,
                "risk_pips": round(risk, 5),
                "reward_pips": round(reward, 5),
            },
        )
    return None


def detect_excessive_risk(
    trade: Trade,
    rules: Optional[TradingRules],
    account_balance: float = 10000.0,
) -> Optional[BehavioralAlert]:
    """Detect if position risk exceeds the user's max risk percentage.

    Args:
        trade: Trade to evaluate.
        rules: User's trading rules.
        account_balance: Current account balance for risk calculation.

    Returns:
        BehavioralAlert if excessive risk detected, else None.
    """
    if not trade.entry_price or account_balance <= 0:
        return None

    if not trade.sl:
        return BehavioralAlert(
            flag="excessive_risk",
            severity="critical",
            message="🚨 No stop loss set — position risk is unlimited. "
                    "Set a stop loss to define your maximum loss.",
            details={"risk_percent": None, "unlimited": True},
        )

    max_risk = rules.max_risk_percent if rules else 2.0

    # Calculate risk in account currency using the same 3-tier formula as the
    # P&L fallback calculation so that all risk math is consistent.
    #
    # Tier 1 — Crypto / high-price (BTC, ETH, indices > $1 000):
    #   1 standard lot = 1 coin/unit  →  risk = price_diff × lot_size  (direct USD)
    # Tier 2 — Indices / metals / oil ($20 < price ≤ $1 000):
    #   pip_size = 0.01, pip_value ≈ $10 per standard lot
    # Tier 3 — Standard forex (price ≤ $20):
    #   pip_size = 0.0001, pip_value = $10 per standard lot
    sl_distance = abs(trade.entry_price - trade.sl)
    entry = trade.entry_price
    lot = trade.lot_size
    if entry > 1000:
        # Crypto / high-price instruments: 1 lot = 1 unit of base asset
        risk_amount = sl_distance * lot
    elif entry > 20:
        # Indices, metals, oil
        risk_amount = (sl_distance / 0.01) * 10.0 * lot
    else:
        # Standard forex pairs
        risk_amount = (sl_distance / 0.0001) * 10.0 * lot

    risk_percent = (risk_amount / account_balance) * 100

    if risk_percent > max_risk:
        return BehavioralAlert(
            flag="excessive_risk",
            severity="critical" if risk_percent > max_risk * 2 else "high",
            message=f"🚨 Position risk is {risk_percent:.1f}% of account "
                    f"(your limit: {max_risk:.1f}%). "
                    f"Risk amount: ${risk_amount:.2f} on ${account_balance:.2f} balance.",
            details={
                "risk_percent": round(risk_percent, 2),
                "max_risk_percent": max_risk,
                "risk_amount": round(risk_amount, 2),
                "account_balance": account_balance,
            },
        )
    return None


async def detect_correlation_stacking(
    db: AsyncSession,
    user_id: str,
    new_trade: Trade,
) -> Optional[BehavioralAlert]:
    """Detect correlated open positions in the same direction.

    Flags when 2+ open trades are in the same asset class and direction,
    which multiplies risk exposure.

    Args:
        db: Database session.
        user_id: User UUID.
        new_trade: The new trade being opened.

    Returns:
        BehavioralAlert if correlation stacking detected, else None.
    """
    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.user_id == user_id,
                Trade.status == TradeStatus.OPEN,
                Trade.id != new_trade.id,
            )
        )
    )
    open_trades = result.scalars().all()

    if not open_trades:
        return None

    new_classes = get_asset_class(new_trade.symbol)

    correlated = []
    for existing_trade in open_trades:
        existing_classes = get_asset_class(existing_trade.symbol)
        shared_classes = set(new_classes) & set(existing_classes)

        if shared_classes and existing_trade.direction == new_trade.direction:
            correlated.append({
                "symbol": existing_trade.symbol,
                "direction": existing_trade.direction.value if hasattr(existing_trade.direction, 'value') else str(existing_trade.direction),
                "shared_classes": list(shared_classes),
            })

    if correlated:
        symbols = [c["symbol"] for c in correlated]
        return BehavioralAlert(
            flag="correlation_stacking",
            severity="high" if len(correlated) >= 2 else "medium",
            message=f"🔗 Correlated positions: {new_trade.symbol} {new_trade.direction.value if hasattr(new_trade.direction, 'value') else new_trade.direction} "
                    f"is correlated with open trades: {', '.join(symbols)}. "
                    f"This multiplies your risk exposure.",
            details={
                "new_trade_symbol": new_trade.symbol,
                "correlated_trades": correlated,
                "total_correlated": len(correlated),
            },
        )
    return None


async def detect_news_gambling(
    news_events: List[dict],
) -> Optional[BehavioralAlert]:
    """Detect trading near high-impact news events.

    Args:
        news_events: List of upcoming news events with impact, time, currency fields.

    Returns:
        BehavioralAlert if news gambling detected, else None.
    """
    now = datetime.now(timezone.utc)
    high_impact_soon = []

    for event in news_events:
        event_time = event.get("time")
        impact = event.get("impact", "").lower()

        if impact not in ("high", "critical"):
            continue

        if isinstance(event_time, str):
            try:
                event_time = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue

        if event_time and abs((event_time - now).total_seconds()) <= 900:  # 15 min
            high_impact_soon.append(event)

    if high_impact_soon:
        event_names = [e.get("title", "Unknown") for e in high_impact_soon[:3]]
        return BehavioralAlert(
            flag="news_gambling",
            severity="high",
            message=f"📰 High-impact news within 15 minutes: {', '.join(event_names)}. "
                    f"Trading around major news is gambling, not trading.",
            details={
                "events": high_impact_soon[:5],
                "count": len(high_impact_soon),
            },
        )
    return None


async def detect_winner_cutting(
    db: AsyncSession,
    user_id: str,
) -> Optional[BehavioralAlert]:
    """Detect a pattern of cutting winners short.

    Flags when average winner duration is less than 50% of average loser duration,
    suggesting the trader exits profitable trades too early.

    Args:
        db: Database session.
        user_id: User UUID.

    Returns:
        BehavioralAlert if winner cutting detected, else None.
    """
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    result = await db.execute(
        select(Trade).where(
            and_(
                Trade.user_id == user_id,
                Trade.status == TradeStatus.CLOSED,
                Trade.close_time >= thirty_days_ago,
                Trade.duration_seconds.isnot(None),
            )
        )
    )
    trades = result.scalars().all()

    winners = [t for t in trades if t.pnl and t.pnl > 0 and t.duration_seconds]
    losers = [t for t in trades if t.pnl and t.pnl < 0 and t.duration_seconds]

    if len(winners) < 5 or len(losers) < 5:
        return None

    avg_winner_duration = sum(t.duration_seconds for t in winners) / len(winners)
    avg_loser_duration = sum(t.duration_seconds for t in losers) / len(losers)

    if avg_loser_duration <= 0:
        return None

    ratio = avg_winner_duration / avg_loser_duration

    if ratio < 0.5:
        return BehavioralAlert(
            flag="winner_cutting",
            severity="medium",
            message=f"✂️ You're cutting winners short. Average winner held "
                    f"{avg_winner_duration/60:.0f} min vs losers held {avg_loser_duration/60:.0f} min "
                    f"(ratio: {ratio:.2f}). Let your winners run!",
            details={
                "avg_winner_duration_sec": round(avg_winner_duration),
                "avg_loser_duration_sec": round(avg_loser_duration),
                "ratio": round(ratio, 3),
                "winners_count": len(winners),
                "losers_count": len(losers),
            },
        )
    return None


def detect_missing_sl_tp(
    trade: Trade,
    rules: Optional[TradingRules],
) -> Optional[BehavioralAlert]:
    """Flag trades placed without a stop loss or take profit.

    Args:
        trade: Trade to evaluate.
        rules: User's trading rules (unused but kept for consistent signature).

    Returns:
        BehavioralAlert if SL or TP is absent, else None.
    """
    missing = []
    if not trade.sl:
        missing.append("Stop Loss")
    if not trade.tp:
        missing.append("Take Profit")

    if missing:
        return BehavioralAlert(
            flag="missing_sl_tp",
            severity="critical",
            message=f"🚨 Trade has no {' or '.join(missing)} set. "
                    "This is unprotected risk — always define your exit before entering.",
            details={"missing": missing},
        )
    return None


async def run_all_checks(
    db: AsyncSession,
    user_id: str,
    trade: Trade,
    rules: Optional[TradingRules],
    news_events: Optional[List[dict]] = None,
    account_balance: float = 10000.0,
) -> List[BehavioralAlert]:
    """Run all behavioral pattern detectors on a trade.

    Args:
        db: Database session.
        user_id: User UUID.
        trade: The trade to analyze.
        rules: User's trading rules.
        news_events: Upcoming economic events.
        account_balance: Current account balance.

    Returns:
        List of BehavioralAlert instances for all detected issues.
    """
    alerts: List[BehavioralAlert] = []

    # Run all async checks
    revenge = await detect_revenge_trading(db, user_id, rules)
    if revenge:
        alerts.append(revenge)

    overtrading = await detect_overtrading(db, user_id, rules)
    if overtrading:
        alerts.append(overtrading)

    weak_session = await detect_weak_session(db, user_id, rules)
    if weak_session:
        alerts.append(weak_session)

    correlation = await detect_correlation_stacking(db, user_id, trade)
    if correlation:
        alerts.append(correlation)

    winner_cut = await detect_winner_cutting(db, user_id)
    if winner_cut:
        alerts.append(winner_cut)

    # Sync checks
    missing_sl_tp = detect_missing_sl_tp(trade, rules)
    if missing_sl_tp:
        alerts.append(missing_sl_tp)

    bad_rr = detect_bad_rr(trade, rules)
    if bad_rr:
        alerts.append(bad_rr)

    excessive_risk = detect_excessive_risk(trade, rules, account_balance)
    if excessive_risk:
        alerts.append(excessive_risk)

    # News check
    if news_events:
        news_alert = await detect_news_gambling(news_events)
        if news_alert:
            alerts.append(news_alert)

    return alerts
