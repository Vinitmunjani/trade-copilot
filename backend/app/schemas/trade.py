from typing import Optional, Union
"""Pydantic schemas for trade operations."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class TradeBase(BaseModel):
    """Base trade fields."""
    symbol: str
    direction: str  # BUY or SELL
    entry_price: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    lot_size: float


class TradeCreate(TradeBase):
    """Schema for creating a trade (simulation)."""
    external_trade_id: Optional[str] = None
    open_time: Optional[datetime] = None


class TradeClose(BaseModel):
    """Schema for closing a trade (simulation)."""
    exit_price: float
    close_time: Optional[datetime] = None


class TradeResponse(BaseModel):
    """Full trade response."""
    id: uuid.UUID
    user_id: uuid.UUID
    external_trade_id: Optional[str] = None
    symbol: str
    direction: str
    entry_price: float
    exit_price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    lot_size: float
    open_time: datetime
    close_time: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_r: Optional[float] = None
    duration_seconds: Optional[int] = None
    ai_score: Optional[int] = None
    ai_analysis: Optional[dict] = None
    ai_review: Optional[dict] = None
    behavioral_flags: Optional[list] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TradeListResponse(BaseModel):
    """Paginated trade list."""
    trades: list[TradeResponse]
    total: int
    page: int
    per_page: int


class SimulateTradeRequest(BaseModel):
    """Request to simulate a trade for testing."""
    symbol: str = Field(default="EURUSD", description="Trading symbol")
    direction: str = Field(default="BUY", description="BUY or SELL")
    entry_price: float = Field(default=1.0850, description="Entry price")
    sl: Optional[float] = Field(default=1.0820, description="Stop loss")
    tp: Optional[float] = Field(default=1.0920, description="Take profit")
    lot_size: float = Field(default=0.1, description="Lot size")
    close_after_seconds: Optional[int] = Field(
        default=None,
        description="If set, auto-close after N seconds with a random exit price"
    )
