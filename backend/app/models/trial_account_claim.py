"""Trial account claim model.

Stores a normalized trading account fingerprint (login+server+platform)
to prevent repeated free-trial abuse across newly created user accounts.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.compat import PortableUUID
from app.database import Base


class TrialAccountClaim(Base):
    """Tracks first claim of a trading account fingerprint for trial gating."""

    __tablename__ = "trial_account_claims"
    __table_args__ = (
        UniqueConstraint("fingerprint", name="uq_trial_account_claims_fingerprint"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    fingerprint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mt_login: Mapped[str] = mapped_column(String(50), nullable=False)
    mt_server: Mapped[str] = mapped_column(String(255), nullable=False)
    mt_platform: Mapped[str] = mapped_column(String(10), nullable=False, default="mt5")

    first_user_id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), ForeignKey("users.id"), nullable=False, index=True)
    last_user_id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), ForeignKey("users.id"), nullable=False, index=True)

    claim_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
