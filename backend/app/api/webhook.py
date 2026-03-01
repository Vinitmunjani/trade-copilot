from datetime import datetime, timezone
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy import select
from app.database import async_session_factory
from app.models.user import User
from app.services.trade_processing_service import trade_processor

router = APIRouter(prefix="/webhook", tags=["Webhook"])
logger = logging.getLogger(__name__)

async def update_last_heartbeat(user_id: str):
    """Update the user's last heartbeat timestamp."""
    async with async_session_factory() as db:
        try:
            result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
            user = result.scalar_one_or_none()
            if user:
                user.mt_last_heartbeat = datetime.now(timezone.utc)
                await db.commit()
        except Exception as e:
            logger.error(f"Error updating heartbeat for user {user_id}: {e}")
            await db.rollback()

@router.post("/mt5/trade")
async def mt5_trade_webhook(
    payload: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID"),
):
    """
    Receive trade alerts from local MT5 engines.
    
    Payload format:
    {
        "event": "open" | "close",
        "trade": {
            "external_id": "...",
            "symbol": "...",
            "type": "BUY"|"SELL",
            "entry_price": 1.23,
            "exit_price": 1.24, (for close)
            "sl": 1.22,
            "tp": 1.25,
            "lot_size": 0.1
        }
    }
    """
    event = payload.get("event")
    trade_data = payload.get("trade", {})
    
    logger.info(f"Received MT5 webhook from user {x_user_id}: {event}")
    await update_last_heartbeat(x_user_id)
    
    if event == "open":
        await trade_processor.process_trade_opened(x_user_id, trade_data)
    elif event == "close":
        await trade_processor.process_trade_closed(x_user_id, trade_data)
    else:
        raise HTTPException(status_code=400, detail="Invalid event type")
        
    return {"status": "success"}

@router.post("/mt5/heartbeat")
async def mt5_heartbeat(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
):
    """Update connection status without sending trade/account data.
    If X-User-ID header is missing, fall back to the first user in the DB.
    """
    if not x_user_id:
        # Retrieve first user ID as a fallback for testing
        async with async_session_factory() as db:
            result = await db.execute(select(User.id).limit(1))
            first_user = result.scalar_one_or_none()
            if first_user:
                x_user_id = str(first_user)
            else:
                raise HTTPException(status_code=400, detail="No user ID provided and no users in DB")
    await update_last_heartbeat(x_user_id)
    return {"status": "success"}

@router.post("/mt5/account")
async def mt5_account_webhook(
    payload: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID"),
):
    """Receive account updates from local MT5 engines."""
    logger.info(f"Received MT5 account update from user {x_user_id}")
    await update_last_heartbeat(x_user_id)
    # Update account balance/equity in DB or broadcast
    return {"status": "success"}
