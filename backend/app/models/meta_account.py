"""MetaAccount model: represents a single MT4/MT5 account linked to a user via MetaAPI."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.compat import PortableUUID
from app.database import Base


class MetaAccount(Base):
    __tablename__ = "meta_accounts"

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # MetaAPI account identifier (cloud account)
    metaapi_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mt_login: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mt_server: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mt_platform: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="mt5")

    mt_last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to user
    user = relationship("User", back_populates="meta_accounts")