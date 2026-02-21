"""FastAPI dependencies — DB sessions, current user, Redis."""

import uuid
from typing import Optional, AsyncGenerator

import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import decode_access_token
from app.database import async_session_factory
from app.models.user import User

settings = get_settings()
security_scheme = HTTPBearer()

# Global Redis client — initialized at startup
_redis_client: Optional[redis.Redis] = None


async def init_redis() -> redis.Redis:
    """Initialize the global Redis client."""
    global _redis_client
    _redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    # Test connection
    try:
        await _redis_client.ping()
    except Exception:
        # Redis is optional — degrade gracefully
        _redis_client = None
    return _redis_client


async def close_redis() -> None:
    """Close the global Redis client."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_redis() -> Optional[redis.Redis]:
    """Return the global Redis client (may be None if unavailable)."""
    return _redis_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and verify the current user from JWT token.

    Args:
        credentials: Bearer token from Authorization header.
        db: Database session.

    Returns:
        Authenticated User model instance.

    Raises:
        HTTPException 401 if token is invalid or user not found.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user
