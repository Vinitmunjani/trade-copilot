"""Account routes — MetaAPI connection management and trade simulation."""

import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user import AccountConnect, AccountStatus
from app.schemas.trade import SimulateTradeRequest, TradeResponse
from app.services.metaapi_service import metaapi_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Account"])


@router.post("/account/connect")
async def connect_account(
    payload: AccountConnect,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect a MetaAPI broker account.

    Stores the MetaAPI token and account ID on the user record,
    then initiates the MetaAPI connection for real-time trade monitoring.
    """
    # Save credentials to user
    current_user.metaapi_token = payload.metaapi_token
    current_user.metaapi_account_id = payload.account_id
    await db.flush()

    # Initiate connection
    result = await metaapi_service.connect(current_user)

    return {
        "message": "Account connection initiated",
        "account_id": payload.account_id,
        **result,
    }


@router.get("/account/status", response_model=AccountStatus)
async def get_account_status(
    current_user: User = Depends(get_current_user),
):
    """Get the current MetaAPI connection status."""
    status_info = await metaapi_service.get_status(current_user)

    return AccountStatus(
        connected=status_info.get("connected", False),
        account_id=status_info.get("account_id"),
        connection_status=status_info.get("status"),
        broker=status_info.get("broker"),
        server=status_info.get("server"),
    )


@router.delete("/account/disconnect")
async def disconnect_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect the MetaAPI broker account.

    Stops the trade event listener and cleans up the connection.
    Does not remove stored credentials (user can reconnect later).
    """
    result = await metaapi_service.disconnect(current_user)

    return {
        "message": "Account disconnected",
        **result,
    }


@router.post("/dev/simulate-trade", response_model=TradeResponse)
async def simulate_trade(
    payload: SimulateTradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Simulate a trade for development/testing.

    Creates a realistic fake trade event that triggers the same pipeline
    as a real MetaAPI trade event:
    1. Creates trade record in DB
    2. Runs behavioral analysis (revenge trading, overtrading, etc.)
    3. Runs AI pre-trade scoring
    4. Broadcasts via WebSocket

    If close_after_seconds is set, schedules an auto-close with a random
    exit price that simulates a realistic outcome.
    """
    user_id = str(current_user.id)

    trade_data = {
        "symbol": payload.symbol.upper(),
        "direction": payload.direction.upper(),
        "entry_price": payload.entry_price,
        "sl": payload.sl,
        "tp": payload.tp,
        "lot_size": payload.lot_size,
    }

    # Open the trade via the same pipeline as real trades
    trade = await metaapi_service.simulate_trade_open(user_id, trade_data)

    # Schedule auto-close if requested
    if payload.close_after_seconds is not None and payload.close_after_seconds > 0:
        async def auto_close():
            await asyncio.sleep(payload.close_after_seconds)
            # Generate a realistic exit price
            entry = payload.entry_price
            sl = payload.sl
            tp = payload.tp

            # Random outcome: 55% chance of hitting TP, 35% SL, 10% partial
            outcome = random.random()
            if tp and outcome < 0.55:
                # Winner — exit at or near TP
                noise = random.uniform(-0.0005, 0.0005)
                exit_price = tp + noise
            elif sl and outcome < 0.90:
                # Loser — exit at or near SL
                noise = random.uniform(-0.0005, 0.0005)
                exit_price = sl + noise
            else:
                # Partial — exit somewhere between entry and TP/SL
                if payload.direction.upper() == "BUY":
                    low = sl or (entry - 0.005)
                    high = tp or (entry + 0.005)
                else:
                    low = tp or (entry - 0.005)
                    high = sl or (entry + 0.005)
                exit_price = random.uniform(low, high)

            exit_price = round(exit_price, 5)
            await metaapi_service.simulate_trade_close(user_id, str(trade.id), exit_price)
            logger.info(f"Auto-closed simulated trade {trade.id} at {exit_price}")

        asyncio.create_task(auto_close())
        logger.info(
            f"Simulated trade {trade.id} will auto-close in {payload.close_after_seconds}s"
        )

    return TradeResponse.model_validate(trade)
