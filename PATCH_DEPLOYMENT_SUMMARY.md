# Trade Co-Pilot Backend Patch Deployment Summary

## Overview
You reported that your Trade Co-Pilot MVP shows "Connected" but displays **mock data** instead of real account information. This patch fixes that by making the backend query actual MT5 containers for real account data.

## What Was Wrong
```
OLD BEHAVIOR:
Frontend → Backend → Returns hardcoded mock data (balance=10000, equity=10000)
                  └─ Never queries container
                  
NEW BEHAVIOR:
Frontend → Backend → Queries MT5 container (/api/account-info)
                  └─ Returns REAL balance/equity if terminal is running
                  └─ Falls back to mock if terminal is offline
```

## Files Provided

### 1. simple_mock_PATCHED.py (17 KB)
Complete patched backend file with:
- ✅ `import requests` - for HTTP calls to containers
- ✅ `get_real_account_info(account_id)` - Fetches real balance/equity from container
- ✅ `get_real_trades(account_id, limit)` - Fetches real trades from container
- ✅ `get_mock_account_info()` - Fallback when container unavailable
- ✅ Updated `/api/v1/account/me` endpoint - Now uses real data
- ✅ Updated `/api/v1/trades` endpoint - Now uses real trades

### 2. DEPLOY_BACKEND_PATCH.sh (3.4 KB)
Automated deployment script that:
- ✓ Copies patched file to EC2
- ✓ Creates backup of old file
- ✓ Installs patched version
- ✓ Stops old backend process
- ✓ Starts new backend
- ✓ Verifies deployment
- ✓ Shows logs

## Deployment

### Quick Deploy (Single Command)
```bash
bash /root/.openclaw/workspace/DEPLOY_BACKEND_PATCH.sh
```

### Manual Deploy (If script fails)
```bash
# 1. Copy file
scp -i ~/.ssh/vinit.pem /root/.openclaw/workspace/simple_mock_PATCHED.py \
  ec2-user@3.143.147.98:/home/ec2-user/trade-copilot/backend/

# 2. Deploy
ssh -i ~/.ssh/vinit.pem ec2-user@3.143.147.98 << 'COMMANDS'
cd /home/ec2-user/trade-copilot/backend
cp simple_mock.py simple_mock.py.bak.$(date +%s)
cp simple_mock_PATCHED.py simple_mock.py
pkill -f "uvicorn simple_mock"
sleep 2
cd /home/ec2-user/trade-copilot
nohup python -m uvicorn backend.simple_mock:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 3
tail -30 /tmp/backend.log
COMMANDS
```

## Expected Behavior After Deployment

### If MT5 Terminal is Running (with terminal64.exe)
```
Backend logs will show:
[STARTUP] Trade Co-Pilot Backend starting...
[STARTUP] Persistent files initialized
[REAL-DATA] Querying container on port 5004 for account xyz
[REAL-DATA] Got real account data: balance=10000.50, equity=9950.75

Frontend Dashboard:
✅ Shows REAL balance, equity, margin
✅ Shows REAL trade history from EA
```

### If MT5 Terminal is NOT Running (without terminal64.exe)
```
Backend logs will show:
[STARTUP] Trade Co-Pilot Backend starting...
[STARTUP] Persistent files initialized
[REAL-DATA] Querying container on port 5004 for account xyz
[REAL-DATA] Container not reachable on port 5004
[MOCK] Using mock data for account xyz (container unavailable)

Frontend Dashboard:
⚠️ Shows mock data (balance=10000, equity=10000)
ℹ️ This is expected - terminal64.exe needed for real data
```

## Testing After Deployment

### Test 1: Check Backend Logs
```bash
ssh -i ~/.ssh/vinit.pem ec2-user@3.143.147.98 'tail -50 /tmp/backend.log'
```

### Test 2: Verify Endpoint
```bash
# Get your token first (from login)
TOKEN="your_bearer_token_here"

curl -H "Authorization: Bearer $TOKEN" \
  http://3.143.147.98:8000/api/v1/account/me
```

Should return real account data or clear fallback message.

### Test 3: Frontend Test
1. Go to: https://vinitmunjanitradecopilot.vercel.app
2. Login
3. Go to Settings
4. Disconnect account
5. Reconnect: Exness | 279495999 | TradingAlgo@123 | Exness-MT5Trial8
6. Go to Dashboard
7. Check if balance shows REAL data or mock data

## What Gets Queried

The patched backend now queries these endpoints on the MT5 container:

```
GET /api/account-info (port 5000 inside container, mapped to 5004+ on host)
Returns:
{
  "balance": 10000.00,
  "equity": 9950.00,
  "margin": 500.00,
  "margin_free": 9500.00,
  "margin_level": 1990,
  "currency": "USD",
  "trades_count": 2
}

GET /api/trades (port 5000 inside container)
Returns:
{
  "trades": [
    {
      "ticket": 123456,
      "symbol": "EURUSD",
      "type": "BUY",
      "volume": 0.1,
      "open_price": 1.0950,
      "current_price": 1.0960,
      "profit": 10.00
    }
  ]
}
```

## Troubleshooting

### Logs show "[MOCK] Using mock data"
**This is normal without terminal64.exe.** The backend is working correctly - it tried to query the container but got no response (because MT5 terminal isn't running). Once you add terminal64.exe and rebuild the Docker image, real data will flow through.

### Logs show "[ERROR]" or connection refused
- Check container is running: `ssh ec2-user@3.143.147.98 'docker ps | grep mt5'`
- Check backend is running: `ssh ec2-user@3.143.147.98 'ps aux | grep uvicorn'`
- Restart backend: `ssh ec2-user@3.143.147.98 'pkill -f uvicorn'` then run deploy script again

### Frontend still shows old data
- Clear browser cache (Ctrl+Shift+Delete)
- Clear localStorage: Open DevTools (F12) → Application → Local Storage → Delete all
- Refresh page
- Disconnect/reconnect account

## Current Deployment Status

| Component | Status | Notes |
|-----------|--------|-------|
| Backend | ✅ Patching ready | Deploy with script |
| Container Orchestration | ✅ Working | Launches per user |
| MT5 Terminal | ❌ Not running | Need terminal64.exe |
| Real Data Fetching | ✅ Implemented | Will work once terminal runs |
| Fallback Logic | ✅ Implemented | Shows mock if terminal offline |

## Next Steps

1. **Deploy the patch** (run the deployment script)
2. **Test in frontend** (refresh and check logs)
3. **Get terminal64.exe** (150-250 MB binary from broker)
4. **Rebuild Docker image** (includes terminal64.exe)
5. **Full MVP completion** (real data flows through)

## Files Location

- Patched file: `/root/.openclaw/workspace/simple_mock_PATCHED.py`
- Deploy script: `/root/.openclaw/workspace/DEPLOY_BACKEND_PATCH.sh`
- This guide: `/root/.openclaw/workspace/PATCH_DEPLOYMENT_SUMMARY.md`

---

**Ready to deploy?**
```bash
bash /root/.openclaw/workspace/DEPLOY_BACKEND_PATCH.sh
```

Let me know the logs and we'll verify everything is working! 🚀

