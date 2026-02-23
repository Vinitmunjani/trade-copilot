from fastapi.responses import JSONResponse
"""Trade Co-Pilot Backend - MT5 Terminal Integration."""
from fastapi import Header, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
import os
from datetime import datetime
from mt5_container_manager import mt5_manager

app = FastAPI(title="Trade Co-Pilot")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent storage
ACCOUNTS_FILE = "/tmp/accounts.json"
USERS_FILE = "/tmp/users.json"
SESSIONS_FILE = "/tmp/sessions.json"
TRADES_FILE = "/tmp/trades.json"

users = {}
sessions = {}
accounts = {}
trades = {}

def load_from_file(filepath: str, default=None):
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except:
        pass
    return default or {}

def save_to_file(filepath: str, data: dict):
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving to {filepath}: {e}")

# Load persistent data
users = load_from_file(USERS_FILE, {})
sessions = load_from_file(SESSIONS_FILE, {})
accounts = load_from_file(ACCOUNTS_FILE, {})
trades = load_from_file(TRADES_FILE, {})

def get_or_create_session(token: str):
    if token and token in sessions:
        return sessions[token]
    return None

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ============ AUTH ENDPOINTS ============

@app.post("/api/v1/auth/register")
async def register(email: str = None, password: str = None, confirm_password: str = None):
    if not email or not password:
        return JSONResponse({"detail": "Missing fields"}, status_code=422)
    if password != confirm_password:
        return JSONResponse({"detail": "Passwords don't match"}, status_code=400)
    if email in users:
        return JSONResponse({"detail": "User exists"}, status_code=400)
    
    user_id = str(uuid.uuid4())
    token = f"token_{user_id}_{uuid.uuid4().hex[:8]}"
    
    users[email] = {"id": user_id, "password": password, "email": email}
    sessions[token] = {"user_id": user_id, "email": email}
    
    save_to_file(USERS_FILE, users)
    save_to_file(SESSIONS_FILE, sessions)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": email}
    }

@app.post("/api/v1/auth/login")
async def login(email: str = None, password: str = None):
    if email not in users or users[email]["password"] != password:
        return JSONResponse({"detail": "Invalid credentials"}, status_code=401)
    
    user_id = users[email]["id"]
    token = f"token_{user_id}_{uuid.uuid4().hex[:8]}"
    sessions[token] = {"user_id": user_id, "email": email}
    
    save_to_file(SESSIONS_FILE, sessions)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": email}
    }

@app.get("/api/v1/auth/me")
async def get_me(authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    token = authorization.replace("Bearer ", "").strip()
    session = get_or_create_session(token)
    
    if not session:
        return JSONResponse({"detail": "Invalid token"}, status_code=401)
    
    return {
        "id": session["user_id"],
        "email": session["email"]
    }

# ============ ACCOUNT ENDPOINTS ============

@app.post("/api/v1/account/connect")
async def connect_account(broker: str = None, login: str = None, password: str = None, server: str = None, authorization: str = Header(None)):
    """Connect to MT5 account - launches terminal and monitors for trades."""
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    token = authorization.replace("Bearer ", "").strip()
    session = get_or_create_session(token)
    
    if not session:
        return JSONResponse({"detail": "Invalid token"}, status_code=401)
    
    if not broker or not login or not password:
        return JSONResponse({"detail": "Missing broker, login, or password"}, status_code=422)
    
    user_id = session["user_id"]
    
    # Launch MT5 terminal in Docker
    print(f"Launching MT5 terminal: {broker} - {login}")
    result = mt5_manager.launch_terminal(user_id, broker, login, password, server or "Demo")
    
    if result["status"] == "failed":
        return JSONResponse({"detail": result.get("error", "Failed to launch terminal")}, status_code=400)
    
    # Get account info from terminal
    account_info = mt5_manager.get_account_info(user_id)
    
    # Store account record
    account_id = str(uuid.uuid4())
    accounts[account_id] = {
        "id": account_id,
        "user_id": user_id,
        "broker": broker,
        "login": login,
        "server": server or "Demo",
        "status": "connected",
        "container_id": result.get("container_id"),
        "port": result.get("port"),
        "account_info": account_info.get("account_info", {})
    }
    save_to_file(ACCOUNTS_FILE, accounts)
    
    return {
        "id": account_id,
        "broker": broker,
        "login": login,
        "server": server or "Demo",
        "status": "connected",
        "account_info": account_info.get("account_info", {}),
        "message": "Terminal launched and monitoring for trades"
    }

@app.get("/api/v1/account/list")
async def list_accounts(authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    token = authorization.replace("Bearer ", "").strip()
    session = get_or_create_session(token)
    
    if not session:
        return JSONResponse({"detail": "Invalid token"}, status_code=401)
    
    user_accounts = [a for a in accounts.values() if a["user_id"] == session["user_id"]]
    return user_accounts

@app.delete("/api/v1/account/{account_id}")
async def disconnect_account(account_id: str, authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    if account_id in accounts:
        # Stop the MT5 terminal
        user_id = accounts[account_id]["user_id"]
        mt5_manager.stop_terminal(user_id)
        
        del accounts[account_id]
        save_to_file(ACCOUNTS_FILE, accounts)
        return {"status": "disconnected"}
    return JSONResponse({"detail": "Account not found"}, status_code=404)

# ============ TRADES ENDPOINTS ============

@app.get("/api/v1/trades")
async def get_trades(authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    token = authorization.replace("Bearer ", "").strip()
    session = get_or_create_session(token)
    
    if not session:
        return JSONResponse({"detail": "Invalid token"}, status_code=401)
    
    user_id = session["user_id"]
    
    # Get trades from MT5 terminal
    all_trades = []
    user_accounts = [a for a in accounts.values() if a["user_id"] == user_id]
    
    for account in user_accounts:
        terminal_trades = mt5_manager.get_trades(user_id)
        all_trades.extend(terminal_trades)
    
    return all_trades

@app.post("/api/v1/trades")
async def create_trade(symbol: str = None, direction: str = None, entry_price: float = None, exit_price: float = None, lot_size: float = None, authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    token = authorization.replace("Bearer ", "").strip()
    session = get_or_create_session(token)
    
    if not session:
        return JSONResponse({"detail": "Invalid token"}, status_code=401)
    
    # Store trade record
    trade_id = str(uuid.uuid4())
    trades[trade_id] = {
        "id": trade_id,
        "user_id": session["user_id"],
        "symbol": symbol,
        "direction": direction,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "lot_size": lot_size,
    }
    save_to_file(TRADES_FILE, trades)
    return trades[trade_id]

@app.put("/api/v1/trades/{trade_id}")
async def update_trade(trade_id: str, exit_price: float = None, authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    if trade_id not in trades:
        return JSONResponse({"detail": "Trade not found"}, status_code=404)
    
    if exit_price:
        trade = trades[trade_id]
        trade["exit_price"] = exit_price
    
    save_to_file(TRADES_FILE, trades)
    return trades[trade_id]

@app.delete("/api/v1/trades/{trade_id}")
async def delete_trade(trade_id: str, authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    if trade_id in trades:
        del trades[trade_id]
        save_to_file(TRADES_FILE, trades)
        return {"status": "deleted"}
    return JSONResponse({"detail": "Trade not found"}, status_code=404)

# ============ STATS ENDPOINTS ============

@app.get("/api/v1/stats")
async def get_stats(authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    token = authorization.replace("Bearer ", "").strip()
    session = get_or_create_session(token)
    
    if not session:
        return JSONResponse({"detail": "Invalid token"}, status_code=401)
    
    user_trades = [t for t in trades.values() if t["user_id"] == session["user_id"]]
    
    return {
        "total_trades": len(user_trades),
        "winning_trades": 0,
        "losing_trades": 0,
        "total_pnl": 0,
        "win_rate": 0,
        "ai_score": 85,
        "behavioral_alerts": 0
    }

@app.get("/api/v1/stats/daily")
async def get_daily_stats(authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    return {
        "date": datetime.utcnow().isoformat(),
        "trades": 0,
        "pnl": 0,
        "win_rate": 0,
        "ai_score": 85
    }

# ============ RULES ENDPOINTS ============

@app.get("/api/v1/rules")
async def get_rules(authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    return {
        "max_risk_percent": 2.0,
        "max_daily_loss": 5.0,
        "max_trades_per_day": 10,
        "min_risk_reward": 1.5
    }

@app.post("/api/v1/rules")
async def set_rules(max_risk_percent: float = None, authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    return {"status": "saved"}

# ============ ANALYSIS ENDPOINTS ============

@app.post("/api/v1/analysis/trade")
async def analyze_trade(symbol: str = None, direction: str = None, entry: float = None, sl: float = None, tp: float = None, authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    return {
        "symbol": symbol,
        "direction": direction,
        "ai_score": 82,
        "recommendation": "GOOD",
        "flags": []
    }

@app.get("/api/v1/analysis/performance")
async def get_performance(authorization: str = Header(None)):
    if not authorization:
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    
    return {
        "monthly_return": 2.5,
        "sharpe_ratio": 1.8,
        "max_drawdown": 8.5,
        "win_rate": 0.65,
        "profit_factor": 1.95,
        "behavioral_score": 78
    }
