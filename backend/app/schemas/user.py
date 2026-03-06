from typing import Optional
"""Pydantic schemas for user operations."""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


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
    metaapi_account_id: Optional[str] = None
    mt_login: Optional[str] = None
    mt_server: Optional[str] = None
    mt_platform: Optional[str] = None
    settings: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AccountConnect(BaseModel):
    """Schema for connecting MetaAPI account (legacy)."""
    metaapi_token: str = Field(..., description="MetaAPI provisioning profile token")
    account_id: str = Field(..., description="MetaAPI account ID (MT4/MT5)")


class TradingAccountConnect(BaseModel):
    """Schema for connecting a trading account via MT4/MT5 credentials."""
    login: str = Field(..., description="MT4/MT5 account number")
    password: str = Field(..., description="MT4/MT5 account password")
    server: str = Field(..., description="Broker server name (e.g. ICMarketsSC-Demo)")
    platform: str = Field("mt5", description="Platform: mt4 or mt5")
    broker: str = Field("Exness", description="Broker name")
    metaapi_token: Optional[str] = Field(None, description="Optional MetaAPI token to use for this connection (temporary)")
    account_id: Optional[str] = Field(None, description="Optional existing MetaAPI account ID (skip provisioning if provided)")


class TradingAccountResponse(BaseModel):
    """Schema for trading account connection response."""
    connected: bool
    account_id: Optional[str] = None
    login: Optional[str] = None
    server: Optional[str] = None
    platform: Optional[str] = None
    connection_status: Optional[str] = None
    message: Optional[str] = None
    balance: Optional[float] = None
    equity: Optional[float] = None
    currency: Optional[str] = None

    model_config = {"from_attributes": True}


class MetaAccountResponse(BaseModel):
    """Schema for a user's MetaAPI-linked account."""
    id: Optional[uuid.UUID] = None
    account_id: Optional[str] = None
    login: Optional[str] = None
    server: Optional[str] = None
    platform: Optional[str] = None
    connection_status: Optional[str] = None
    message: Optional[str] = None
    last_heartbeat: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AccountStatus(BaseModel):
    """Schema for account connection status."""
    connected: bool
    account_id: Optional[str] = None
    login: Optional[str] = None
    server: Optional[str] = None
    platform: Optional[str] = None
    connection_status: Optional[str] = None
    broker: Optional[str] = None


class AutoAdjustSettingsResponse(BaseModel):
    """Resolved auto-adjust settings for current user."""

    enabled: bool
    score_threshold: int = Field(ge=1, le=10)
    mode: str = Field(description="close | modify | hybrid")
    symbols: list[str] = Field(default_factory=list)


class AutoAdjustSettingsUpdateRequest(BaseModel):
    """Partial update payload for user auto-adjust settings."""

    enabled: Optional[bool] = None
    score_threshold: Optional[int] = Field(default=None, ge=1, le=10)
    mode: Optional[str] = Field(default=None, description="close | modify | hybrid")
    symbols: Optional[list[str]] = None

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in {"close", "modify", "hybrid"}:
            raise ValueError("mode must be one of: close, modify, hybrid")
        return normalized


class AdminUserUpdateRequest(BaseModel):
    """Schema for admin partial updates to user profile fields."""

    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8)
    metaapi_token: Optional[str] = None
    settings: Optional[dict] = None
    mt_login: Optional[str] = Field(default=None, max_length=50)
    mt_server: Optional[str] = Field(default=None, max_length=255)
    mt_platform: Optional[str] = Field(default=None, description="mt4 or mt5")
    mt_last_heartbeat: Optional[datetime] = None
    subscription: Optional["AdminSubscriptionUpdateRequest"] = None

    @field_validator("mt_platform")
    @classmethod
    def validate_mt_platform(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in {"mt4", "mt5"}:
            raise ValueError("mt_platform must be 'mt4' or 'mt5'")
        return normalized


class AdminSubscriptionUpdateRequest(BaseModel):
    """Schema for admin updates to a user's latest subscription row."""

    plan: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, max_length=50)
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().lower()
        allowed = {"trial", "active", "trialing", "past_due", "unpaid", "canceled", "inactive"}
        if normalized not in allowed:
            raise ValueError("Invalid subscription status")
        return normalized


class AdminSubscriptionResponse(BaseModel):
    """Admin-facing subscription details in update responses."""

    plan: str
    status: str
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool

    model_config = {"from_attributes": True}


class AdminUserUpdateResponse(BaseModel):
    """Response schema for admin mega update endpoint."""

    user: UserResponse
    subscription: Optional[AdminSubscriptionResponse] = None
    changed_fields: dict


AdminUserUpdateRequest.model_rebuild()
