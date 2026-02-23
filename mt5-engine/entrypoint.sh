#!/bin/bash
set -e

BROKER=${BROKER:-"Exness"}
LOGIN=${LOGIN:-""}
PASSWORD=${PASSWORD:-""}
SERVER=${SERVER:-""}
USER_ID=${USER_ID:-"user_1"}

echo "[MT5-Engine] Starting container for $BROKER (User: $USER_ID)"

# Start Xvfb (virtual display)
echo "[MT5-Engine] Starting Xvfb..."
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99
sleep 2

# Start the API server
echo "[MT5-Engine] Starting API server..."
python3 /app/api_server.py &
API_PID=$!
sleep 2

# TODO: Start MT5 terminal with credentials
# This would require:
# 1. MT5 terminal executable in Wine
# 2. Terminal.exe launch with credentials
# 3. EA compilation and loading
# 4. Monitoring for trade updates

# For MVP testing: just run the API server and mock responses
echo "[MT5-Engine] Container running. API available on :5000"
echo "[MT5-Engine] To connect: POST /login with login/password/server"

# Keep container alive
wait $API_PID
