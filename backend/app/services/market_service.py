"""Market context service.

Fetches price data, calculates technical indicators (EMA, ATR),
identifies key levels, and determines trading session info.
Caches results in Redis with 5-minute refresh.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

import numpy as np
import redis.asyncio as aioredis
from sqlalchemy import select, and_

from app.config import get_settings
from app.services.behavioral_service import get_current_session, SESSIONS

logger = logging.getLogger(__name__)
settings = get_settings()

CACHE_TTL = 300  # 5 minutes


def calculate_ema(prices: List[float], period: int) -> Optional[float]:
    """Calculate Exponential Moving Average for the given period.

    Args:
        prices: List of closing prices (oldest first).
        period: EMA period (e.g., 20, 50, 200).

    Returns:
        Current EMA value, or None if insufficient data.
    """
    if len(prices) < period:
        return None

    arr = np.array(prices, dtype=float)
    multiplier = 2 / (period + 1)
    ema = arr[0]

    for price in arr[1:]:
        ema = (price - ema) * multiplier + ema

    return round(float(ema), 5)


def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Optional[float]:
    """Calculate Average True Range.

    Args:
        highs: List of high prices.
        lows: List of low prices.
        closes: List of close prices.
        period: ATR period (default 14).

    Returns:
        Current ATR value, or None if insufficient data.
    """
    if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
        return None

    true_ranges = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return None

    # Simple ATR: average of last `period` true ranges
    atr = sum(true_ranges[-period:]) / period
    return round(float(atr), 5)


def identify_key_levels(
    highs: List[float], lows: List[float], closes: List[float], current_price: float
) -> dict:
    """Identify key support and resistance levels from recent price action.

    Uses recent swing highs/lows and round numbers.

    Args:
        highs: Recent high prices.
        lows: Recent low prices.
        closes: Recent close prices.
        current_price: Current market price.

    Returns:
        Dict with support_levels and resistance_levels lists.
    """
    all_levels = set()

    # Recent swing highs and lows
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            all_levels.add(round(highs[i], 5))
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            all_levels.add(round(lows[i], 5))

    # Round numbers (psychological levels)
    if current_price > 10:  # Indices / JPY pairs
        step = 100
    elif current_price > 1:
        step = 0.01
    else:
        step = 0.001

    base = round(current_price / step) * step
    for offset in range(-5, 6):
        all_levels.add(round(base + offset * step, 5))

    supports = sorted([l for l in all_levels if l < current_price], reverse=True)[:5]
    resistances = sorted([l for l in all_levels if l > current_price])[:5]

    return {
        "support_levels": supports,
        "resistance_levels": resistances,
    }


def determine_trend(price: float, ema20: Optional[float], ema50: Optional[float], ema200: Optional[float]) -> dict:
    """Determine trend direction based on EMA alignment.

    Args:
        price: Current price.
        ema20: 20-period EMA.
        ema50: 50-period EMA.
        ema200: 200-period EMA.

    Returns:
        Dict with trend direction and EMA states.
    """
    result = {
        "ema20_trend": "N/A",
        "ema50_trend": "N/A",
        "ema200_trend": "N/A",
        "overall": "neutral",
    }

    if ema20 is not None:
        result["ema20_trend"] = "bullish" if price > ema20 else "bearish"
    if ema50 is not None:
        result["ema50_trend"] = "bullish" if price > ema50 else "bearish"
    if ema200 is not None:
        result["ema200_trend"] = "bullish" if price > ema200 else "bearish"

    # Overall trend from EMA alignment
    bullish_count = sum(1 for v in [result["ema20_trend"], result["ema50_trend"], result["ema200_trend"]] if v == "bullish")
    bearish_count = sum(1 for v in [result["ema20_trend"], result["ema50_trend"], result["ema200_trend"]] if v == "bearish")

    if bullish_count >= 2:
        result["overall"] = "bullish"
    elif bearish_count >= 2:
        result["overall"] = "bearish"
    else:
        result["overall"] = "mixed"

    return result


async def get_market_context(
    symbol: str,
    redis_client: Optional[aioredis.Redis] = None,
    price_data: Optional[dict] = None,
) -> dict:
    """Get comprehensive market context for a symbol.

    Checks Redis cache first, then calculates from price data.

    Args:
        symbol: Trading instrument symbol.
        redis_client: Redis client for caching.
        price_data: Optional price data dict with 'highs', 'lows', 'closes', 'current_price'.

    Returns:
        Market context dictionary with trend, ATR, key levels, session info.
    """
    cache_key = f"market_context:{symbol}"

    # Check cache
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache read error: {e}")

    # Calculate from price data
    if not price_data:
        # Return minimal context if no data available
        return {
            "symbol": symbol,
            "current_price": None,
            "ema20_trend": "N/A",
            "ema50_trend": "N/A",
            "ema200_trend": "N/A",
            "overall_trend": "unknown",
            "atr": None,
            "support_levels": [],
            "resistance_levels": [],
            "session": get_current_session(),
            "daily_range_percent": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    closes = price_data.get("closes", [])
    highs = price_data.get("highs", [])
    lows = price_data.get("lows", [])
    current_price = price_data.get("current_price", closes[-1] if closes else 0)

    # Calculate indicators
    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)
    ema200 = calculate_ema(closes, 200)
    atr = calculate_atr(highs, lows, closes, 14)
    trend = determine_trend(current_price, ema20, ema50, ema200)
    levels = identify_key_levels(highs, lows, closes, current_price)

    # Daily range
    daily_range_percent = None
    if highs and lows and current_price > 0:
        today_high = highs[-1]
        today_low = lows[-1]
        if atr and atr > 0:
            daily_range_percent = round(((today_high - today_low) / atr) * 100, 1)

    context = {
        "symbol": symbol,
        "current_price": current_price,
        "ema20": ema20,
        "ema50": ema50,
        "ema200": ema200,
        "ema20_trend": trend["ema20_trend"],
        "ema50_trend": trend["ema50_trend"],
        "ema200_trend": trend["ema200_trend"],
        "overall_trend": trend["overall"],
        "atr": atr,
        "support_levels": levels["support_levels"],
        "resistance_levels": levels["resistance_levels"],
        "session": get_current_session(),
        "daily_range_percent": daily_range_percent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Cache in Redis
    if redis_client:
        try:
            await redis_client.set(cache_key, json.dumps(context), ex=CACHE_TTL)
        except Exception as e:
            logger.warning(f"Redis cache write error: {e}")

    return context


async def fetch_live_market_context(symbol: str, user_id: str) -> dict:
    """Fetch live market context for a symbol by pulling candles from MetaAPI.

    Looks up the user's active MetaAPI account, downloads 250 H1 candles and
    30 D1 candles, computes EMAs (20/50/200), ATR(14), key support/resistance
    levels and session info.  Result is cached in Redis for 5 minutes.

    Falls back to a minimal empty context rather than raising, so AI tasks
    never abort because of a missing market data dependency.

    Args:
        symbol: Trading symbol, e.g. "EURUSD" or "XAUUSD".
        user_id: User UUID string — used to look up the linked MetaAPI account.

    Returns:
        Market context dict (same schema as ``get_market_context`` output).
    """
    cache_key = f"market_context:{symbol}"

    # --- 1. Check Redis cache first ---
    try:
        from app.core.dependencies import get_redis  # local import avoids top-level circular deps
        redis_client = await get_redis()
        if redis_client:
            cached = await redis_client.get(cache_key)
            if cached:
                logger.debug(f"Market context cache hit for {symbol}")
                return json.loads(cached)
    except Exception:
        redis_client = None

    _empty = {
        "symbol": symbol,
        "current_price": None,
        "ema20": None,
        "ema50": None,
        "ema200": None,
        "ema20_trend": "N/A",
        "ema50_trend": "N/A",
        "ema200_trend": "N/A",
        "overall_trend": "unknown",
        "atr": None,
        "support_levels": [],
        "resistance_levels": [],
        "session": get_current_session(),
        "daily_range_percent": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "empty",
    }

    # --- 2. Look up the user's MetaAPI account ID ---
    metaapi_account_id: Optional[str] = None
    try:
        from app.database import async_session_factory
        from app.models.meta_account import MetaAccount

        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        async with async_session_factory() as db:
            result = await db.execute(
                select(MetaAccount).where(
                    and_(
                        MetaAccount.user_id == user_uuid,
                        MetaAccount.metaapi_account_id.isnot(None),
                    )
                ).order_by(MetaAccount.created_at.desc())
            )
            account_row = result.scalars().first()
            if account_row:
                metaapi_account_id = account_row.metaapi_account_id
    except Exception:
        logger.warning(f"Could not look up MetaAPI account for user {user_id} — skipping live candle fetch")
        return _empty

    if not metaapi_account_id:
        logger.info(f"No MetaAPI account linked for user {user_id} — skipping live candle fetch")
        return _empty

    # --- 3. Fetch candles from MetaAPI ---
    try:
        token = settings.METAAPI_TOKEN
        if not token:
            logger.warning("METAAPI_TOKEN not set — cannot fetch live candles")
            return _empty

        from metaapi_cloud_sdk import MetaApi  # noqa: lazy import
        api = MetaApi(token)
        account = await api.metatrader_account_api.get_account(metaapi_account_id)

        # Fetch 250 H1 candles (enough for EMA-200) and 30 D1 candles (ATR + daily range)
        h1_candles_raw = await account.get_historical_candles(symbol, "1h", limit=250)
        d1_candles_raw = await account.get_historical_candles(symbol, "1d", limit=30)

        # Sort oldest-first for EMA calculation
        def _sort_candles(candles):
            return sorted(candles, key=lambda c: c.get("time") or c.get("brokerTime") or "")

        h1_candles = _sort_candles(h1_candles_raw) if h1_candles_raw else []
        d1_candles = _sort_candles(d1_candles_raw) if d1_candles_raw else []

        if not h1_candles:
            logger.warning(f"MetaAPI returned no H1 candles for {symbol}")
            return _empty

        # Extract OHLC arrays
        h1_closes = [float(c.get("close", 0)) for c in h1_candles]
        h1_highs  = [float(c.get("high",  0)) for c in h1_candles]
        h1_lows   = [float(c.get("low",   0)) for c in h1_candles]

        current_price = h1_closes[-1] if h1_closes else 0

        # D1 for ATR — fall back to H1 if not available
        if d1_candles and len(d1_candles) >= 15:
            d_closes = [float(c.get("close", 0)) for c in d1_candles]
            d_highs  = [float(c.get("high",  0)) for c in d1_candles]
            d_lows   = [float(c.get("low",   0)) for c in d1_candles]
        else:
            d_closes, d_highs, d_lows = h1_closes, h1_highs, h1_lows

        # Compute indicators
        ema20  = calculate_ema(h1_closes, 20)
        ema50  = calculate_ema(h1_closes, 50)
        ema200 = calculate_ema(h1_closes, 200)
        atr    = calculate_atr(d_highs, d_lows, d_closes, 14)
        trend  = determine_trend(current_price, ema20, ema50, ema200)
        levels = identify_key_levels(h1_highs, h1_lows, h1_closes, current_price)

        # Daily range
        daily_range_percent = None
        if d1_candles:
            today = d1_candles[-1]
            today_high = float(today.get("high", 0))
            today_low  = float(today.get("low",  0))
            if atr and atr > 0 and today_high and today_low:
                daily_range_percent = round(((today_high - today_low) / atr) * 100, 1)

        context: Dict[str, Any] = {
            "symbol": symbol,
            "current_price": current_price,
            "ema20": ema20,
            "ema50": ema50,
            "ema200": ema200,
            "ema20_trend": trend["ema20_trend"],
            "ema50_trend": trend["ema50_trend"],
            "ema200_trend": trend["ema200_trend"],
            "overall_trend": trend["overall"],
            "atr": atr,
            "support_levels": levels["support_levels"],
            "resistance_levels": levels["resistance_levels"],
            "session": get_current_session(),
            "daily_range_percent": daily_range_percent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "metaapi_live",
        }

        logger.info(
            f"Live market context for {symbol}: price={current_price}, "
            f"trend={trend['overall']}, ema20={ema20}, atr={atr}"
        )

        # --- 4. Cache result ---
        try:
            if redis_client:
                await redis_client.set(cache_key, json.dumps(context), ex=CACHE_TTL)
        except Exception:
            pass

        return context

    except Exception:
        logger.exception(f"Failed to fetch live market context for {symbol} — returning empty context")
        return _empty
