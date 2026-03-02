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


def calculate_fibonacci_pivot_levels(
    prev_high: float, prev_low: float, prev_close: float
) -> Optional[dict]:
    """Calculate Fibonacci pivot levels using the previous period's OHLC.

    Uses the standard Fibonacci pivot formula:
        Pivot (P) = (H + L + C) / 3
        R1/S1 = P ± 0.382 × (H − L)
        R2/S2 = P ± 0.618 × (H − L)
        R3/S3 = P ± 1.000 × (H − L)

    Args:
        prev_high:  Previous period's high price.
        prev_low:   Previous period's low price.
        prev_close: Previous period's close price.

    Returns:
        Dict with keys: pivot, r1, r2, r3, s1, s2, s3, or None if inputs are invalid.
    """
    if not (prev_high and prev_low and prev_close) or prev_high <= prev_low:
        return None

    rng = prev_high - prev_low
    pivot = round((prev_high + prev_low + prev_close) / 3, 5)

    return {
        "pivot": pivot,
        "r1": round(pivot + 0.382 * rng, 5),
        "r2": round(pivot + 0.618 * rng, 5),
        "r3": round(pivot + 1.000 * rng, 5),
        "s1": round(pivot - 0.382 * rng, 5),
        "s2": round(pivot - 0.618 * rng, 5),
        "s3": round(pivot - 1.000 * rng, 5),
    }


def _ema_series(prices: List[float], period: int) -> List[float]:
    """Return the full EMA series (oldest-first) for a list of prices.

    Args:
        prices: Close prices, oldest first.
        period: EMA period.

    Returns:
        List of EMA values, same length as prices (first ``period-1`` values
        will be bootstrapped from the seed value).
    """
    if len(prices) < period:
        return []
    arr = np.array(prices, dtype=float)
    multiplier = 2 / (period + 1)
    ema = arr[0]
    result: List[float] = [ema]
    for price in arr[1:]:
        ema = (price - ema) * multiplier + ema
        result.append(ema)
    return result


def calculate_rsi(closes: List[float], period: int = 14) -> dict:
    """Calculate RSI(14) and return value with overbought/oversold/neutral label.

    Args:
        closes: Close prices, oldest first.
        period: RSI period (default 14).

    Returns:
        Dict with ``rsi`` (float or None) and ``rsi_state`` string.
    """
    if len(closes) < period + 1:
        return {"rsi": None, "rsi_state": "N/A"}

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [abs(min(d, 0.0)) for d in deltas]

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = round(100.0 - (100.0 / (1.0 + rs)), 2)

    if rsi >= 70:
        state = "overbought"
    elif rsi <= 30:
        state = "oversold"
    else:
        state = "neutral"

    return {"rsi": rsi, "rsi_state": state}


def calculate_macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """Calculate MACD line, signal line, histogram and detect recent crossover.

    Args:
        closes: Close prices, oldest first.
        fast: Fast EMA period (default 12).
        slow: Slow EMA period (default 26).
        signal: Signal EMA period (default 9).

    Returns:
        Dict with ``macd_line``, ``signal_line``, ``histogram``, ``macd_cross``.
    """
    _empty = {"macd_line": None, "signal_line": None, "histogram": None, "macd_cross": "N/A"}
    if len(closes) < slow + signal:
        return _empty

    ema_fast = _ema_series(closes, fast)
    ema_slow = _ema_series(closes, slow)

    # Align: ema_slow starts at index slow-1 in the original series,
    # ema_fast starts at index fast-1; offset = slow - fast
    offset = slow - fast
    if offset >= len(ema_fast):
        return _empty
    macd_series = [f - s for f, s in zip(ema_fast[offset:], ema_slow)]

    if len(macd_series) < signal:
        return _empty

    signal_series = _ema_series(macd_series, signal)
    if not signal_series:
        return _empty

    macd_val    = round(macd_series[-1], 6)
    signal_val  = round(signal_series[-1], 6)
    hist_val    = round(macd_val - signal_val, 6)

    # Crossover detection (last two bars)
    cross = "none"
    if len(macd_series) >= 2 and len(signal_series) >= 2:
        prev_diff = macd_series[-2] - signal_series[-2]
        curr_diff = macd_series[-1] - signal_series[-1]
        if prev_diff < 0 and curr_diff >= 0:
            cross = "bullish_cross"
        elif prev_diff > 0 and curr_diff <= 0:
            cross = "bearish_cross"

    return {
        "macd_line": macd_val,
        "signal_line": signal_val,
        "histogram": hist_val,
        "macd_cross": cross,
    }


def calculate_bollinger_bands(
    closes: List[float], period: int = 20, std_multiplier: float = 2.0
) -> dict:
    """Calculate Bollinger Bands and derived metrics.

    Args:
        closes: Close prices, oldest first.
        period: Band period (default 20).
        std_multiplier: Standard deviation multiplier (default 2).

    Returns:
        Dict with ``bb_upper``, ``bb_lower``, ``bb_middle``, ``bb_percent_b``
        (0 = at lower band, 1 = at upper band), ``bb_squeeze`` (bool).
    """
    _empty_bb = {
        "bb_upper": None, "bb_lower": None, "bb_middle": None,
        "bb_percent_b": None, "bb_squeeze": None,
    }
    if len(closes) < period:
        return _empty_bb

    window = closes[-period:]
    mean    = sum(window) / period
    variance = sum((x - mean) ** 2 for x in window) / period
    std      = variance ** 0.5

    bb_upper  = round(mean + std_multiplier * std, 5)
    bb_lower  = round(mean - std_multiplier * std, 5)
    bb_middle = round(mean, 5)
    band_width = bb_upper - bb_lower

    bb_percent_b = None
    if band_width > 0:
        bb_percent_b = round((closes[-1] - bb_lower) / band_width, 3)

    # Squeeze: band width less than 1% of price → tight consolidation
    bb_squeeze = bool(mean > 0 and band_width / mean < 0.01)

    return {
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "bb_middle": bb_middle,
        "bb_percent_b": bb_percent_b,
        "bb_squeeze": bb_squeeze,
    }


def calculate_atr_percentile(atr_history: List[float]) -> dict:
    """Calculate current ATR's percentile rank vs. its own history.

    Args:
        atr_history: List of ATR readings over time (current is the last element).

    Returns:
        Dict with ``atr_percentile`` (0–100) and ``volatility_regime``
        (``"low"`` / ``"normal"`` / ``"high"`` / ``"unknown"``).
    """
    if not atr_history or len(atr_history) < 2:
        return {"atr_percentile": None, "volatility_regime": "unknown"}

    current = atr_history[-1]
    history = atr_history[:-1]
    rank = round(sum(1 for v in history if v <= current) / len(history) * 100, 1)

    if rank >= 75:
        regime = "high"
    elif rank <= 25:
        regime = "low"
    else:
        regime = "normal"

    return {"atr_percentile": rank, "volatility_regime": regime}


def detect_candle_pattern(
    opens: List[float], highs: List[float], lows: List[float], closes: List[float]
) -> str:
    """Detect the most significant single or two-candle pattern on the last bar.

    Checks (in priority order): doji, pin bars, inside bar, engulfing, strong candle.

    Args:
        opens: Open prices.
        highs: High prices.
        lows: Low prices.
        closes: Close prices.

    Returns:
        Pattern name string, e.g. ``"bullish_pin_bar"``, or ``"none"``.
    """
    if len(closes) < 2:
        return "none"

    o, h, l, c              = opens[-1],  highs[-1],  lows[-1],  closes[-1]
    prev_o, prev_h, prev_l, prev_c = opens[-2], highs[-2], lows[-2], closes[-2]

    body        = abs(c - o)
    total_range = h - l if h > l else 1e-10
    upper_wick  = h - max(o, c)
    lower_wick  = min(o, c) - l

    # Doji: body < 10% of range
    if body / total_range < 0.1:
        return "doji"

    # Bullish pin bar: long lower wick (>60%), small body near top
    if lower_wick / total_range > 0.6 and body / total_range < 0.25:
        return "bullish_pin_bar"

    # Bearish pin bar: long upper wick (>60%), small body near bottom
    if upper_wick / total_range > 0.6 and body / total_range < 0.25:
        return "bearish_pin_bar"

    # Inside bar: current candle completely inside previous
    if h <= prev_h and l >= prev_l:
        return "inside_bar"

    # Bullish engulfing: bullish candle engulfs previous bearish candle
    if c > o and prev_c < prev_o and c > prev_o and o < prev_c:
        return "bullish_engulfing"

    # Bearish engulfing: bearish candle engulfs previous bullish candle
    if c < o and prev_c > prev_o and c < prev_o and o > prev_c:
        return "bearish_engulfing"

    # Strong bullish: body > 70% of range, closes near high
    if c > o and body / total_range > 0.7 and (h - c) / total_range < 0.1:
        return "strong_bullish"

    # Strong bearish: body > 70% of range, closes near low
    if c < o and body / total_range > 0.7 and (c - l) / total_range < 0.1:
        return "strong_bearish"

    return "none"


def calculate_price_distances(
    current_price: float,
    support_levels: List[float],
    resistance_levels: List[float],
    atr: Optional[float],
) -> dict:
    """Express distance from price to nearest key level in ATR units.

    Args:
        current_price: Current market price.
        support_levels: Support levels sorted nearest-first.
        resistance_levels: Resistance levels sorted nearest-first.
        atr: Current ATR value.

    Returns:
        Dict with ``distance_to_support_atr`` and ``distance_to_resistance_atr``.
    """
    result: dict = {"distance_to_support_atr": None, "distance_to_resistance_atr": None}
    if not atr or atr <= 0:
        return result
    if support_levels:
        result["distance_to_support_atr"] = round(abs(current_price - support_levels[0]) / atr, 2)
    if resistance_levels:
        result["distance_to_resistance_atr"] = round(abs(resistance_levels[0] - current_price) / atr, 2)
    return result


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
            "atr_percentile": None,
            "volatility_regime": "unknown",
            "support_levels": [],
            "resistance_levels": [],
            "distance_to_support_atr": None,
            "distance_to_resistance_atr": None,
            "fibonacci_pivots": None,
            "rsi": None,
            "rsi_state": "N/A",
            "macd_line": None,
            "signal_line": None,
            "histogram": None,
            "macd_cross": "N/A",
            "bb_upper": None,
            "bb_lower": None,
            "bb_middle": None,
            "bb_percent_b": None,
            "bb_squeeze": None,
            "candle_pattern": "none",
            "session": get_current_session(),
            "daily_range_percent": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    closes = price_data.get("closes", [])
    highs  = price_data.get("highs",  [])
    lows   = price_data.get("lows",   [])
    opens  = price_data.get("opens",  [])
    current_price = price_data.get("current_price", closes[-1] if closes else 0)

    # Core indicators
    ema20  = calculate_ema(closes, 20)
    ema50  = calculate_ema(closes, 50)
    ema200 = calculate_ema(closes, 200)
    atr    = calculate_atr(highs, lows, closes, 14)
    trend  = determine_trend(current_price, ema20, ema50, ema200)
    levels = identify_key_levels(highs, lows, closes, current_price)

    # Fibonacci pivot levels (use second-to-last candle's H/L/C as previous period)
    fib_pivots = None
    if len(highs) >= 2 and len(lows) >= 2 and len(closes) >= 2:
        fib_pivots = calculate_fibonacci_pivot_levels(highs[-2], lows[-2], closes[-2])
    elif highs and lows and closes:
        fib_pivots = calculate_fibonacci_pivot_levels(highs[-1], lows[-1], closes[-1])

    # Momentum & volatility
    rsi_data  = calculate_rsi(closes)
    macd_data = calculate_macd(closes)
    bb_data   = calculate_bollinger_bands(closes)

    # ATR percentile (rolling ATR values from available data)
    atr_history: List[float] = []
    for i in range(14, len(closes)):
        sample = calculate_atr(highs[:i + 1], lows[:i + 1], closes[:i + 1], 14)
        if sample:
            atr_history.append(sample)
    atr_perc_data = calculate_atr_percentile(atr_history)

    # Candle pattern on last bar
    candle_pattern = detect_candle_pattern(opens, highs, lows, closes) if opens else "none"

    # Price distances (ATR units) to nearest levels
    dist_data = calculate_price_distances(
        current_price, levels["support_levels"], levels["resistance_levels"], atr
    )

    # Daily range
    daily_range_percent = None
    if highs and lows and current_price > 0:
        today_high = highs[-1]
        today_low  = lows[-1]
        if atr and atr > 0:
            daily_range_percent = round(((today_high - today_low) / atr) * 100, 1)

    context = {
        "symbol":            symbol,
        "current_price":     current_price,
        "ema20":             ema20,
        "ema50":             ema50,
        "ema200":            ema200,
        "ema20_trend":       trend["ema20_trend"],
        "ema50_trend":       trend["ema50_trend"],
        "ema200_trend":      trend["ema200_trend"],
        "overall_trend":     trend["overall"],
        "atr":               atr,
        "atr_percentile":    atr_perc_data["atr_percentile"],
        "volatility_regime": atr_perc_data["volatility_regime"],
        "support_levels":    levels["support_levels"],
        "resistance_levels": levels["resistance_levels"],
        "distance_to_support_atr":    dist_data["distance_to_support_atr"],
        "distance_to_resistance_atr": dist_data["distance_to_resistance_atr"],
        "fibonacci_pivots":  fib_pivots,
        "rsi":               rsi_data["rsi"],
        "rsi_state":         rsi_data["rsi_state"],
        "macd_line":         macd_data["macd_line"],
        "signal_line":       macd_data["signal_line"],
        "histogram":         macd_data["histogram"],
        "macd_cross":        macd_data["macd_cross"],
        "bb_upper":          bb_data["bb_upper"],
        "bb_lower":          bb_data["bb_lower"],
        "bb_middle":         bb_data["bb_middle"],
        "bb_percent_b":      bb_data["bb_percent_b"],
        "bb_squeeze":        bb_data["bb_squeeze"],
        "candle_pattern":    candle_pattern,
        "session":           get_current_session(),
        "daily_range_percent": daily_range_percent,
        "timestamp":         datetime.now(timezone.utc).isoformat(),
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

    _empty: Dict[str, Any] = {
        "symbol":            symbol,
        "current_price":     None,
        "ema20":             None,
        "ema50":             None,
        "ema200":            None,
        "ema20_trend":       "N/A",
        "ema50_trend":       "N/A",
        "ema200_trend":      "N/A",
        "overall_trend":     "unknown",
        "htf_trend":         "unknown",
        "atr":               None,
        "atr_percentile":    None,
        "volatility_regime": "unknown",
        "support_levels":    [],
        "resistance_levels": [],
        "distance_to_support_atr":    None,
        "distance_to_resistance_atr": None,
        "fibonacci_pivots":  None,
        "rsi":               None,
        "rsi_state":         "N/A",
        "macd_line":         None,
        "signal_line":       None,
        "histogram":         None,
        "macd_cross":        "N/A",
        "bb_upper":          None,
        "bb_lower":          None,
        "bb_middle":         None,
        "bb_percent_b":      None,
        "bb_squeeze":        None,
        "candle_pattern":    "none",
        "prev_day_high":     None,
        "prev_day_low":      None,
        "prev_day_close":    None,
        "news_risk_level":   "unknown",
        "news_events_1h":    0,
        "nearest_news_event": None,
        "session":           get_current_session(),
        "daily_range_percent": None,
        "timestamp":         datetime.now(timezone.utc).isoformat(),
        "source":            "empty",
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
        h1_opens  = [float(c.get("open",  0)) for c in h1_candles]

        current_price = h1_closes[-1] if h1_closes else 0

        # D1 for ATR & HTF — fall back to H1 if not available
        if d1_candles and len(d1_candles) >= 15:
            d_closes = [float(c.get("close", 0)) for c in d1_candles]
            d_highs  = [float(c.get("high",  0)) for c in d1_candles]
            d_lows   = [float(c.get("low",   0)) for c in d1_candles]
        else:
            d_closes, d_highs, d_lows = h1_closes, h1_highs, h1_lows

        # --- H1 indicators ---
        ema20  = calculate_ema(h1_closes, 20)
        ema50  = calculate_ema(h1_closes, 50)
        ema200 = calculate_ema(h1_closes, 200)
        atr    = calculate_atr(d_highs, d_lows, d_closes, 14)
        trend  = determine_trend(current_price, ema20, ema50, ema200)
        levels = identify_key_levels(h1_highs, h1_lows, h1_closes, current_price)

        # Fibonacci pivot levels — use previous day's OHLC
        fib_pivots = None
        if len(d1_candles) >= 2:
            prev_day = d1_candles[-2]
            fib_pivots = calculate_fibonacci_pivot_levels(
                float(prev_day.get("high",  0)),
                float(prev_day.get("low",   0)),
                float(prev_day.get("close", 0)),
            )
        elif d1_candles:
            prev_day = d1_candles[-1]
            fib_pivots = calculate_fibonacci_pivot_levels(
                float(prev_day.get("high",  0)),
                float(prev_day.get("low",   0)),
                float(prev_day.get("close", 0)),
            )

        # Momentum & volatility (H1)
        rsi_data  = calculate_rsi(h1_closes)
        macd_data = calculate_macd(h1_closes)
        bb_data   = calculate_bollinger_bands(h1_closes)

        # ATR percentile from rolling D1 ATR history
        d1_atr_history: List[float] = []
        for i in range(14, len(d_closes)):
            sample = calculate_atr(d_highs[:i + 1], d_lows[:i + 1], d_closes[:i + 1], 14)
            if sample:
                d1_atr_history.append(sample)
        atr_perc_data = calculate_atr_percentile(d1_atr_history)

        # Candle pattern on last H1 bar
        candle_pattern = detect_candle_pattern(h1_opens, h1_highs, h1_lows, h1_closes)

        # Price distances (ATR units) to nearest levels
        dist_data = calculate_price_distances(
            current_price, levels["support_levels"], levels["resistance_levels"], atr
        )

        # Higher-timeframe (D1) trend — EMA20 & EMA50 on daily closes
        d1_ema20 = calculate_ema(d_closes, 20)
        d1_ema50 = calculate_ema(d_closes, 50)
        d1_trend = determine_trend(current_price, d1_ema20, d1_ema50, None)
        htf_trend = d1_trend["overall"]

        # Previous day OHLC (institutional levels)
        prev_day_high  = None
        prev_day_low   = None
        prev_day_close = None
        if len(d1_candles) >= 2:
            pd = d1_candles[-2]
            prev_day_high  = float(pd.get("high",  0)) or None
            prev_day_low   = float(pd.get("low",   0)) or None
            prev_day_close = float(pd.get("close", 0)) or None

        # Daily range
        daily_range_percent = None
        if d1_candles:
            today      = d1_candles[-1]
            today_high = float(today.get("high", 0))
            today_low  = float(today.get("low",  0))
            if atr and atr > 0 and today_high and today_low:
                daily_range_percent = round(((today_high - today_low) / atr) * 100, 1)

        # News risk
        news_risk_level   = "unknown"
        news_events_1h    = 0
        nearest_news_event = None
        try:
            from app.services.news_service import get_news_summary  # local import
            from app.core.dependencies import get_redis as _get_redis
            _rc = await _get_redis()
            news_summary = await get_news_summary(symbol, _rc)
            news_risk_level    = news_summary.get("risk_level", "unknown")
            news_events_1h     = news_summary.get("high_impact_events_1h", 0)
            nearest_event_obj  = news_summary.get("nearest_event")
            if nearest_event_obj:
                nearest_news_event = (
                    f"{nearest_event_obj.get('title', 'Event')} "
                    f"({nearest_event_obj.get('country', '')} @ {nearest_event_obj.get('time', 'N/A')})"
                )
        except Exception:
            pass  # news is best-effort; never block analysis

        context: Dict[str, Any] = {
            "symbol":            symbol,
            "current_price":     current_price,
            "ema20":             ema20,
            "ema50":             ema50,
            "ema200":            ema200,
            "ema20_trend":       trend["ema20_trend"],
            "ema50_trend":       trend["ema50_trend"],
            "ema200_trend":      trend["ema200_trend"],
            "overall_trend":     trend["overall"],
            "htf_trend":         htf_trend,
            "atr":               atr,
            "atr_percentile":    atr_perc_data["atr_percentile"],
            "volatility_regime": atr_perc_data["volatility_regime"],
            "support_levels":    levels["support_levels"],
            "resistance_levels": levels["resistance_levels"],
            "distance_to_support_atr":    dist_data["distance_to_support_atr"],
            "distance_to_resistance_atr": dist_data["distance_to_resistance_atr"],
            "fibonacci_pivots":  fib_pivots,
            "rsi":               rsi_data["rsi"],
            "rsi_state":         rsi_data["rsi_state"],
            "macd_line":         macd_data["macd_line"],
            "signal_line":       macd_data["signal_line"],
            "histogram":         macd_data["histogram"],
            "macd_cross":        macd_data["macd_cross"],
            "bb_upper":          bb_data["bb_upper"],
            "bb_lower":          bb_data["bb_lower"],
            "bb_middle":         bb_data["bb_middle"],
            "bb_percent_b":      bb_data["bb_percent_b"],
            "bb_squeeze":        bb_data["bb_squeeze"],
            "candle_pattern":    candle_pattern,
            "prev_day_high":     prev_day_high,
            "prev_day_low":      prev_day_low,
            "prev_day_close":    prev_day_close,
            "news_risk_level":   news_risk_level,
            "news_events_1h":    news_events_1h,
            "nearest_news_event": nearest_news_event,
            "session":           get_current_session(),
            "daily_range_percent": daily_range_percent,
            "timestamp":         datetime.now(timezone.utc).isoformat(),
            "source":            "metaapi_live",
        }

        logger.info(
            f"Live market context for {symbol}: price={current_price}, "
            f"trend={trend['overall']}, htf={htf_trend}, rsi={rsi_data['rsi']}, "
            f"macd_cross={macd_data['macd_cross']}, news={news_risk_level}, atr={atr}"
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
