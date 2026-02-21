"""Minimal mock API for MVP testing - bypasses all import/compatibility issues."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from datetime import datetime
import json

app = FastAPI(title="Trade Co-Pilot Mock API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://vinitmunjanitradecopilot.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data storage
users_db = {}
trades_db = {}

class UserCreate(BaseModel):
    email: str
    password: str
    confirm_password: str
    
    class Config:
        extra = "allow"  # Allow extra fields

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TradeCreate(BaseModel):
    symbol: str
    direction: str
    entry_price: float
    exit_price: float = None
    lot_size: float

class TradeResponse(BaseModel):
    id: str
    user_id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: float = None
    lot_size: float
    pnl: float = 0.0

@app.get("/health", tags=["Health"])
async def health():
    """Health check."""
    return {"status": "healthy", "redis": "connected", "websocket_connections": 0}

@app.post("/api/v1/auth/register")
async def register(request: Request):
    """Register a new user - accept raw JSON to avoid Pydantic issues."""
    try:
        body = await request.json()
    except:
        raise HTTPException(status_code=422, detail="Invalid JSON")
    
    email = body.get("email")
    password = body.get("password")
    confirm_password = body.get("confirm_password")
    
    # Validate
    if not email or not password or not confirm_password:
        raise HTTPException(status_code=422, detail="Missing required fields")
    
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    if email in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user
    user_id = str(uuid.uuid4())
    users_db[email] = {
        "id": user_id,
        "email": email,
        "password": password,
    }
    
    # Return token
    return {
        "access_token": f"mock_token_{user_id}",
        "token_type": "bearer",
    }

@app.post("/api/v1/auth/login")
async def login(request: Request):
    """Login user."""
    body = await request.json()
    email = body.get("email")
    password = body.get("password")
    
    if email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = users_db[email]
    if user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "access_token": f"mock_token_{user['id']}",
        "token_type": "bearer",
    }

@app.post("/api/v1/trades")
async def create_trade(request: Request):
    """Create a trade."""
    body = await request.json()
    
    trade_id = str(uuid.uuid4())
    symbol = body.get("symbol", "EURUSD")
    direction = body.get("direction", "BUY")
    entry_price = float(body.get("entry_price", 1.0))
    exit_price = body.get("exit_price")
    lot_size = float(body.get("lot_size", 1.0))
    
    if exit_price:
        exit_price = float(exit_price)
    
    # Mock P&L calculation
    pnl = 0.0
    if exit_price:
        if direction == "BUY":
            pnl = (exit_price - entry_price) * lot_size
        else:
            pnl = (entry_price - exit_price) * lot_size
    
    trades_db[trade_id] = {
        "id": trade_id,
        "user_id": "mock_user",
        "symbol": symbol,
        "direction": direction,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "lot_size": lot_size,
        "pnl": pnl,
    }
    
    return trades_db[trade_id]

@app.get("/api/v1/trades")
async def get_trades():
    """Get all trades."""
    return list(trades_db.values())

@app.get("/api/v1/stats")
async def get_stats():
    """Get trading stats."""
    trades = list(trades_db.values())
    winning = [t for t in trades if t.get("pnl", 0) > 0]
    losing = [t for t in trades if t.get("pnl", 0) < 0]
    
    return {
        "total_trades": len(trades),
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "total_pnl": sum(t.get("pnl", 0) for t in trades),
        "win_rate": len(winning) / len(trades) if trades else 0,
        "ai_score": 85,
    }

@app.get("/docs")
async def docs():
    """OpenAPI docs."""
    return {"message": "See /openapi.json"}
