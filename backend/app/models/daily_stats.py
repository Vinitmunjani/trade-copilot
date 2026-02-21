"""Daily statistics model."""
from typing import Optional, Dict, Any

import uuid
from datetime import date as DateType, datetime

from sqlalchemy import Date, DateTime, Float, Integer, JSON, ForeignKey, UniqueConstraint
from app.models.compat import PortableUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DailyStats(Base):
    """Aggregated daily trading statistics per user."""

    __tablename__ = "daily_stats"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[DateType] = mapped_column(Date, nullable=False, index=True)

    # Aggregated metrics
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0)
    losing_trades: Mapped[int] = mapped_column(Integer, default=0)
    breakeven_trades: Mapped[int] = mapped_column(Integer, default=0)

    total_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    total_pnl_r: Mapped[float] = mapped_column(Float, default=0.0)
    largest_win: Mapped[float] = mapped_column(Float, default=0.0)
    largest_loss: Mapped[float] = mapped_column(Float, default=0.0)
    avg_winner: Mapped[float] = mapped_column(Float, default=0.0)
    avg_loser: Mapped[float] = mapped_column(Float, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_rr: Mapped[float] = mapped_column(Float, default=0.0)
    r_expectancy: Mapped[float] = mapped_column(Float, default=0.0)

    # Session breakdown
    session_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Symbol breakdown
    symbol_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Behavioral
    behavioral_flags_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_ai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="daily_stats")
