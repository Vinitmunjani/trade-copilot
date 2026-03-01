from typing import List, Dict,  Optional, Union
"""Trade routes — list, filter, and retrieve trades."""

import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.trade import Trade, TradeStatus, TradeDirection
from app.models.trade_log import TradeLog
from app.models.user import User
from app.schemas.trade import TradeResponse, TradeListResponse, SimulateTradeRequest
from app.services.trade_processing_service import trade_processor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trades", tags=["Trades"])


@router.get("", response_model=TradeListResponse)
async def list_trades(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., EURUSD)"),
    direction: Optional[str] = Query(None, description="Filter by direction (BUY or SELL)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (OPEN or CLOSED)"),
    date_from: Optional[datetime] = Query(None, description="Start of date range (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="End of date range (ISO format)"),
    score_min: Optional[int] = Query(None, ge=1, le=10, description="Minimum AI score"),
    score_max: Optional[int] = Query(None, ge=1, le=10, description="Maximum AI score"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List trades with pagination and optional filters.

    Supports filtering by symbol, direction, date range, status, and AI score range.
    Results are ordered by open_time descending (newest first).
    """
    conditions = [Trade.user_id == current_user.id]

    if symbol:
        conditions.append(Trade.symbol == symbol.upper())
    if direction:
        conditions.append(Trade.direction == direction.upper())
    if status_filter:
        conditions.append(Trade.status == status_filter.upper())
    if date_from:
        conditions.append(Trade.open_time >= date_from)
    if date_to:
        conditions.append(Trade.open_time <= date_to)
    if score_min is not None:
        conditions.append(Trade.ai_score >= score_min)
    if score_max is not None:
        conditions.append(Trade.ai_score <= score_max)

    where_clause = and_(*conditions)

    # Fetch all matching rows, then deduplicate legacy duplicate OPEN trades
    # (same external_trade_id can be inserted twice due to earlier race conditions).
    result = await db.execute(
        select(Trade)
        .where(where_clause)
        .order_by(Trade.open_time.desc())
    )
    all_trades = result.scalars().all()

    deduped_trades = []
    seen_open_external_ids = set()
    for trade in all_trades:
        if trade.status == TradeStatus.OPEN and trade.external_trade_id:
            if trade.external_trade_id in seen_open_external_ids:
                continue
            seen_open_external_ids.add(trade.external_trade_id)
        deduped_trades.append(trade)

    total = len(deduped_trades)
    offset = (page - 1) * per_page
    trades = deduped_trades[offset: offset + per_page]

    return TradeListResponse(
        trades=[TradeResponse.model_validate(t) for t in trades],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/open", response_model=List[TradeResponse])
async def get_open_trades(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all currently open trades for the authenticated user."""
    result = await db.execute(
        select(Trade)
        .where(
            and_(
                Trade.user_id == current_user.id,
                Trade.status == TradeStatus.OPEN,
            )
        )
        .order_by(Trade.open_time.desc())
    )
    all_open_trades = result.scalars().all()

    trades = []
    seen_external_ids = set()
    for trade in all_open_trades:
        ext_id = trade.external_trade_id
        if ext_id and ext_id in seen_external_ids:
            continue
        if ext_id:
            seen_external_ids.add(ext_id)
        trades.append(trade)

    return [TradeResponse.model_validate(t) for t in trades]


@router.get("/{trade_id}/logs")
async def get_trade_logs(
    trade_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the audit log for a trade (opened, closed, modified, score_update, behavioral_flag events)."""
    # First verify trade ownership
    trade_result = await db.execute(
        select(Trade).where(
            and_(
                Trade.id == trade_id,
                Trade.user_id == current_user.id,
            )
        )
    )
    trade = trade_result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")

    log_result = await db.execute(
        select(TradeLog)
        .where(TradeLog.trade_id == trade_id)
        .order_by(TradeLog.created_at.asc())
    )
    logs = log_result.scalars().all()
    return [
        {
            "id": str(log.id),
            "trade_id": str(log.trade_id),
            "event_type": log.event_type,
            "payload": log.payload,
            "note": log.note,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single trade by ID.

    Returns the full trade detail including AI analysis, review, and behavioral flags.
    Raises 404 if the trade doesn't exist or doesn't belong to the current user.
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

    return TradeResponse.model_validate(trade)


@router.post("/test/simulate", response_model=TradeResponse)
async def simulate_trade(
    req: SimulateTradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Simulate a trade for testing AI analysis.
    
    This endpoint creates a trade and runs through the full AI analysis pipeline
    to test the trade scoring, behavioral analysis, and post-trade review.
    """
    # Process as if it came from the webhook
    trade_data = {
        "external_id": str(uuid.uuid4()),
        "symbol": req.symbol,
        "type": "BUY" if req.direction == "BUY" else "SELL",
        "entry_price": req.entry_price,
        "sl": req.sl,
        "tp": req.tp,
        "lot_size": req.lot_size,
    }
    
    # Process the trade opening with AI analysis
    trade = await trade_processor.process_trade_opened(str(current_user.id), trade_data)
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process trade",
        )
    
    # If close_after_seconds is set, close the trade
    if req.close_after_seconds:
        import asyncio
        await asyncio.sleep(min(req.close_after_seconds, 5))  # Max 5 second wait
        
        close_data = {
            "external_id": trade_data["external_id"],
            "exit_price": req.entry_price + (0.0050 if req.direction == "BUY" else -0.0050),
        }
        trade = await trade_processor.process_trade_closed(str(current_user.id), close_data)
    
    await db.refresh(trade)
    return TradeResponse.model_validate(trade)
