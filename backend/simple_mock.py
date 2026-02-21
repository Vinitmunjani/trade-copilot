"""Ultra-simple mock API - no Pydantic, no validation issues."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid

app = FastAPI(title="Trade Co-Pilot")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

users = {}
trades = {}
accounts = {}

@app.get("/health")
async def health():
    return {"status": "healthy", "redis": "connected", "websocket_connections": 0}

# AUTH ENDPOINTS
@app.post("/api/v1/auth/register")
async def register(email: str = None, password: str = None, confirm_password: str = None):
    """Register - accept form or JSON body."""
    if not email or not password:
        return {"detail": "Missing fields"}, 422
    if password != confirm_password:
        return {"detail": "Passwords don't match"}, 400
    if email in users:
        return {"detail": "User exists"}, 400
    
    user_id = str(uuid.uuid4())
    users[email] = {"id": user_id, "password": password}
    return {"access_token": f"token_{user_id}", "token_type": "bearer"}

@app.post("/api/v1/auth/login")
async def login(email: str = None, password: str = None):
    """Login."""
    if email not in users or users[email]["password"] != password:
        return {"detail": "Invalid credentials"}, 401
    return {"access_token": f"token_{users[email]['id']}", "token_type": "bearer"}

@app.get("/api/v1/auth/me")
async def get_me():
    """Get current user."""
    return {"id": str(uuid.uuid4()), "email": "user@example.com"}

# ACCOUNT ENDPOINTS
@app.post("/api/v1/account/connect")
async def connect_account(broker: str = None, login: str = None, password: str = None, server: str = None):
    """Connect broker account."""
    if not broker or not login:
        return {"detail": "Missing broker or login"}, 422
    
    account_id = str(uuid.uuid4())
    accounts[account_id] = {
        "id": account_id,
        "broker": broker,
        "login": login,
        "server": server or "Demo",
        "status": "connected"
    }
    return {
        "id": account_id,
        "broker": broker,
        "login": login,
        "server": server or "Demo",
        "status": "connected"
    }

@app.get("/api/v1/account/list")
async def list_accounts():
    """Get all connected accounts."""
    return list(accounts.values())

@app.get("/api/v1/account/{account_id}")
async def get_account(account_id: str):
    """Get account details."""
    if account_id in accounts:
        return accounts[account_id]
    return {"detail": "Account not found"}, 404

@app.delete("/api/v1/account/{account_id}")
async def disconnect_account(account_id: str):
    """Disconnect account."""
    if account_id in accounts:
        del accounts[account_id]
        return {"status": "disconnected"}
    return {"detail": "Account not found"}, 404

# TRADES ENDPOINTS
@app.post("/api/v1/trades")
async def create_trade(symbol: str = "EURUSD", direction: str = "BUY", entry_price: float = 1.0, exit_price: float = None, lot_size: float = 1.0):
    """Create trade."""
    trade_id = str(uuid.uuid4())
    pnl = 0.0
    if exit_price:
        pnl = (exit_price - entry_price) * lot_size if direction == "BUY" else (entry_price - exit_price) * lot_size
    trades[trade_id] = {"id": trade_id, "symbol": symbol, "direction": direction, "entry_price": entry_price, "exit_price": exit_price, "lot_size": lot_size, "pnl": pnl}
    return trades[trade_id]

@app.get("/api/v1/trades")
async def get_trades():
    return list(trades.values())

@app.get("/api/v1/trades/{trade_id}")
async def get_trade(trade_id: str):
    if trade_id in trades:
        return trades[trade_id]
    return {"detail": "Trade not found"}, 404

@app.put("/api/v1/trades/{trade_id}")
async def update_trade(trade_id: str, exit_price: float = None):
    """Close/update trade."""
    if trade_id not in trades:
        return {"detail": "Trade not found"}, 404
    
    if exit_price:
        trade = trades[trade_id]
        trade["exit_price"] = exit_price
        if trade["direction"] == "BUY":
            trade["pnl"] = (exit_price - trade["entry_price"]) * trade["lot_size"]
        else:
            trade["pnl"] = (trade["entry_price"] - exit_price) * trade["lot_size"]
    
    return trades[trade_id]

@app.delete("/api/v1/trades/{trade_id}")
async def delete_trade(trade_id: str):
    if trade_id in trades:
        del trades[trade_id]
        return {"status": "deleted"}
    return {"detail": "Trade not found"}, 404

# STATS ENDPOINTS
@app.get("/api/v1/stats")
async def get_stats():
    t = list(trades.values())
    winning = [x for x in t if x.get("pnl", 0) > 0]
    losing = [x for x in t if x.get("pnl", 0) < 0]
    total_pnl = sum(x.get("pnl", 0) for x in t)
    return {
        "total_trades": len(t),
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "total_pnl": total_pnl,
        "win_rate": len(winning)/len(t) if t else 0,
        "ai_score": 85,
        "behavioral_alerts": 0
    }

@app.get("/api/v1/stats/daily")
async def get_daily_stats():
    """Get daily stats."""
    return {
        "date": "2026-02-21",
        "trades": len(trades),
        "pnl": sum(x.get("pnl", 0) for x in trades.values()),
        "win_rate": 0.65,
        "ai_score": 88
    }

# RULES ENDPOINTS
@app.post("/api/v1/rules")
async def set_rules(max_risk_percent: float = 2.0, max_daily_loss: float = 5.0):
    """Set trading rules."""
    return {
        "max_risk_percent": max_risk_percent,
        "max_daily_loss": max_daily_loss,
        "status": "saved"
    }

@app.get("/api/v1/rules")
async def get_rules():
    """Get trading rules."""
    return {
        "max_risk_percent": 2.0,
        "max_daily_loss": 5.0,
        "max_trades_per_day": 10,
        "min_risk_reward": 1.5
    }

# ANALYSIS ENDPOINTS
@app.post("/api/v1/analysis/trade")
async def analyze_trade(symbol: str = "EURUSD", direction: str = "BUY", entry: float = 1.0, sl: float = 0.99, tp: float = 1.01):
    """Analyze trade setup."""
    return {
        "symbol": symbol,
        "direction": direction,
        "entry": entry,
        "stop_loss": sl,
        "take_profit": tp,
        "risk_reward": abs(tp - entry) / abs(entry - sl),
        "ai_score": 82,
        "recommendation": "GOOD",
        "flags": []
    }

@app.get("/api/v1/analysis/performance")
async def get_performance():
    """Get performance analysis."""
    return {
        "monthly_return": 2.5,
        "sharpe_ratio": 1.8,
        "max_drawdown": 8.5,
        "win_rate": 0.65,
        "profit_factor": 1.95,
        "behavioral_score": 78
    }
