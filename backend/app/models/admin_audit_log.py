"""Admin audit log model for privileged change tracking."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.compat import PortableUUID


class AdminAuditLog(Base):
    """Persisted audit entries for admin-driven mutations."""

    __tablename__ = "admin_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    admin_user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    changed_fields: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    before_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    after_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
