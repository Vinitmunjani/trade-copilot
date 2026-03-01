"""User model."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import String, DateTime, Text, JSON
from app.models.compat import PortableUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    metaapi_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metaapi_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mt_login: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mt_server: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mt_platform: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="mt5")
    mt_last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    trades = relationship("Trade", back_populates="user", lazy="selectin")
    trading_rules = relationship("TradingRules", back_populates="user", uselist=False, lazy="selectin")
    daily_stats = relationship("DailyStats", back_populates="user", lazy="selectin")
    # New relationship: one user can have many MetaAPI-linked trading accounts
    meta_accounts = relationship("MetaAccount", back_populates="user", lazy="selectin")
