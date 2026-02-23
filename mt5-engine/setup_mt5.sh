#!/bin/bash
# Setup MT5 terminal in Wine

set -e

BROKER=${1:-"Exness"}

echo "[MT5 Setup] ============================================"
echo "[MT5 Setup] Installing MT5 Terminal for $BROKER"
echo "[MT5 Setup] ============================================"

export WINEARCH=win64
export WINEPREFIX=/root/.wine

# Download terminal if not present
if [ ! -f "/app/terminal/terminal.exe" ]; then
    echo "[MT5 Setup] Terminal not found, attempting download..."
    /app/download_mt5.sh "$BROKER" || true
fi

# Check if terminal exists
if [ ! -f "/app/terminal/terminal.exe" ]; then
    echo "[MT5 Setup] ⚠️  Terminal.exe not available"
    echo "[MT5 Setup] Starting in API-only mode"
    echo "[MT5 Setup] To use real MT5:"
    echo "[MT5 Setup] 1. Download terminal.exe from broker website"
    echo "[MT5 Setup] 2. Add to /mt5-engine/terminal.exe"
    echo "[MT5 Setup] 3. Rebuild Docker image"
    exit 0
fi

echo "[MT5 Setup] Found terminal.exe at /app/terminal/terminal.exe"
echo "[MT5 Setup] Terminal size: $(stat -c%s /app/terminal/terminal.exe 2>/dev/null || stat -f%z /app/terminal/terminal.exe) bytes"

# Initialize Wine if needed
if [ ! -d "/root/.wine/drive_c" ]; then
    echo "[MT5 Setup] Initializing Wine prefix..."
    wineboot --init 2>/dev/null || true
    sleep 5
fi

# Install terminal
echo "[MT5 Setup] Installing MT5 terminal in Wine..."
cd /app/terminal

# Silent install
wine terminal.exe /S /D="C:\\Program Files\\MT5" 2>&1 | grep -v "fixme\|warn" || true

sleep 10

# Verify installation
if [ -f "/root/.wine/drive_c/Program Files/MT5/terminal.exe" ]; then
    echo "[MT5 Setup] ✅ MT5 terminal installed successfully!"
    ls -lh "/root/.wine/drive_c/Program Files/MT5/terminal.exe"
else
    echo "[MT5 Setup] ⚠️ Terminal installation uncertain"
    echo "[MT5 Setup] Will attempt to run from /app/terminal/terminal.exe"
fi

echo "[MT5 Setup] Complete!"
