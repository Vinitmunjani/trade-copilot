import asyncio
import logging
import os
import random
import uuid
import traceback
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user import (
    AccountStatus,
    TradingAccountConnect,
    TradingAccountResponse,
    AutoAdjustSettingsResponse,
    AutoAdjustSettingsUpdateRequest,
)
from app.schemas.user import MetaAccountResponse
from app.schemas.trade import SimulateTradeRequest, TradeResponse
from app.services.trade_processing_service import trade_processor
from app.services.metaapi_provisioning import metaapi_provisioning
from app.services.metaapi_service import metaapi_service
from app.config import get_settings
from app.models.meta_account import MetaAccount
from app.models.subscription import Subscription
from app.models.trial_account_claim import TrialAccountClaim
from app.models.trade import Trade, TradeStatus
from app.services.trader_data_service import build_trader_data_payload

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Account"])

MT5_ENGINE_URL = os.getenv("MT5_ENGINE_URL", "http://127.0.0.1:5000")


def _is_connected_recently(last_heartbeat, minutes=5):
    """Check if heartbeat is recent, handling both timezone-aware and naive datetimes."""
    if not last_heartbeat:
        return False
    # Ensure both datetimes are timezone-aware for comparison
    now = datetime.now(timezone.utc)
    hb = last_heartbeat
    if hb.tzinfo is None:
        # If heartbeat is naive, assume it's UTC
        hb = hb.replace(tzinfo=timezone.utc)
    return (now - hb) < timedelta(minutes=minutes)


def _account_fingerprint(login: str, server: str, platform: str) -> str:
    return f"{str(login).strip()}|{str(server).strip().lower()}|{str(platform).strip().lower()}"


async def _has_paid_subscription(db: AsyncSession, user_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.updated_at.desc())
    )
    sub = result.scalars().first()
    if not sub:
        return False

    status_value = (sub.status or "").lower()
    paid_statuses = {"active", "trialing", "past_due", "unpaid"}
    return status_value in paid_statuses and status_value != "trial"


async def _is_trial_expired(db: AsyncSession, user_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.updated_at.desc())
    )
    sub = result.scalars().first()
    if not sub:
        return True

    status_value = (sub.status or "").lower()
    if status_value != "trial":
        return False

    if not sub.current_period_end:
        return False

    period_end = sub.current_period_end
    if period_end.tzinfo is None:
        period_end = period_end.replace(tzinfo=timezone.utc)
    return period_end < datetime.now(timezone.utc)



@router.post("/account/connect", response_model=TradingAccountResponse)
async def connect_account(
    payload: TradingAccountConnect,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect trading account via MetaAPI provisioning.
    
    Creates a MetaAPI cloud account from MT4/MT5 broker credentials and establishes
    a live WebSocket connection for real-time trade data streaming.
    
    If account_id is provided, skips provisioning and connects directly to existing account.
    """
    try:
        # Validate platform
        platform = payload.platform.lower()
        if platform not in ("mt4", "mt5"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Platform must be 'mt4' or 'mt5'",
            )

        logger.info(f"Connecting to MetaAPI for account {payload.login} on {payload.server}...")

        # Anti-abuse: free/trial users cannot re-claim trial on an account already
        # claimed by a different user.
        fingerprint = _account_fingerprint(payload.login, payload.server, platform)
        paid_user = await _has_paid_subscription(db, current_user.id)
        trial_expired = await _is_trial_expired(db, current_user.id)

        if trial_expired and not paid_user:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Your 7-day free trial has ended. Upgrade your plan to reconnect trading accounts.",
            )

        claim_result = await db.execute(
            select(TrialAccountClaim).where(TrialAccountClaim.fingerprint == fingerprint)
        )
        existing_claim = claim_result.scalar_one_or_none()

        if existing_claim and existing_claim.first_user_id != current_user.id and not paid_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "This trading account has already used a free trial on another profile. "
                    "Please upgrade billing on this account to continue."
                ),
            )

        if existing_claim:
            existing_claim.last_user_id = current_user.id
            existing_claim.last_claimed_at = datetime.now(timezone.utc)
            existing_claim.claim_count = int(existing_claim.claim_count or 0) + 1
            db.add(existing_claim)
        else:
            db.add(
                TrialAccountClaim(
                    fingerprint=fingerprint,
                    mt_login=str(payload.login).strip(),
                    mt_server=str(payload.server).strip().lower(),
                    mt_platform=platform,
                    first_user_id=current_user.id,
                    last_user_id=current_user.id,
                    claim_count=1,
                    first_claimed_at=datetime.now(timezone.utc),
                    last_claimed_at=datetime.now(timezone.utc),
                )
            )
        await db.flush()
        
        # Create a new MetaAccount record for this user (support many accounts)
        # We will provision a MetaAPI cloud account and associate it with this MetaAccount
        metaapi_account_id = None
        # Allow passing a temporary MetaAPI token in the request (useful for testing)
        orig_provision_token = getattr(metaapi_provisioning, "_token", None)
        orig_metaapi_api = getattr(metaapi_service, "_api", None)
        orig_metaapi_settings = getattr(metaapi_service, "settings", None)

        if getattr(payload, "metaapi_token", None):
            # Inject token into provisioning and service singletons for this request
            metaapi_provisioning._token = payload.metaapi_token
            try:
                # Update metaapi_service settings and clear cached client so it re-initializes
                metaapi_service.settings.METAAPI_TOKEN = payload.metaapi_token
            except Exception:
                metaapi_service.settings = get_settings()
                metaapi_service.settings.METAAPI_TOKEN = payload.metaapi_token
            metaapi_service._api = None

        try:
            # If account_id is provided, use it directly (skip provisioning)
            if getattr(payload, "account_id", None):
                metaapi_account_id = payload.account_id
                logger.info(f"Using provided MetaAPI account ID: {metaapi_account_id}")
            else:
                # Otherwise, provision/find account
                metaapi_account_id = await metaapi_provisioning.create_account(
                    login=payload.login,
                    password=payload.password,
                    server=payload.server,
                    platform=platform,
                )
                logger.info(f"MetaAPI account created/verified: {metaapi_account_id}")
        except Exception as e:
            logger.error(f"MetaAPI provisioning failed: {e}")
            # restore transient tokens if provided
            if getattr(payload, "metaapi_token", None):
                try:
                    metaapi_provisioning._token = orig_provision_token
                    metaapi_service._api = orig_metaapi_api
                    if orig_metaapi_settings is not None:
                        metaapi_service.settings = orig_metaapi_settings
                except Exception:
                    pass
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to provision MetaAPI account: {str(e)}",
            )

        # Persist new MetaAccount row
        meta_account = MetaAccount(
            user_id=current_user.id,
            metaapi_account_id=metaapi_account_id,
            mt_login=payload.login,
            mt_server=payload.server,
            mt_platform=platform,
        )
        db.add(meta_account)
        await db.commit()
        await db.refresh(meta_account)
        logger.info(f"✅ Created MetaAccount {meta_account.id} for user {current_user.id}")

        # Attempt to connect the newly created MetaAccount
        connection_result = await metaapi_service.connect(current_user, account_id=metaapi_account_id)
        logger.info(f"MetaAPI connection result: {connection_result}")
        # Restore any transient tokens that were injected for this request
        if getattr(payload, "metaapi_token", None):
            try:
                metaapi_provisioning._token = orig_provision_token
                metaapi_service._api = orig_metaapi_api
                if orig_metaapi_settings is not None:
                    metaapi_service.settings = orig_metaapi_settings
            except Exception:
                pass
        

        # Step 5: Fetch account info (balance, equity, etc.)
        account_info = None
        try:
            if connection_result.get("connected"):
                # Get account state from MetaAPI
                account_state = connection_result
                account_info = {
                    "balance": account_state.get("balance"),
                    "equity": account_state.get("equity"),
                    "currency": account_state.get("currency", "USD"),
                }
        except Exception as e:
            logger.debug(f"Could not fetch account info: {e}")

        # Step 6: Auto-fetch trade history if connected (run in background, don't block response)
        if connection_result.get("connected"):
            try:
                # Launch background task to fetch history (don't await, let it run async)
                import asyncio
                asyncio.create_task(
                    metaapi_service.fetch_trade_history(
                        user_id=str(current_user.id),
                        account_id=metaapi_account_id,
                        lookback_days=180
                    )
                )
                logger.info(f"Launched background task to fetch trade history for account {metaapi_account_id}")
            except Exception as e:
                logger.warning(f"Could not launch history fetch task: {e}")

        return TradingAccountResponse(
            connected=connection_result.get("connected", False),
            account_id=current_user.metaapi_account_id,
            login=current_user.mt_login,
            server=current_user.mt_server,
            platform=current_user.mt_platform,
            connection_status="connected" if connection_result.get("connected") else "connecting",
            message=f"Account {payload.login} connected via MetaAPI. Status: {connection_result.get('status', 'connecting')}",
            balance=account_info.get("balance") if account_info else None,
            equity=account_info.get("equity") if account_info else None,
            currency=account_info.get("currency") if account_info else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        # Log full traceback to file for debugging without exposing details to client
        tb = traceback.format_exc()
        logger.error(f"Error connecting account: {e}\n{tb}")
        try:
            os.makedirs('logs', exist_ok=True)
            with open('logs/metaapi_connect_error.log', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().isoformat()}] Error connecting account: {e}\n")
                f.write(tb + "\n")
        except Exception as write_err:
            logger.error(f"Failed to write metaapi_connect_error.log: {write_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect trading account.",
        )


@router.get("/account/info", response_model=TradingAccountResponse)
async def get_account_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get trading account registration info."""
    # Return the most relevant MetaAccount for the user:
    # 1) If any MetaAccount has a recent heartbeat, return that as the active account
    # 2) Else if any MetaAccount exists, return the first as linked
    result = await db.execute(select(MetaAccount).where(MetaAccount.user_id == current_user.id))
    accounts = result.scalars().all()

    if not accounts:
        if current_user.mt_login and current_user.metaapi_account_id:
            return TradingAccountResponse(
                connected=False,
                account_id=current_user.metaapi_account_id,
                login=current_user.mt_login,
                server=current_user.mt_server,
                platform=current_user.mt_platform,
                connection_status="linked",
                message="Account linked, waiting for terminal heartbeat...",
            )
        return TradingAccountResponse(
            connected=False,
            connection_status="not_configured",
            message="No account linked",
        )

    # Find active by heartbeat (handle both naive and timezone-aware datetimes)
    now = datetime.now(timezone.utc)
    active = None
    for a in accounts:
        if a.mt_last_heartbeat:
            # Make heartbeat timezone-aware if it's naive
            heartbeat = a.mt_last_heartbeat
            if isinstance(heartbeat, str):
                # Parse ISO string
                try:
                    heartbeat = datetime.fromisoformat(heartbeat.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    continue
            elif heartbeat.tzinfo is None:
                # Naive datetime - assume UTC
                heartbeat = heartbeat.replace(tzinfo=timezone.utc)
            
            if (now - heartbeat) < timedelta(minutes=5):
                active = a
                break

    if active is None:
        # pick the first account as linked
        a = accounts[0]
        return TradingAccountResponse(
            connected=False,
            account_id=a.metaapi_account_id,
            login=a.mt_login,
            server=a.mt_server,
            platform=a.mt_platform,
            connection_status="linked",
            message="Account linked, waiting for terminal heartbeat...",
        )

    # Active account
    return TradingAccountResponse(
        connected=True,
        account_id=active.metaapi_account_id,
        login=active.mt_login,
        server=active.mt_server,
        platform=active.mt_platform,
        connection_status="connected",
        message="Active",
    )


@router.get("/account/status", response_model=AccountStatus)
async def get_account_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current connection status (Linked vs Active)."""
    # Check MetaAccount rows for any recent heartbeat
    result = await db.execute(select(MetaAccount).where(MetaAccount.user_id == current_user.id))
    accounts = result.scalars().all()

    if not accounts:
        if current_user.mt_login and current_user.metaapi_account_id:
            return AccountStatus(
                connected=False,
                login=current_user.mt_login,
                server=current_user.mt_server,
                platform=current_user.mt_platform,
                connection_status="linked",
                broker=current_user.settings.get("broker") if current_user.settings else None,
            )
        return AccountStatus(
            connected=False,
            login=current_user.mt_login,
            server=current_user.mt_server,
            platform=current_user.mt_platform,
            connection_status="disconnected",
            broker=current_user.settings.get("broker") if current_user.settings else None,
        )

    now = datetime.now(timezone.utc)
    for a in accounts:
        if a.mt_last_heartbeat:
            # Make heartbeat timezone-aware if it's naive
            heartbeat = a.mt_last_heartbeat
            if isinstance(heartbeat, str):
                # Parse ISO string
                try:
                    heartbeat = datetime.fromisoformat(heartbeat.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    continue
            elif heartbeat.tzinfo is None:
                # Naive datetime - assume UTC
                heartbeat = heartbeat.replace(tzinfo=timezone.utc)
            
            if (now - heartbeat) < timedelta(minutes=5):
                return AccountStatus(
                    connected=True,
                    login=a.mt_login,
                    server=a.mt_server,
                    platform=a.mt_platform,
                    connection_status="connected",
                    broker=current_user.settings.get("broker") if current_user.settings else None,
                )

    # No recent heartbeat, but at least one linked account exists
    a = accounts[0]
    return AccountStatus(
        connected=False,
        login=a.mt_login,
        server=a.mt_server,
        platform=a.mt_platform,
        connection_status="linked",
        broker=current_user.settings.get("broker") if current_user.settings else None,
    )


@router.get("/account/auto-adjust-settings", response_model=AutoAdjustSettingsResponse)
async def get_auto_adjust_settings(
    current_user: User = Depends(get_current_user),
):
    """Return resolved auto-adjust settings for the current user."""
    app_settings = get_settings()
    user_settings = current_user.settings or {}

    enabled = bool(user_settings.get("beta_auto_adjust", False))
    score_threshold = int(
        user_settings.get(
            "auto_adjust_score_threshold",
            getattr(app_settings, "AUTO_ADJUST_DEFAULT_THRESHOLD", 3),
        )
    )
    mode = str(
        user_settings.get(
            "auto_adjust_mode",
            getattr(app_settings, "AUTO_ADJUST_DEFAULT_MODE", "hybrid"),
        )
    ).lower()
    symbols = user_settings.get("auto_adjust_symbols") or []

    return AutoAdjustSettingsResponse(
        enabled=enabled,
        score_threshold=max(1, min(10, score_threshold)),
        mode=mode if mode in {"close", "modify", "hybrid"} else "hybrid",
        symbols=[str(s).upper() for s in symbols if str(s).strip()],
    )


@router.put("/account/auto-adjust-settings", response_model=AutoAdjustSettingsResponse)
async def update_auto_adjust_settings(
    payload: AutoAdjustSettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update per-user auto-adjust settings (beta)."""
    app_settings = get_settings()
    merged = dict(current_user.settings or {})

    if payload.enabled is not None:
        merged["beta_auto_adjust"] = bool(payload.enabled)
    if payload.score_threshold is not None:
        merged["auto_adjust_score_threshold"] = int(payload.score_threshold)
    if payload.mode is not None:
        merged["auto_adjust_mode"] = payload.mode
    if payload.symbols is not None:
        merged["auto_adjust_symbols"] = [
            str(symbol).strip().upper()
            for symbol in payload.symbols
            if str(symbol).strip()
        ]

    current_user.settings = merged
    await db.commit()
    await db.refresh(current_user)

    return AutoAdjustSettingsResponse(
        enabled=bool(merged.get("beta_auto_adjust", False)),
        score_threshold=int(
            merged.get(
                "auto_adjust_score_threshold",
                getattr(app_settings, "AUTO_ADJUST_DEFAULT_THRESHOLD", 3),
            )
        ),
        mode=str(
            merged.get(
                "auto_adjust_mode",
                getattr(app_settings, "AUTO_ADJUST_DEFAULT_MODE", "hybrid"),
            )
        ).lower(),
        symbols=[str(s).upper() for s in (merged.get("auto_adjust_symbols") or []) if str(s).strip()],
    )


@router.get("/accounts", response_model=list[MetaAccountResponse])
async def list_meta_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all MetaAccounts for the current user."""
    result = await db.execute(select(MetaAccount).where(MetaAccount.user_id == current_user.id))
    accounts = result.scalars().all()
    out = []
    for a in accounts:
        out.append(
            MetaAccountResponse(
                id=a.id,
                account_id=a.metaapi_account_id,
                login=a.mt_login,
                server=a.mt_server,
                platform=a.mt_platform,
                connection_status=("connected" if _is_connected_recently(a.mt_last_heartbeat) else "linked"),
                message=("Active" if _is_connected_recently(a.mt_last_heartbeat) else "Linked"),
                last_heartbeat=a.mt_last_heartbeat,
            )
        )
    return out


@router.post("/account/select", response_model=TradingAccountResponse)
async def select_account(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Select an existing MetaAccount and attempt to connect to it."""
    account_id = payload.get("account_id")
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id required")

    result = await db.execute(select(MetaAccount).where(MetaAccount.user_id == current_user.id, MetaAccount.metaapi_account_id == account_id))
    ma = result.scalar_one_or_none()
    if not ma:
        raise HTTPException(status_code=404, detail="MetaAccount not found")

    connection_result = await metaapi_service.connect(current_user, account_id=account_id)

    # Return a TradingAccountResponse reflecting the selected account
    return TradingAccountResponse(
        connected=connection_result.get("connected", False),
        account_id=ma.metaapi_account_id,
        login=ma.mt_login,
        server=ma.mt_server,
        platform=ma.mt_platform,
        connection_status=("connected" if connection_result.get("connected") else connection_result.get("status") or "disconnected"),
        message=connection_result.get("error") or connection_result.get("status") or "",
    )


@router.delete("/account/disconnect")
async def disconnect_account(
    account_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect the trading account.

    Clears the stored MT5/MT4 credentials in the database.
    """
    if account_id:
        # Remove specific MetaAccount for this user
        result = await db.execute(select(MetaAccount).where(MetaAccount.user_id == current_user.id, MetaAccount.metaapi_account_id == account_id))
        ma = result.scalar_one_or_none()
        if ma:
            await db.delete(ma)
            await db.commit()
            return {"message": f"Account {account_id} disconnected"}
        else:
            raise HTTPException(status_code=404, detail="MetaAccount not found")

    # Legacy behavior: clear primary fields on user
    current_user.mt_login = None
    current_user.mt_server = None
    current_user.mt_platform = None
    if current_user.settings:
        current_user.settings.pop("broker", None)
    
    await db.commit()
    return {"message": "Account disconnected"}


@router.get("/dev/trader-data")
async def get_trader_data(
    user_id: str = Query(None, description="User ID (UUID)"),
    email: str = Query(None, description="User email to lookup"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return trader diagnostics for the authenticated user.

    Optional user_id/email filters are accepted for backward compatibility,
    but they must match the authenticated user.
    """
    if user_id and user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only access your own trader data")
    if email and email.lower().strip() != current_user.email.lower().strip():
        raise HTTPException(status_code=403, detail="You can only access your own trader data")

    return await build_trader_data_payload(db=db, user=current_user)


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
        "external_id": f"SIM_{uuid.uuid4().hex[:8]}",
        "symbol": payload.symbol.upper(),
        "type": payload.direction.upper(),
        "entry_price": payload.entry_price,
        "sl": payload.sl,
        "tp": payload.tp,
        "lot_size": payload.lot_size,
    }

    # Open the trade via the same pipeline as real trades
    trade = await trade_processor.process_trade_opened(user_id, trade_data)
    if not trade:
        raise HTTPException(status_code=500, detail="Failed to simulate trade open")

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

            exit_price = round(float(exit_price), 5)
            await trade_processor.process_trade_closed(user_id, {
                "external_id": trade.external_trade_id,
                "exit_price": exit_price
            })
            logger.info(f"Auto-closed simulated trade {trade.id} at {exit_price}")

        asyncio.create_task(auto_close())
        logger.info(
            f"Simulated trade {trade.id} will auto-close in {payload.close_after_seconds}s"
        )

    return TradeResponse.model_validate(trade)

@router.get("/history/stats", tags=["Accounts"])
async def get_trade_history_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get trade history statistics and check if enough data exists for analytics.
    
    Returns:
        - total_closed_trades: Number of closed trades
        - min_trades_for_analytics: Minimum trades needed (10)
        - has_enough_history: Boolean indicating if analytics can be run
        - status: Message about history status
    """
    from sqlalchemy import func

    result = await db.execute(
        select(func.count(Trade.id)).where(
            and_(
                Trade.user_id == current_user.id,
                Trade.status == TradeStatus.CLOSED,
            )
        )
    )
    total_closed = result.scalar() or 0
    
    MIN_TRADES_FOR_ANALYTICS = 10
    has_enough = total_closed >= MIN_TRADES_FOR_ANALYTICS
    
    status = "ready_for_analytics" if has_enough else "insufficient_history"
    message = f"You have {total_closed} closed trade(s). " + (
        "✓ Ready for analytics!" if has_enough else f"Need {MIN_TRADES_FOR_ANALYTICS - total_closed} more trades."
    )
    
    return {
        "total_closed_trades": total_closed,
        "min_trades_for_analytics": MIN_TRADES_FOR_ANALYTICS,
        "has_enough_history": has_enough,
        "status": status,
        "message": message,
    }