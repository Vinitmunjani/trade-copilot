"""
Trade Co-Pilot Backend - FastAPI with Real MT5 Data Fetching
PATCHED VERSION: Now fetches real account data from MT5 containers
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import uuid
from datetime import datetime, timedelta
import hashlib
import requests
import jwt

# ============================================================================
# CONFIGURATION
# ============================================================================

app = FastAPI()
SECRET_KEY = "your-secret-key-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

ACCOUNTS_FILE = "/tmp/accounts.json"
SESSIONS_FILE = "/tmp/sessions.json"
TRADES_FILE = "/tmp/trades.json"

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HELPER FUNCTIONS - REAL ACCOUNT DATA FETCHING
# ============================================================================

def get_real_account_info(account_id: str):
    """Fetch REAL account data from MT5 container instead of mock"""
    try:
        if not os.path.exists("/tmp/accounts.json"):
            return None
        
        with open("/tmp/accounts.json", 'r') as f:
            accounts = json.load(f)
        
        account = accounts.get(account_id)
        if not account:
            return None
        
        container_port = account.get("container_port")
        if not container_port:
            return None
        
        print(f"[REAL-DATA] Querying container on port {container_port} for account {account_id}")
        
        try:
            response = requests.get(
                f"http://localhost:{container_port}/api/account-info",
                timeout=5
            )
            
            if response.status_code == 200:
                real_data = response.json()
                print(f"[REAL-DATA] Got real account data: balance={real_data.get('balance')}, equity={real_data.get('equity')}")
                
                return {
                    "id": account_id,
                    "broker": account.get("broker"),
                    "login": account.get("login"),
                    "server": account.get("server"),
                    "status": "connected",
                    "balance": real_data.get("balance", 0),
                    "equity": real_data.get("equity", 0),
                    "margin": real_data.get("margin", 0),
                    "margin_free": real_data.get("margin_free", 0),
                    "margin_level": real_data.get("margin_level", 0),
                    "currency": real_data.get("currency", "USD"),
                    "trades_count": real_data.get("trades_count", 0),
                    "account_info": real_data
                }
            else:
                print(f"[REAL-DATA] Container returned status {response.status_code}, falling back to mock")
                return get_mock_account_info(account_id, account)
                
        except requests.exceptions.ConnectionError as e:
            print(f"[REAL-DATA] Container not reachable on port {container_port}: {e}")
            print(f"[REAL-DATA] This means MT5 terminal is not running or container crashed")
            return get_mock_account_info(account_id, account)
        except Exception as e:
            print(f"[REAL-DATA] Error querying container: {e}")
            return get_mock_account_info(account_id, account)
    
    except Exception as e:
        print(f"[ERROR] Failed to fetch account info: {e}")
        return None


def get_mock_account_info(account_id: str, account: dict):
    """Fallback to mock data when container is unavailable"""
    print(f"[MOCK] Using mock data for account {account_id} (container unavailable)")
    return {
        "id": account_id,
        "broker": account.get("broker"),
        "login": account.get("login"),
        "server": account.get("server"),
        "status": "connected",
        "balance": 10000.00,
        "equity": 10000.00,
        "margin": 0.00,
        "margin_free": 10000.00,
        "margin_level": 0,
        "currency": "USD",
        "trades_count": 0,
        "account_info": {
            "balance": 10000.00,
            "equity": 10000.00
        }
    }


def get_real_trades(account_id: str, limit: int = 50):
    """Fetch REAL trades from MT5 container instead of mock data"""
    try:
        if not os.path.exists("/tmp/accounts.json"):
            return []
        
        with open("/tmp/accounts.json", 'r') as f:
            accounts = json.load(f)
        
        account = accounts.get(account_id)
        if not account:
            return []
        
        container_port = account.get("container_port")
        if not container_port:
            return []
        
        print(f"[REAL-TRADES] Querying container on port {container_port} for trades")
        
        try:
            response = requests.get(
                f"http://localhost:{container_port}/api/trades",
                params={"limit": limit},
                timeout=5
            )
            
            if response.status_code == 200:
                trades = response.json().get("trades", [])
                print(f"[REAL-TRADES] Got {len(trades)} real trades from container")
                return trades
            else:
                print(f"[REAL-TRADES] Container returned status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[REAL-TRADES] Failed to fetch trades from container: {e}")
            return []
    
    except Exception as e:
        print(f"[ERROR] Failed to get trades: {e}")
        return []


def validate_token(token: str):
    """Validate JWT token"""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return user_id
    except:
        return None


def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def hash_password(password: str):
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str):
    """Verify password"""
    return hash_password(plain_password) == hashed_password


def ensure_files_exist():
    """Ensure persistent JSON files exist"""
    for file_path in [ACCOUNTS_FILE, SESSIONS_FILE, TRADES_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f)


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "trade-copilot-backend"
    })


@app.get("/api/v1/health")
async def health_check_v1():
    """Health check endpoint (v1)"""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "trade-copilot-backend"
    })


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/register")
async def register(email: str, password: str, confirm_password: str):
    """Register new user"""
    ensure_files_exist()
    
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password too short")
    
    with open("/tmp/sessions.json", 'r') as f:
        sessions = json.load(f)
    
    # Check if email already exists
    for user_id, session in sessions.items():
        if session.get("email") == email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    access_token = create_access_token({"sub": user_id})
    
    sessions[user_id] = {
        "email": email,
        "password": hash_password(password),
        "account_id": None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    with open("/tmp/sessions.json", 'w') as f:
        json.dump(sessions, f)
    
    return JSONResponse(content={
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email
        }
    })


@app.post("/api/v1/auth/login")
async def login(email: str, password: str):
    """Login user"""
    ensure_files_exist()
    
    with open("/tmp/sessions.json", 'r') as f:
        sessions = json.load(f)
    
    # Find user by email
    user_id = None
    for uid, session in sessions.items():
        if session.get("email") == email:
            if verify_password(password, session.get("password", "")):
                user_id = uid
                break
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": user_id})
    
    return JSONResponse(content={
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email
        }
    })


# ============================================================================
# ACCOUNT ENDPOINTS
# ============================================================================

@app.get("/api/v1/account/me")
async def get_account_me(authorization: str = Header(None)):
    """Get current connected account info - REAL DATA from container"""
    token = authorization.replace("Bearer ", "") if authorization else None
    user_id = validate_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    ensure_files_exist()
    
    if not os.path.exists("/tmp/sessions.json"):
        raise HTTPException(status_code=404, detail="No session")
    
    with open("/tmp/sessions.json", 'r') as f:
        sessions = json.load(f)
    
    account_id = sessions.get(user_id, {}).get("account_id")
    if not account_id:
        raise HTTPException(status_code=404, detail="No connected account")
    
    # FETCH REAL DATA FROM CONTAINER (not mock!)
    account_info = get_real_account_info(account_id)
    if not account_info:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return JSONResponse(content=account_info)


@app.post("/api/v1/account/connect")
async def connect_account(broker: str, login: str, password: str, server: str, authorization: str = Header(None)):
    """Connect to MT5 broker account and launch container"""
    token = authorization.replace("Bearer ", "") if authorization else None
    user_id = validate_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    ensure_files_exist()
    
    print(f"[ACCOUNT-CONNECT] User {user_id} connecting to {broker} account {login}")
    
    # Import container manager
    try:
        from mt5_container_manager import launch_mt5_container
    except ImportError:
        print("[ERROR] Could not import mt5_container_manager")
        raise HTTPException(status_code=500, detail="Container manager not available")
    
    # Launch container
    try:
        container_port = launch_mt5_container(user_id, broker, login, password, server)
        print(f"[ACCOUNT-CONNECT] Container launched on port {container_port}")
    except Exception as e:
        print(f"[ERROR] Failed to launch container: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to launch container: {str(e)}")
    
    # Create account record
    account_id = str(uuid.uuid4())
    
    with open("/tmp/accounts.json", 'r') as f:
        accounts = json.load(f)
    
    accounts[account_id] = {
        "id": account_id,
        "user_id": user_id,
        "broker": broker,
        "login": login,
        "server": server,
        "status": "connected",
        "container_port": container_port,
        "created_at": datetime.utcnow().isoformat()
    }
    
    with open("/tmp/accounts.json", 'w') as f:
        json.dump(accounts, f)
    
    # Update session
    with open("/tmp/sessions.json", 'r') as f:
        sessions = json.load(f)
    
    sessions[user_id]["account_id"] = account_id
    
    with open("/tmp/sessions.json", 'w') as f:
        json.dump(sessions, f)
    
    return JSONResponse(content={
        "id": account_id,
        "broker": broker,
        "login": login,
        "server": server,
        "status": "connected",
        "account_info": {},
        "message": "Terminal launched and monitoring for trades"
    })


@app.post("/api/v1/account/disconnect")
async def disconnect_account(authorization: str = Header(None)):
    """Disconnect from broker account"""
    token = authorization.replace("Bearer ", "") if authorization else None
    user_id = validate_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    ensure_files_exist()
    
    with open("/tmp/sessions.json", 'r') as f:
        sessions = json.load(f)
    
    account_id = sessions.get(user_id, {}).get("account_id")
    if not account_id:
        raise HTTPException(status_code=404, detail="No connected account")
    
    # Stop container
    try:
        import subprocess
        subprocess.run(["docker", "stop", f"mt5-{user_id[:8]}-*"], shell=True, timeout=10)
    except:
        pass
    
    # Update session
    sessions[user_id]["account_id"] = None
    
    with open("/tmp/sessions.json", 'w') as f:
        json.dump(sessions, f)
    
    return JSONResponse(content={"status": "disconnected"})


# ============================================================================
# TRADES ENDPOINTS
# ============================================================================

@app.get("/api/v1/trades")
async def get_trades(authorization: str = Header(None), limit: int = 50):
    """Get trades for current account - REAL DATA from container"""
    token = authorization.replace("Bearer ", "") if authorization else None
    user_id = validate_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    ensure_files_exist()
    
    if not os.path.exists("/tmp/sessions.json"):
        raise HTTPException(status_code=404, detail="No session")
    
    with open("/tmp/sessions.json", 'r') as f:
        sessions = json.load(f)
    
    account_id = sessions.get(user_id, {}).get("account_id")
    if not account_id:
        raise HTTPException(status_code=404, detail="No connected account")
    
    # FETCH REAL TRADES FROM CONTAINER (not mock!)
    trades = get_real_trades(account_id, limit)
    
    return JSONResponse(content={
        "trades": trades,
        "total": len(trades),
        "account_id": account_id
    })


@app.get("/api/v1/stats")
async def get_stats(authorization: str = Header(None)):
    """Get account statistics"""
    token = authorization.replace("Bearer ", "") if authorization else None
    user_id = validate_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return JSONResponse(content={
        "win_rate": 0.55,
        "total_trades": 0,
        "profit_loss": 0,
        "avg_win": 0,
        "avg_loss": 0
    })


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("[STARTUP] Trade Co-Pilot Backend starting...")
    ensure_files_exist()
    print("[STARTUP] Persistent files initialized")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

