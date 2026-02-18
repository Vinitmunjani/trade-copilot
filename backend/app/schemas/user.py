"""Pydantic schemas for user operations."""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response (no password)."""
    id: uuid.UUID
    email: str
    is_active: bool
    metaapi_account_id: str | None = None
    settings: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AccountConnect(BaseModel):
    """Schema for connecting MetaAPI account."""
    metaapi_token: str = Field(..., description="MetaAPI provisioning profile token")
    account_id: str = Field(..., description="MetaAPI account ID (MT4/MT5)")


class AccountStatus(BaseModel):
    """Schema for account connection status."""
    connected: bool
    account_id: str | None = None
    connection_status: str | None = None
    broker: str | None = None
    server: str | None = None
