"""Flask API server for MT5 terminal control and data retrieval."""
from flask import Flask, jsonify, request
import os
import json
import time
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# Store for trades captured by EA
TRADES_FILE = "/tmp/mt5_trades.json"
ACCOUNT_FILE = "/tmp/mt5_account.json"
TERMINAL_STATE_FILE = "/tmp/mt5_state.json"

def get_trades():
    """Get trades from EA output file."""
    if os.path.exists(TRADES_FILE):
        try:
            with open(TRADES_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def get_account_info():
    """Get account info from EA output file."""
    if os.path.exists(ACCOUNT_FILE):
        try:
            with open(ACCOUNT_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def get_terminal_state():
    """Get terminal login state."""
    if os.path.exists(TERMINAL_STATE_FILE):
        try:
            with open(TERMINAL_STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"logged_in": False}
    return {"logged_in": False}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    broker = os.getenv('BROKER', 'unknown')
    return jsonify({
        "status": "ok",
        "broker": broker,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/account', methods=['GET'])
def get_account():
    """Get account information."""
    login = request.args.get('login')
    account_info = get_account_info()
    
    if not account_info:
        return jsonify({
            "status": "error",
            "message": "Terminal not logged in or account data unavailable"
        }), 404
    
    return jsonify({
        "status": "success",
        "account_info": account_info
    })

@app.route('/trades', methods=['GET'])
def get_open_trades():
    """Get open trades from terminal."""
    login = request.args.get('login')
    trades = get_trades()
    
    return jsonify({
        "status": "success",
        "trades": trades,
        "count": len(trades),
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/login', methods=['POST'])
def terminal_login():
    """Trigger MT5 terminal login."""
    data = request.json
    login = data.get('login')
    password = data.get('password')
    server = data.get('server')
    
    # In real implementation, would use pyautogui to:
    # 1. Launch MT5 terminal
    # 2. Wait for login window
    # 3. Input credentials
    # 4. Submit
    
    # For now, return success (EA will handle actual login)
    state = {
        "logged_in": True,
        "login": login,
        "server": server,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with open(TERMINAL_STATE_FILE, 'w') as f:
        json.dump(state, f)
    
    return jsonify({
        "status": "success",
        "message": "Login request sent to terminal"
    })

@app.route('/trades/new', methods=['POST'])
def new_trade_notification():
    """Receive trade notification from EA."""
    data = request.json
    
    # This endpoint is called by the TradeMonitor EA
    # when a new trade is placed
    
    trades = get_trades()
    trades.append({
        "ticket": data.get('ticket'),
        "symbol": data.get('symbol'),
        "type": data.get('type'),
        "open_price": data.get('open_price'),
        "volume": data.get('volume'),
        "open_time": data.get('open_time'),
        "comment": data.get('comment')
    })
    
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades, f)
    
    return jsonify({"status": "received"})

@app.route('/account/update', methods=['POST'])
def account_update_notification():
    """Receive account info update from EA."""
    data = request.json
    
    # This endpoint is called by the TradeMonitor EA
    # when account info changes
    
    with open(ACCOUNT_FILE, 'w') as f:
        json.dump(data, f)
    
    return jsonify({"status": "received"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
