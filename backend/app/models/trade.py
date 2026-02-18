"""Trade model."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, Float, Integer, JSON, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TradeDirection(str, PyEnum):
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(str, PyEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Trade(Base):
    """Trade record model — captures all trade data plus AI analysis results."""

    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_trade_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Trade details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    direction: Mapped[TradeDirection] = mapped_column(
        Enum(TradeDirection), nullable=False
    )
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sl: Mapped[float | None] = mapped_column(Float, nullable=True)
    tp: Mapped[float | None] = mapped_column(Float, nullable=True)
    lot_size: Mapped[float] = mapped_column(Float, nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    close_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Performance
    pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    pnl_r: Mapped[float | None] = mapped_column(Float, nullable=True)  # P&L in R-multiples
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # AI analysis
    ai_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10
    ai_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Pre-trade analysis
    ai_review: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Post-trade review
    behavioral_flags: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)

    # Status
    status: Mapped[TradeStatus] = mapped_column(
        Enum(TradeStatus), nullable=False, default=TradeStatus.OPEN
    )

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="trades")
