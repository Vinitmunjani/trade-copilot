"""Pydantic schemas for trade operations."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class TradeBase(BaseModel):
    """Base trade fields."""
    symbol: str
    direction: str  # BUY or SELL
    entry_price: float
    sl: float | None = None
    tp: float | None = None
    lot_size: float


class TradeCreate(TradeBase):
    """Schema for creating a trade (simulation)."""
    external_trade_id: str | None = None
    open_time: datetime | None = None


class TradeClose(BaseModel):
    """Schema for closing a trade (simulation)."""
    exit_price: float
    close_time: datetime | None = None


class TradeResponse(BaseModel):
    """Full trade response."""
    id: uuid.UUID
    user_id: uuid.UUID
    external_trade_id: str | None = None
    symbol: str
    direction: str
    entry_price: float
    exit_price: float | None = None
    sl: float | None = None
    tp: float | None = None
    lot_size: float
    open_time: datetime
    close_time: datetime | None = None
    pnl: float | None = None
    pnl_r: float | None = None
    duration_seconds: int | None = None
    ai_score: int | None = None
    ai_analysis: dict | None = None
    ai_review: dict | None = None
    behavioral_flags: list | None = None
    status: str
    notes: str | None = None
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
    sl: float | None = Field(default=1.0820, description="Stop loss")
    tp: float | None = Field(default=1.0920, description="Take profit")
    lot_size: float = Field(default=0.1, description="Lot size")
    close_after_seconds: int | None = Field(
        default=None,
        description="If set, auto-close after N seconds with a random exit price"
    )
