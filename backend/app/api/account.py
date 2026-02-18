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
from app.schemas.user import (
    AccountConnect,
    AccountStatus,
    TradingAccountConnect,
    TradingAccountResponse,
)
from app.schemas.trade import SimulateTradeRequest, TradeResponse
from app.services.metaapi_service import metaapi_service
from app.services.metaapi_provisioning import metaapi_provisioning, MetaApiProvisioningError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Account"])


@router.post("/account/connect", response_model=TradingAccountResponse)
async def connect_account(
    payload: TradingAccountConnect,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect a trading account using MT4/MT5 broker credentials.

    Creates a MetaAPI cloud account from the provided credentials,
    waits for deployment, then initiates real-time trade monitoring.
    The MT password is NOT stored — it is only used for MetaAPI provisioning.
    """
    # Validate platform
    platform = payload.platform.lower()
    if platform not in ("mt4", "mt5"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Platform must be 'mt4' or 'mt5'",
        )

    try:
        # Step 1: Create MetaAPI account from broker credentials
        logger.info(
            f"Provisioning MetaAPI account for user {current_user.id}: "
            f"login={payload.login}, server={payload.server}, platform={platform}"
        )
        account_id = await metaapi_provisioning.create_account(
            login=payload.login,
            password=payload.password,
            server=payload.server,
            platform=platform,
        )

        # Step 2: Store account info on user (password is NOT stored)
        current_user.metaapi_account_id = account_id
        current_user.mt_login = payload.login
        current_user.mt_server = payload.server
        current_user.mt_platform = platform
        await db.flush()
        await db.commit()

        # Step 3: Wait for deployment (non-blocking with timeout)
        try:
            deployed = await metaapi_provisioning.wait_for_deployment(
                account_id, timeout=90
            )
            if not deployed:
                logger.warning(
                    f"Account {account_id} deployment timed out but may still be deploying"
                )
        except MetaApiProvisioningError as e:
            logger.error(f"Deployment failed: {e.message}")
            return TradingAccountResponse(
                connected=False,
                account_id=account_id,
                login=payload.login,
                server=payload.server,
                platform=platform,
                connection_status="deployment_failed",
                message=f"Account created but deployment failed: {e.message}",
            )

        # Step 4: Initiate MetaAPI connection for live data
        result = await metaapi_service.connect(current_user)

        return TradingAccountResponse(
            connected=result.get("connected", False),
            account_id=account_id,
            login=payload.login,
            server=payload.server,
            platform=platform,
            connection_status=result.get("status", "unknown"),
            message="Trading account connected successfully"
            if result.get("connected")
            else f"Account created, connection status: {result.get('status', 'pending')}",
        )

    except MetaApiProvisioningError as e:
        logger.error(f"MetaAPI provisioning failed: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=e.message,
        )
    except Exception as e:
        logger.error(f"Unexpected error connecting account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while connecting your trading account.",
        )


@router.get("/account/info", response_model=TradingAccountResponse)
async def get_account_info(
    current_user: User = Depends(get_current_user),
):
    """Get trading account connection info.

    Returns the connected account details including login, server,
    platform, and real-time connection status.
    """
    if not current_user.metaapi_account_id:
        return TradingAccountResponse(
            connected=False,
            connection_status="not_configured",
            message="No trading account connected",
        )

    # Get live connection status
    status_info = await metaapi_service.get_status(current_user)

    return TradingAccountResponse(
        connected=status_info.get("connected", False),
        account_id=current_user.metaapi_account_id,
        login=current_user.mt_login,
        server=current_user.mt_server,
        platform=current_user.mt_platform,
        connection_status=status_info.get("status", "unknown"),
        message=None,
    )


@router.get("/account/status", response_model=AccountStatus)
async def get_account_status(
    current_user: User = Depends(get_current_user),
):
    """Get the current MetaAPI connection status."""
    status_info = await metaapi_service.get_status(current_user)

    return AccountStatus(
        connected=status_info.get("connected", False),
        account_id=status_info.get("account_id"),
        login=current_user.mt_login,
        server=current_user.mt_server,
        platform=current_user.mt_platform,
        connection_status=status_info.get("status"),
        broker=status_info.get("broker"),
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
