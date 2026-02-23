#!/bin/bash
# Download and setup MT5 terminal in Docker for Wine

set -e

BROKER=${1:-"Exness"}
DOWNLOAD_URL=""

echo "[MT5 Setup] Installing MT5 Terminal for $BROKER..."

# Determine download URL based on broker
case $BROKER in
    "Exness")
        DOWNLOAD_URL="https://download.exness.com/en/terminal/mt5/exness-terminal.exe"
        ;;
    "ICMarkets")
        DOWNLOAD_URL="https://download.icmarkets.com/mt5/ic-markets-terminal.exe"
        ;;
    "XM")
        DOWNLOAD_URL="https://download.xm.com/mt5/xm-terminal.exe"
        ;;
    *)
        echo "[MT5 Setup] Unknown broker: $BROKER"
        exit 1
        ;;
esac

echo "[MT5 Setup] Downloading from: $DOWNLOAD_URL"

# Download terminal
cd /app
wget -q --show-progress "$DOWNLOAD_URL" -O terminal.exe || \
    curl -L -o terminal.exe "$DOWNLOAD_URL"

if [ ! -f terminal.exe ]; then
    echo "[MT5 Setup] Failed to download terminal"
    exit 1
fi

echo "[MT5 Setup] Terminal downloaded ($(stat -f%z terminal.exe 2>/dev/null || stat -c%s terminal.exe) bytes)"

# Setup Wine environment
export WINEARCH=win64
export WINEPREFIX=/root/.wine

echo "[MT5 Setup] Setting up Wine prefix..."
wineboot --init 2>/dev/null || true
sleep 5

# Install terminal
echo "[MT5 Setup] Installing MT5 terminal..."
wine terminal.exe /S /D=/root/.wine/drive_c/Program\ Files/MT5 || true
sleep 10

# Check if installation worked
if [ -f "/root/.wine/drive_c/Program Files/MT5/terminal.exe" ]; then
    echo "[MT5 Setup] ✅ MT5 terminal installed successfully!"
    ls -lh "/root/.wine/drive_c/Program Files/MT5/terminal.exe"
else
    echo "[MT5 Setup] ⚠️ Terminal installation uncertain - may need manual verification"
fi

echo "[MT5 Setup] Complete!"
