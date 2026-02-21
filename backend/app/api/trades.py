"""Trade routes — list, filter, and retrieve trades."""

import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.trade import Trade, TradeStatus
from app.models.user import User
from app.schemas.trade import TradeResponse, TradeListResponse

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

    # Get total count
    count_result = await db.execute(
        select(func.count(Trade.id)).where(where_clause)
    )
    total = count_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Trade)
        .where(where_clause)
        .order_by(Trade.open_time.desc())
        .offset(offset)
        .limit(per_page)
    )
    trades = result.scalars().all()

    return TradeListResponse(
        trades=[TradeResponse.model_validate(t) for t in trades],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/open", response_model=list[TradeResponse])
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
    trades = result.scalars().all()
    return [TradeResponse.model_validate(t) for t in trades]


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
