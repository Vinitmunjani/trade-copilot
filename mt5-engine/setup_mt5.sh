#!/bin/bash
# Setup MT5 terminal in Wine (supports terminal64.exe or terminal.exe)

set -e

BROKER=${1:-"Exness"}

echo "[MT5 Setup] ============================================"
echo "[MT5 Setup] Installing MT5 Terminal for $BROKER"
echo "[MT5 Setup] ============================================"

export WINEARCH=win64
export WINEPREFIX=/root/.wine

# Look for terminal executable (support both 32-bit and 64-bit)
TERMINAL_EXE=""

if [ -f "/app/terminal/terminal64.exe" ]; then
    TERMINAL_EXE="/app/terminal/terminal64.exe"
    echo "[MT5 Setup] Found terminal64.exe"
elif [ -f "/app/terminal/terminal.exe" ]; then
    TERMINAL_EXE="/app/terminal/terminal.exe"
    echo "[MT5 Setup] Found terminal.exe"
fi

# Try to download if not found
if [ -z "$TERMINAL_EXE" ] || [ ! -s "$TERMINAL_EXE" ]; then
    echo "[MT5 Setup] Terminal not found, attempting download..."
    /app/download_mt5.sh "$BROKER" 2>&1 | tee /tmp/download.log || true
    
    # Check again after download
    if [ -f "/app/terminal/terminal64.exe" ] && [ -s "/app/terminal/terminal64.exe" ]; then
        TERMINAL_EXE="/app/terminal/terminal64.exe"
    elif [ -f "/app/terminal/terminal.exe" ] && [ -s "/app/terminal/terminal.exe" ]; then
        TERMINAL_EXE="/app/terminal/terminal.exe"
    fi
fi

# Check if terminal exists
if [ -z "$TERMINAL_EXE" ] || [ ! -f "$TERMINAL_EXE" ] || [ ! -s "$TERMINAL_EXE" ]; then
    echo "[MT5 Setup] ⚠️  Terminal.exe not available"
    echo "[MT5 Setup] Starting in API-only mode"
    echo "[MT5 Setup] To use real MT5:"
    echo "[MT5 Setup] 1. Download terminal64.exe from broker website"
    echo "[MT5 Setup] 2. Add to /mt5-engine/terminal64.exe"
    echo "[MT5 Setup] 3. Rebuild Docker image"
    exit 0
fi

echo "[MT5 Setup] Using: $TERMINAL_EXE"
echo "[MT5 Setup] File size: $(stat -c%s "$TERMINAL_EXE" 2>/dev/null || stat -f%z "$TERMINAL_EXE") bytes"

# Initialize Wine if needed
if [ ! -d "/root/.wine/drive_c" ]; then
    echo "[MT5 Setup] Initializing Wine prefix..."
    wineboot --init 2>/dev/null || true
    sleep 5
fi

# Install terminal
echo "[MT5 Setup] Installing MT5 terminal in Wine..."
cd /tmp

# Copy terminal to /tmp for installation
cp "$TERMINAL_EXE" /tmp/terminal.exe

# Run installer (silent mode)
echo "[MT5 Setup] Running installer..."
wine /tmp/terminal.exe /S /D="C:\\Program Files\\MT5" 2>&1 | grep -v "fixme\|warn" || true

sleep 10

# Verify installation
if [ -f "/root/.wine/drive_c/Program Files/MT5/terminal.exe" ]; then
    echo "[MT5 Setup] ✅ MT5 terminal installed successfully!"
    ls -lh "/root/.wine/drive_c/Program Files/MT5/terminal.exe"
    INSTALL_PATH="/root/.wine/drive_c/Program Files/MT5/terminal.exe"
elif [ -f "/root/.wine/drive_c/Program Files/MT5/terminal64.exe" ]; then
    echo "[MT5 Setup] ✅ MT5 terminal (64-bit) installed successfully!"
    ls -lh "/root/.wine/drive_c/Program Files/MT5/terminal64.exe"
    INSTALL_PATH="/root/.wine/drive_c/Program Files/MT5/terminal64.exe"
else
    echo "[MT5 Setup] ⚠️ Terminal installation may have failed"
    echo "[MT5 Setup] Will attempt to run from original location"
    INSTALL_PATH="$TERMINAL_EXE"
fi

echo "[MT5 Setup] Terminal path: $INSTALL_PATH"
echo "[MT5 Setup] Complete!"
