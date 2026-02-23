#!/bin/bash
# Download MT5 terminal executables for different brokers

set -e

BROKER=${1:-"Exness"}
INSTALL_PATH="/app/terminal"

echo "[MT5 Download] Getting MT5 terminal for $BROKER..."

mkdir -p "$INSTALL_PATH"
cd "$INSTALL_PATH"

case $BROKER in
    "Exness")
        echo "[MT5 Download] Downloading Exness MT5..."
        # Try multiple sources
        wget -q --show-progress "https://download.exness.com/en/terminal/mt5/exness-terminal-latest.exe" -O terminal.exe 2>/dev/null || \
        wget -q --show-progress "https://www.exness.com/downloads/exness-terminal.exe" -O terminal.exe 2>/dev/null || \
        curl -L -o terminal.exe "https://download.exness.com/en/terminal/mt5/exness-terminal-latest.exe" 2>/dev/null || \
        echo "[MT5 Download] ⚠️ Could not download Exness terminal - network may be restricted"
        ;;
    "ICMarkets")
        echo "[MT5 Download] Downloading IC Markets MT5..."
        wget -q --show-progress "https://download.icmarkets.com/download/mt5/icmarkets-terminal.exe" -O terminal.exe 2>/dev/null || \
        curl -L -o terminal.exe "https://download.icmarkets.com/download/mt5/icmarkets-terminal.exe" 2>/dev/null || \
        echo "[MT5 Download] ⚠️ Could not download IC Markets terminal"
        ;;
    "XM")
        echo "[MT5 Download] Downloading XM MT5..."
        wget -q --show-progress "https://download.xm.com/download/mt5/xm-terminal.exe" -O terminal.exe 2>/dev/null || \
        curl -L -o terminal.exe "https://download.xm.com/download/mt5/xm-terminal.exe" 2>/dev/null || \
        echo "[MT5 Download] ⚠️ Could not download XM terminal"
        ;;
    *)
        echo "[MT5 Download] Unknown broker: $BROKER"
        exit 1
        ;;
esac

if [ -f "terminal.exe" ] && [ -s "terminal.exe" ]; then
    SIZE=$(stat -c%s "terminal.exe" 2>/dev/null || stat -f%z "terminal.exe" 2>/dev/null || echo "unknown")
    echo "[MT5 Download] ✅ Terminal downloaded ($SIZE bytes)"
    file terminal.exe
    ls -lh terminal.exe
else
    echo "[MT5 Download] ⚠️ Terminal not available - will need to be provided manually"
    echo "[MT5 Download] Please add terminal.exe to /mt5-engine/ and rebuild image"
fi
