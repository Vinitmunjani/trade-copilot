"""Economic calendar / news service.

Fetches upcoming economic events from free APIs and flags
high-impact events that could affect open positions.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

import httpx
import redis.asyncio as aioredis
import json

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

CACHE_TTL = 600  # 10 minutes
FOREX_FACTORY_FALLBACK_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"


async def fetch_economic_calendar(
    redis_client: Optional[aioredis.Redis] = None,
) -> list[dict]:
    """Fetch this week's economic calendar events.

    Uses a free Forex Factory JSON mirror. Falls back to cached or empty list.

    Args:
        redis_client: Optional Redis client for caching.

    Returns:
        List of event dicts with title, country, date, time, impact, forecast, previous.
    """
    cache_key = "economic_calendar"

    # Check cache first
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache read error for calendar: {e}")

    events = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(FOREX_FACTORY_FALLBACK_URL)
            response.raise_for_status()
            raw_events = response.json()

            for event in raw_events:
                parsed = {
                    "title": event.get("title", "Unknown Event"),
                    "country": event.get("country", ""),
                    "date": event.get("date", ""),
                    "time": None,
                    "impact": event.get("impact", "Low"),
                    "forecast": event.get("forecast", ""),
                    "previous": event.get("previous", ""),
                }

                # Parse date string into ISO format
                date_str = event.get("date", "")
                if date_str:
                    try:
                        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        parsed["time"] = dt.isoformat()
                    except (ValueError, TypeError):
                        parsed["time"] = date_str

                events.append(parsed)

    except Exception as e:
        logger.error(f"Failed to fetch economic calendar: {e}")
        return []

    # Cache results
    if redis_client and events:
        try:
            await redis_client.set(cache_key, json.dumps(events), ex=CACHE_TTL)
        except Exception as e:
            logger.warning(f"Redis cache write error for calendar: {e}")

    return events


async def get_upcoming_high_impact_events(
    symbol: Optional[str] = None,
    within_minutes: int = 60,
    redis_client: Optional[aioredis.Redis] = None,
) -> list[dict]:
    """Get high-impact economic events happening within the specified time window.

    Args:
        symbol: Trading symbol to filter relevant currencies (e.g., 'EURUSD' → EUR, USD).
        within_minutes: Look-ahead window in minutes.
        redis_client: Optional Redis client.

    Returns:
        List of high-impact event dicts happening soon.
    """
    events = await fetch_economic_calendar(redis_client)
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(minutes=within_minutes)

    # Extract relevant currencies from symbol
    relevant_currencies = set()
    if symbol:
        symbol_clean = symbol.upper().replace(".", "").replace("/", "")
        # Extract 3-letter currency codes
        if len(symbol_clean) >= 6:
            relevant_currencies.add(symbol_clean[:3])
            relevant_currencies.add(symbol_clean[3:6])
        # Special cases
        if symbol_clean in ("XAUUSD", "GOLD"):
            relevant_currencies.update(["USD", "XAU"])
        elif symbol_clean in ("USOIL", "XTIUSD"):
            relevant_currencies.update(["USD", "OIL"])

    upcoming = []
    for event in events:
        impact = (event.get("impact") or "").lower()
        if impact not in ("high", "critical", "holiday"):
            continue

        event_time = event.get("time")
        if not event_time:
            continue

        try:
            if isinstance(event_time, str):
                et = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
            else:
                et = event_time

            if now <= et <= cutoff:
                # Filter by currency if symbol provided
                event_country = (event.get("country") or "").upper()
                if relevant_currencies and event_country not in relevant_currencies:
                    # USD events affect everything
                    if event_country != "USD":
                        continue

                upcoming.append(event)
        except (ValueError, TypeError):
            continue

    return upcoming


async def get_news_summary(
    symbol: str,
    redis_client: Optional[aioredis.Redis] = None,
) -> dict:
    """Get a summary of news context for a symbol.

    Args:
        symbol: Trading instrument symbol.
        redis_client: Optional Redis client.

    Returns:
        Dict with upcoming events count, nearest event, and risk level.
    """
    events_1h = await get_upcoming_high_impact_events(symbol, 60, redis_client)
    events_15m = await get_upcoming_high_impact_events(symbol, 15, redis_client)

    risk_level = "low"
    if events_15m:
        risk_level = "critical"
    elif events_1h:
        risk_level = "high"

    return {
        "symbol": symbol,
        "high_impact_events_1h": len(events_1h),
        "high_impact_events_15m": len(events_15m),
        "nearest_event": events_1h[0] if events_1h else None,
        "risk_level": risk_level,
        "events": events_1h[:5],
    }
