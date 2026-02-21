"""Mock API with session persistence and MT5 connection."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid

app = FastAPI(title="Trade Co-Pilot")

# CORS with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent storage
users = {}
sessions = {}
accounts = {}
trades = {}

def get_or_create_session(token: str):
    """Get or create session from token."""
    if token and token in sessions:
        return sessions[token]
    return None

@app.get("/health")
async def health():
    return {"status": "healthy", "redis": "connected", "websocket_connections": 0}

# AUTH ENDPOINTS
@app.post("/api/v1/auth/register")
async def register(email: str = None, password: str = None, confirm_password: str = None):
    """Register - returns token."""
    if not email or not password:
        return {"detail": "Missing fields"}, 422
    if password != confirm_password:
        return {"detail": "Passwords don't match"}, 400
    if email in users:
        return {"detail": "User exists"}, 400
    
    user_id = str(uuid.uuid4())
    token = f"token_{user_id}_{uuid.uuid4().hex[:8]}"
    
    users[email] = {"id": user_id, "password": password, "email": email}
    sessions[token] = {"user_id": user_id, "email": email}
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": email}
    }

@app.post("/api/v1/auth/login")
async def login(email: str = None, password: str = None):
    """Login - returns persistent token."""
    if email not in users or users[email]["password"] != password:
        return {"detail": "Invalid credentials"}, 401
    
    user_id = users[email]["id"]
    token = f"token_{user_id}_{uuid.uuid4().hex[:8]}"
    sessions[token] = {"user_id": user_id, "email": email}
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": email}
    }

@app.get("/api/v1/auth/me")
async def get_me(authorization: str = None):
    """Get current user from token."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    token = authorization.replace("Bearer ", "").strip()
    session = get_or_create_session(token)
    
    if not session:
        return {"detail": "Invalid token"}, 401
    
    return {
        "id": session["user_id"],
        "email": session["email"]
    }

# ACCOUNT ENDPOINTS
@app.post("/api/v1/account/connect")
async def connect_account(broker: str = None, login: str = None, password: str = None, server: str = None, authorization: str = None):
    """Connect broker account."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    token = authorization.replace("Bearer ", "").strip()
    session = get_or_create_session(token)
    
    if not session:
        return {"detail": "Invalid token"}, 401
    
    if not broker or not login:
        return {"detail": "Missing broker or login"}, 422
    
    # Map broker to MT5 container port
    mt5_ports = {
        "ICMarkets": 5001,
        "Exness": 5002,
        "XM": 5003,
        "ic_markets": 5001,
        "exness": 5002,
        "xm": 5003,
    }
    
    mt5_port = mt5_ports.get(broker.lower(), 5001)
    
    # Create account record (mock connection - don't verify)
    account_id = str(uuid.uuid4())
    accounts[account_id] = {
        "id": account_id,
        "user_id": session["user_id"],
        "broker": broker,
        "login": login,
        "server": server or "Demo",
        "status": "connected",
        "mt5_port": mt5_port
    }
    
    return {
        "id": account_id,
        "broker": broker,
        "login": login,
        "server": server or "Demo",
        "status": "connected"
    }

@app.get("/api/v1/account/list")
async def list_accounts(authorization: str = None):
    """Get all connected accounts."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    token = authorization.replace("Bearer ", "").strip()
    session = get_or_create_session(token)
    
    if not session:
        return {"detail": "Invalid token"}, 401
    
    user_accounts = [a for a in accounts.values() if a["user_id"] == session["user_id"]]
    return user_accounts

@app.delete("/api/v1/account/{account_id}")
async def disconnect_account(account_id: str, authorization: str = None):
    """Disconnect account."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    if account_id in accounts:
        del accounts[account_id]
        return {"status": "disconnected"}
    return {"detail": "Account not found"}, 404

# TRADES ENDPOINTS
@app.post("/api/v1/trades")
async def create_trade(symbol: str = "EURUSD", direction: str = "BUY", entry_price: float = 1.0, exit_price: float = None, lot_size: float = 1.0, authorization: str = None):
    """Create trade."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    token = authorization.replace("Bearer ", "").strip()
    session = get_or_create_session(token)
    
    if not session:
        return {"detail": "Invalid token"}, 401
    
    trade_id = str(uuid.uuid4())
    pnl = 0.0
    if exit_price:
        pnl = (exit_price - entry_price) * lot_size if direction == "BUY" else (entry_price - exit_price) * lot_size
    
    trades[trade_id] = {
        "id": trade_id,
        "user_id": session["user_id"],
        "symbol": symbol,
        "direction": direction,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "lot_size": lot_size,
        "pnl": pnl
    }
    return trades[trade_id]

@app.get("/api/v1/trades")
async def get_trades(authorization: str = None):
    """Get user trades."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    token = authorization.replace("Bearer ", "").strip()
    session = get_or_create_session(token)
    
    if not session:
        return {"detail": "Invalid token"}, 401
    
    user_trades = [t for t in trades.values() if t["user_id"] == session["user_id"]]
    return user_trades

@app.put("/api/v1/trades/{trade_id}")
async def update_trade(trade_id: str, exit_price: float = None, authorization: str = None):
    """Close/update trade."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
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
async def delete_trade(trade_id: str, authorization: str = None):
    """Delete trade."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    if trade_id in trades:
        del trades[trade_id]
        return {"status": "deleted"}
    return {"detail": "Trade not found"}, 404

# STATS ENDPOINTS
@app.get("/api/v1/stats")
async def get_stats(authorization: str = None):
    """Get trading stats."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    token = authorization.replace("Bearer ", "").strip()
    session = get_or_create_session(token)
    
    if not session:
        return {"detail": "Invalid token"}, 401
    
    user_trades = [t for t in trades.values() if t["user_id"] == session["user_id"]]
    winning = [x for x in user_trades if x.get("pnl", 0) > 0]
    losing = [x for x in user_trades if x.get("pnl", 0) < 0]
    total_pnl = sum(x.get("pnl", 0) for x in user_trades)
    
    return {
        "total_trades": len(user_trades),
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "total_pnl": total_pnl,
        "win_rate": len(winning)/len(user_trades) if user_trades else 0,
        "ai_score": 85,
        "behavioral_alerts": 0
    }

@app.get("/api/v1/stats/daily")
async def get_daily_stats(authorization: str = None):
    """Get daily stats."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    return {
        "date": "2026-02-21",
        "trades": 3,
        "pnl": 150.50,
        "win_rate": 0.67,
        "ai_score": 88
    }

# RULES ENDPOINTS
@app.post("/api/v1/rules")
async def set_rules(max_risk_percent: float = 2.0, max_daily_loss: float = 5.0, authorization: str = None):
    """Set trading rules."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    return {
        "max_risk_percent": max_risk_percent,
        "max_daily_loss": max_daily_loss,
        "status": "saved"
    }

@app.get("/api/v1/rules")
async def get_rules(authorization: str = None):
    """Get trading rules."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    return {
        "max_risk_percent": 2.0,
        "max_daily_loss": 5.0,
        "max_trades_per_day": 10,
        "min_risk_reward": 1.5
    }

# ANALYSIS ENDPOINTS
@app.post("/api/v1/analysis/trade")
async def analyze_trade(symbol: str = "EURUSD", direction: str = "BUY", entry: float = 1.0, sl: float = 0.99, tp: float = 1.01, authorization: str = None):
    """Analyze trade setup."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    return {
        "symbol": symbol,
        "direction": direction,
        "entry": entry,
        "stop_loss": sl,
        "take_profit": tp,
        "risk_reward": abs(tp - entry) / abs(entry - sl) if entry != sl else 0,
        "ai_score": 82,
        "recommendation": "GOOD",
        "flags": []
    }

@app.get("/api/v1/analysis/performance")
async def get_performance(authorization: str = None):
    """Get performance analysis."""
    if not authorization:
        return {"detail": "Not authenticated"}, 401
    
    return {
        "monthly_return": 2.5,
        "sharpe_ratio": 1.8,
        "max_drawdown": 8.5,
        "win_rate": 0.65,
        "profit_factor": 1.95,
        "behavioral_score": 78
    }
