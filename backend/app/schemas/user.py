from typing import Optional, Union
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


class TradingAccountResponse(BaseModel):
    """Schema for trading account connection response."""
    connected: bool
    account_id: Optional[str] = None
    login: Optional[str] = None
    server: Optional[str] = None
    platform: Optional[str] = None
    connection_status: Optional[str] = None
    message: Optional[str] = None

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
