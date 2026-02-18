"""Cross-database UUID compatibility.

SQLite doesn't support PostgreSQL's UUID type natively.
This module provides a portable UUID column type.
"""
import uuid
from sqlalchemy import String, TypeDecorator


class PortableUUID(TypeDecorator):
    """Platform-independent UUID type.
    Uses PostgreSQL UUID when available, otherwise stores as String(36).
    """
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return str(value)
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
        return value
