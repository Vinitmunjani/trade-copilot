#!/bin/bash
set -e

echo "[MT5-Engine] Starting headless MT5 terminal..."

# Set up display
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
sleep 2

# Initialize Wine environment
export WINEPREFIX=/root/.wine
export WINEARCH=win64

# Download & install MT5
if [ ! -f "/mt5/terminal.exe" ]; then
    echo "[MT5-Engine] Installing MT5..."
    cd /mt5
    wine mt5setup.exe /S /D=/mt5
    sleep 30
fi

# Copy Expert Advisor to terminal folder
cp /mt5/ea/TradeMonitor.mq5 /mt5/MQL5/Experts/

# Start MT5 terminal in headless mode
wine /mt5/terminal.exe &
MT5_PID=$!

# Monitor health
echo "[MT5-Engine] Health monitoring active (PID: $$)"
python3 /app/scripts/health_monitor.py

# Keep container alive
wait $MT5_PID
