"""Script to demonstrate WebSocket streaming and simulate trades.

This script will:
1. Ensure the SQLite database has a user trader@example.com.
2. Create a JWT access token for that user.
3. Connect to the WebSocket endpoint and print incoming events.
4. Periodically hit the /dev/simulate-trade endpoint to generate trade events.

Usage: python stream_test.py
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import select

import httpx
import websockets

from app.config import get_settings
from app.core.security import create_access_token, hash_password
from app.database import async_session_factory, init_db
from app.models.user import User
from app.models.meta_account import MetaAccount
from app.models.trade import Trade, TradeStatus

settings = get_settings()
BACKEND_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/ws/trades"  # include api prefix


async def ensure_user():
    """Make sure user exists and return User object."""
    await init_db()  # create tables if needed
    async with async_session_factory() as db:
        result = await db.execute(
            select(User).where(User.email == "trader@example.com")
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email="trader@example.com",
                hashed_password=hash_password("password"),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user


def get_token(user_id: str) -> str:
    payload = {"sub": user_id}
    return create_access_token(payload)


async def ws_listener(token: str):
    url = f"{WS_URL}?token={token}"
    print("Connecting to websocket", url)
    # connect without extra headers
    async with websockets.connect(url) as ws:
        try:
            async for msg in ws:
                print("WS msg ->", msg)
        except Exception as e:
            print("WebSocket error", e)


async def simulate_trades(token: str):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        for i in range(5):
            payload = {
                "symbol": "EURUSD",
                "direction": "BUY" if i % 2 == 0 else "SELL",
                "entry_price": 1.1000 + i * 0.001,
                "sl": 1.0950,
                "tp": 1.1200,
                "lot_size": 0.1,
                "close_after_seconds": 3,
            }
            resp = await client.post(f"{BACKEND_URL}/dev/simulate-trade", json=payload, headers=headers)
            print("simulate response", resp.status_code, resp.text)
            await asyncio.sleep(4)


async def main():
    user = await ensure_user()
    token = get_token(str(user.id))
    print("Generated token", token)

    # run websocket and simulator in parallel
    await asyncio.gather(
        ws_listener(token),
        simulate_trades(token),
    )


if __name__ == "__main__":
    asyncio.run(main())
