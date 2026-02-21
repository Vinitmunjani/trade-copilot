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

@app.get("/health")
async def health():
    return {"status": "healthy", "redis": "connected", "websocket_connections": 0}

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

@app.get("/api/v1/stats")
async def get_stats():
    t = list(trades.values())
    winning = [x for x in t if x.get("pnl", 0) > 0]
    return {"total_trades": len(t), "winning_trades": len(winning), "total_pnl": sum(x.get("pnl", 0) for x in t), "win_rate": len(winning)/len(t) if t else 0, "ai_score": 85}
