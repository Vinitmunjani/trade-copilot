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

# Start dbus (required by Wine)
echo "[MT5-Engine] Starting dbus..."
dbus-daemon --session --print-address > /tmp/dbus.log 2>&1 &
sleep 1

# Initialize Wine if needed
if [ ! -d "/root/.wine/drive_c" ]; then
    echo "[MT5-Engine] Initializing Wine prefix..."
    wineboot --init > /tmp/wine_init.log 2>&1
    sleep 5
fi

# Start the API server
echo "[MT5-Engine] Starting Flask API server..."
python3 /app/api_server.py > /tmp/api.log 2>&1 &
API_PID=$!
sleep 2

# Check if MT5 is installed
if [ ! -f "/root/.wine/drive_c/Program Files/MT5/terminal.exe" ]; then
    echo "[MT5-Engine] MT5 not found. Running setup..."
    /app/setup_mt5.sh "$BROKER" 2>&1 | tee /tmp/setup.log
fi

# Launch MT5 terminal
if [ ! -z "$LOGIN" ] && [ ! -z "$PASSWORD" ]; then
    echo "[MT5-Engine] Launching MT5 terminal..."
    echo "[MT5-Engine] Credentials: Login=$LOGIN, Server=$SERVER"
    
    # Start terminal with credentials
    # Note: MT5 may need time to load before accepting input
    wine "/root/.wine/drive_c/Program Files/MT5/terminal.exe" \
        --login "$LOGIN" \
        --password "$PASSWORD" \
        --server "$SERVER" \
        > /tmp/terminal.log 2>&1 &
    
    TERMINAL_PID=$!
    sleep 10
    
    # Wait for EA to be loaded
    echo "[MT5-Engine] Waiting for EA to load..."
    sleep 5
    
    echo "[MT5-Engine] ✅ MT5 Terminal running (PID: $TERMINAL_PID)"
    echo "[MT5-Engine] API available on port 5000"
    echo "[MT5-Engine] Monitoring for trade events..."
    
    # Keep container alive
    wait $TERMINAL_PID
else
    echo "[MT5-Engine] No credentials provided - starting in API-only mode"
    echo "[MT5-Engine] API available on port 5000"
    echo "[MT5-Engine] Use POST /login to trigger terminal login"
    
    # Wait indefinitely
    wait $API_PID
fi
