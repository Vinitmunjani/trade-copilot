#!/bin/bash
set -e

BROKER=${BROKER:-"Exness"}
LOGIN=${LOGIN:-""}
PASSWORD=${PASSWORD:-""}
SERVER=${SERVER:-""}
USER_ID=${USER_ID:-"user_1"}

echo "[MT5-Engine] ============================================"
echo "[MT5-Engine] Starting MT5 Terminal Container"
echo "[MT5-Engine] Broker: $BROKER | User: $USER_ID"
echo "[MT5-Engine] ============================================"

export DISPLAY=:99
export WINEARCH=win64
export WINEPREFIX=/root/.wine

# Start Xvfb (virtual X11 display)
echo "[MT5-Engine] Starting X server (Xvfb)..."
Xvfb :99 -screen 0 1024x768x24 > /tmp/xvfb.log 2>&1 &
XVFB_PID=$!
sleep 2

# Start the API server first (it doesn't require MT5)
echo "[MT5-Engine] Starting Flask API server on port 5000..."
python3 /app/api_server.py > /tmp/api.log 2>&1 &
API_PID=$!
sleep 2

echo "[MT5-Engine] API Server started (PID: $API_PID)"
echo "[MT5-Engine] Health endpoint: /health"
echo "[MT5-Engine] Trades endpoint: /trades"

# Setup MT5 if credentials provided
if [ ! -z "$LOGIN" ] && [ ! -z "$PASSWORD" ]; then
    echo "[MT5-Engine] Setting up MT5 terminal..."
    
    # Run setup (handles download and installation)
    /app/setup_mt5.sh "$BROKER" 2>&1 | tee /tmp/setup.log || true
    
    # Check if MT5 is available
    if [ -f "/root/.wine/drive_c/Program Files/MT5/terminal.exe" ] || [ -f "/app/terminal/terminal.exe" ]; then
        echo "[MT5-Engine] ✅ MT5 terminal available!"
        
        # Determine terminal path
        TERMINAL_PATH="/root/.wine/drive_c/Program Files/MT5/terminal.exe"
        if [ ! -f "$TERMINAL_PATH" ]; then
            TERMINAL_PATH="/app/terminal/terminal.exe"
        fi
        
        echo "[MT5-Engine] Launching MT5 with credentials..."
        echo "[MT5-Engine] Broker: $BROKER"
        echo "[MT5-Engine] Login: $LOGIN"
        echo "[MT5-Engine] Server: $SERVER"
        
        # Launch terminal in background
        wine "$TERMINAL_PATH" \
            --login "$LOGIN" \
            --password "$PASSWORD" \
            --server "$SERVER" \
            > /tmp/terminal.log 2>&1 &
        
        TERMINAL_PID=$!
        echo "[MT5-Engine] MT5 Terminal launched (PID: $TERMINAL_PID)"
        
        # Wait for terminal to initialize
        sleep 15
        
        echo "[MT5-Engine] ✅ Terminal initialized"
        echo "[MT5-Engine] Monitoring for trade events..."
        
        # Keep container alive - restart terminal if it crashes
        while true; do
            if ! kill -0 $TERMINAL_PID 2>/dev/null; then
                echo "[MT5-Engine] Terminal process died, restarting..."
                wine "$TERMINAL_PATH" \
                    --login "$LOGIN" \
                    --password "$PASSWORD" \
                    --server "$SERVER" \
                    > /tmp/terminal.log 2>&1 &
                TERMINAL_PID=$!
                sleep 10
            fi
            sleep 5
        done
    else
        echo "[MT5-Engine] ⚠️  MT5 terminal not available"
        echo "[MT5-Engine] Running in API-only mode"
        echo "[MT5-Engine] API available on port 5000"
        wait $API_PID
    fi
else
    echo "[MT5-Engine] No credentials provided - API-only mode"
    echo "[MT5-Engine] API available on port 5000"
    echo "[MT5-Engine] POST /login to manually trigger login"
    
    # Keep API running indefinitely
    wait $API_PID
fi
