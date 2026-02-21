"""Pydantic schemas for trading rules."""
from typing import List, Dict,  Optional, Union

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class TradingRulesUpdate(BaseModel):
    """Schema for updating trading rules."""
    max_risk_percent: Optional[float] = Field(None, ge=0.1, le=10.0)
    min_risk_reward: Optional[float] = Field(None, ge=0.5, le=10.0)
    max_trades_per_day: Optional[int] = Field(None, ge=1, le=50)
    max_daily_loss_percent: Optional[float] = Field(None, ge=1.0, le=20.0)
    max_concurrent_trades: Optional[int] = Field(None, ge=1, le=20)
    blocked_sessions: Optional[List[str]] = None
    allowed_symbols: Optional[List[str]] = None
    custom_checklist: Optional[List[str]] = None
    min_time_between_trades: Optional[int] = Field(None, ge=0, le=120)


class TradingRulesResponse(BaseModel):
    """Trading rules response."""
    id: uuid.UUID
    user_id: uuid.UUID
    max_risk_percent: float
    min_risk_reward: float
    max_trades_per_day: int
    max_daily_loss_percent: float
    max_concurrent_trades: int
    blocked_sessions: List[str]
    allowed_symbols: List[str]
    custom_checklist: List[str]
    min_time_between_trades: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RuleAdherenceItem(BaseModel):
    """Single rule adherence check."""
    rule: str
    description: str
    adhered: bool
    details: Optional[str] = None


class RuleAdherenceResponse(BaseModel):
    """Full rule adherence report."""
    overall_score: float = Field(..., description="0-100 adherence score")
    items: List[RuleAdherenceItem]
    period_start: datetime
    period_end: datetime
