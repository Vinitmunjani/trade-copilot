"""Trading rules model — user-defined risk management rules."""
from typing import Optional, Dict, Any

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, JSON, ForeignKey, DateTime
from app.models.compat import PortableUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TradingRules(Base):
    """User-defined trading rules for behavioral analysis and enforcement."""

    __tablename__ = "trading_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Risk rules
    max_risk_percent: Mapped[float] = mapped_column(Float, default=2.0)
    min_risk_reward: Mapped[float] = mapped_column(Float, default=1.5)
    max_trades_per_day: Mapped[int] = mapped_column(Integer, default=5)
    max_daily_loss_percent: Mapped[float] = mapped_column(Float, default=5.0)
    max_concurrent_trades: Mapped[int] = mapped_column(Integer, default=3)

    # Session rules — list of blocked sessions: ["asian", "london", "new_york"]
    blocked_sessions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)

    # Allowed symbols — empty means all allowed
    allowed_symbols: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)

    # Custom checklist items — user-defined pre-trade checklist
    custom_checklist: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)

    # Minimum time between trades (minutes) to prevent revenge trading
    min_time_between_trades: Mapped[int] = mapped_column(Integer, default=10)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="trading_rules")
