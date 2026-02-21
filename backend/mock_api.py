"""Minimal mock API for MVP testing - bypasses all import/compatibility issues."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from datetime import datetime

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

@app.post("/api/v1/auth/register", response_model=TokenResponse)
async def register(user: UserCreate):
    """Register a new user."""
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user
    user_id = str(uuid.uuid4())
    users_db[user.email] = {
        "id": user_id,
        "email": user.email,
        "password": user.password,
    }
    
    # Return mock token
    return {
        "access_token": f"mock_token_{user_id}",
        "token_type": "bearer",
    }

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(email: str, password: str):
    """Login user."""
    if email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = users_db[email]
    if user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "access_token": f"mock_token_{user['id']}",
        "token_type": "bearer",
    }

@app.post("/api/v1/trades", response_model=TradeResponse)
async def create_trade(trade: TradeCreate):
    """Create a trade."""
    trade_id = str(uuid.uuid4())
    
    # Mock P&L calculation
    pnl = 0.0
    if trade.exit_price:
        if trade.direction == "BUY":
            pnl = (trade.exit_price - trade.entry_price) * trade.lot_size
        else:
            pnl = (trade.entry_price - trade.exit_price) * trade.lot_size
    
    trades_db[trade_id] = {
        "id": trade_id,
        "user_id": "mock_user",
        "symbol": trade.symbol,
        "direction": trade.direction,
        "entry_price": trade.entry_price,
        "exit_price": trade.exit_price,
        "lot_size": trade.lot_size,
        "pnl": pnl,
    }
    
    return trades_db[trade_id]

@app.get("/api/v1/trades", response_model=list)
async def get_trades():
    """Get all trades."""
    return list(trades_db.values())

@app.get("/api/v1/stats", response_model=dict)
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
