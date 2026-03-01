"""TradeLog model — append-only audit log for every state change on a trade."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, JSON, ForeignKey, Text
from app.models.compat import PortableUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TradeLog(Base):
    """One row per noteworthy event on a trade (opened, closed, modified, behavioral_flag, score_update)."""

    __tablename__ = "trade_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    trade_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("trades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # opened | closed | modified | score_update | behavioral_flag
    payload: Mapped[dict] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
