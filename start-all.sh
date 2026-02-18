#!/bin/bash
# Kill old processes
pkill -f "uvicorn app.main" 2>/dev/null
pkill -f "next-server" 2>/dev/null
pkill -f cloudflared 2>/dev/null
sleep 2

# Start backend
cd /root/.openclaw/workspace/trade-copilot/backend
nohup ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
echo "Backend PID: $!"

# Start frontend
cd /root/.openclaw/workspace/trade-copilot/frontend
nohup npm run dev -- --hostname 0.0.0.0 > /tmp/frontend.log 2>&1 &
echo "Frontend PID: $!"

# Wait for services
sleep 6

# Start tunnel
nohup cloudflared tunnel --url http://localhost:80 > /tmp/tunnel.log 2>&1 &
echo "Tunnel PID: $!"

sleep 8

# Print status
echo ""
echo "=== STATUS ==="
curl -s http://localhost:8000/health && echo " ✅ Backend" || echo "❌ Backend"
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q 200 && echo "✅ Frontend" || echo "❌ Frontend"
grep "trycloudflare.com" /tmp/tunnel.log | tail -1
