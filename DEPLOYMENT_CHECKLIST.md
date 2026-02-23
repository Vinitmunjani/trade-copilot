# Trade Co-Pilot Backend Patch - Deployment Checklist

## Pre-Deployment Checklist
- [ ] You have SSH access to EC2 (can run: `ssh -i ~/.ssh/vinit.pem ec2-user@3.143.147.98`)
- [ ] SSH key is at: `~/.ssh/vinit.pem` (or adjust path in script)
- [ ] Internet connection is stable
- [ ] Frontend is currently accessible: https://vinitmunjanitradecopilot.vercel.app

## Deployment Execution
- [ ] Run deployment script: `bash /root/.openclaw/workspace/DEPLOY_BACKEND_PATCH.sh`
- [ ] Script completes without errors
- [ ] See message: "✅ Backend patch deployed successfully!"

## Post-Deployment Verification

### 1. Check Backend Logs ✅
Run:
```bash
ssh -i ~/.ssh/vinit.pem ec2-user@3.143.147.98 'tail -50 /tmp/backend.log'
```

Look for ONE of these:

**Success (with MT5 terminal running):**
```
[STARTUP] Trade Co-Pilot Backend starting...
[STARTUP] Persistent files initialized
[REAL-DATA] Querying container on port 5004 for account xyz
[REAL-DATA] Got real account data: balance=10000.50, equity=9950.75
```
- [ ] See this? ✅ MT5 terminal is running (you have terminal64.exe)
- [ ] Proceed to step 2

**Expected (without MT5 terminal):**
```
[STARTUP] Trade Co-Pilot Backend starting...
[STARTUP] Persistent files initialized
[REAL-DATA] Querying container on port 5004 for account xyz
[REAL-DATA] Container not reachable on port 5004
[MOCK] Using mock data for account xyz (container unavailable)
```
- [ ] See this? ✅ Patch is working correctly
- [ ] Normal without terminal64.exe
- [ ] Proceed to step 2

**Error (something went wrong):**
```
[ERROR] ...
```
- [ ] See this? ❌ Check troubleshooting section below

### 2. Test Frontend UI ✅

1. [ ] Open: https://vinitmunjanitradecopilot.vercel.app
2. [ ] Login with your credentials
3. [ ] Go to **Settings** page
4. [ ] Click **Disconnect** button
5. [ ] Fill in connection form:
   - Broker: **Exness**
   - Account: **279495999**
   - Password: **TradingAlgo@123**
   - Server: **Exness-MT5Trial8**
6. [ ] Click **Connect**
7. [ ] Wait 3-5 seconds for container to launch
8. [ ] Go to **Dashboard** page
9. [ ] Check Account Balance display:

**If you see a number for balance:** ✅ Patch is working
- [ ] Frontend loads REAL (or fallback) data successfully
- [ ] Move to step 3

**If you see ERROR or blank:** ❌ Check troubleshooting below

### 3. Check Browser Console (Advanced) ✅

1. [ ] Open Frontend: https://vinitmunjanitradecopilot.vercel.app
2. [ ] Press **F12** to open Developer Tools
3. [ ] Go to **Console** tab
4. [ ] Look for any red errors
5. [ ] Check **Network** tab:
   - [ ] Find request to `/api/v1/account/me`
   - [ ] Status should be **200** (green)
   - [ ] Response contains balance/equity fields

### 4. Verify Backend Process ✅

Run:
```bash
ssh -i ~/.ssh/vinit.pem ec2-user@3.143.147.98 'ps aux | grep uvicorn'
```

Should show:
```
root 12345  0.0  0.2 ... python -m uvicorn backend.simple_mock:app ...
```
- [ ] Process is running
- [ ] PID (first number) is present
- [ ] If not running, restart: `bash /root/.openclaw/workspace/DEPLOY_BACKEND_PATCH.sh`

## Troubleshooting

### Problem: "[ERROR] Cannot connect to EC2 instance"

**Solution:**
1. Check SSH key location: `ls -la ~/.ssh/vinit.pem`
2. Check key permissions: `chmod 600 ~/.ssh/vinit.pem`
3. Test SSH manually: `ssh -i ~/.ssh/vinit.pem ec2-user@3.143.147.98 'echo OK'`
4. If still fails, get your new IP from AWS console and update script

### Problem: Logs show "[ERROR] Failed to deploy"

**Solution:**
1. Check backend directory exists: `ssh -i ~/.ssh/vinit.pem ec2-user@3.143.147.98 'ls -la /home/ec2-user/trade-copilot/backend/'`
2. Manually deploy (see PATCH_DEPLOYMENT_SUMMARY.md for manual steps)
3. Check disk space: `ssh -i ~/.ssh/vinit.pem ec2-user@3.143.147.98 'df -h'`

### Problem: Frontend shows no data or error

**Solution:**
1. Clear browser cache: **Ctrl+Shift+Delete**
2. Clear localStorage: **F12 → Application → Local Storage → Clear All**
3. Refresh page
4. Disconnect and reconnect account
5. Check backend logs: `ssh -i ~/.ssh/vinit.pem ec2-user@3.143.147.98 'tail -100 /tmp/backend.log'`

### Problem: Logs show "[MOCK] Using mock data"

**This is NORMAL and EXPECTED without terminal64.exe!**

The patch is working correctly - it's just using the fallback because:
- [ ] MT5 terminal is NOT running in the container
- [ ] Need to get terminal64.exe (150-250 MB binary)
- [ ] Next step: Rebuild Docker image with terminal64.exe

### Problem: "Backend is running but frontend can't connect"

**Check CORS:**
```bash
curl -i -H "Origin: https://vinitmunjanitradecopilot.vercel.app" \
  http://3.143.147.98:8000/health
```

Should see:
```
Access-Control-Allow-Origin: *
```

If not, CORS might be blocked. Check firewall: `ssh -i ~/.ssh/vinit.pem ec2-user@3.143.147.98 'sudo ufw status'`

## Success Criteria ✅

All of these should be true:

1. [ ] Deployment script runs without errors
2. [ ] Backend logs show either [REAL-DATA] or [MOCK] prefix
3. [ ] Frontend loads without JavaScript errors
4. [ ] Can login and connect account
5. [ ] Dashboard shows balance (real or mock)
6. [ ] No 401/403/500 errors in Network tab

## Next Steps After Successful Deployment

### Immediate (Done!)
- ✅ Backend now fetches from containers instead of hardcoded mock
- ✅ System has intelligent fallback logic
- ✅ Frontend can display real data when available

### Short Term (1-2 hours)
1. Get terminal64.exe from broker website
2. Copy to EC2: `scp -i vinit.pem terminal64.exe ec2-user@3.143.147.98:/home/ec2-user/trade-copilot/mt5-engine/`
3. Rebuild Docker: `ssh -i vinit.pem ec2-user@3.143.147.98 'cd /home/ec2-user/trade-copilot/mt5-engine && docker build -t mt5-engine:latest .'`
4. Restart container from frontend
5. Dashboard will show REAL MT5 account data

### Medium Term (After MVP validation)
- Deploy Polymarket Bitcoin Arbitrage Bot
- Run end-to-end tests with real trades
- Monitor for 1-2 weeks

## Files for Reference

- Patched file: `/root/.openclaw/workspace/simple_mock_PATCHED.py`
- Deploy script: `/root/.openclaw/workspace/DEPLOY_BACKEND_PATCH.sh`
- Deployment guide: `/root/.openclaw/workspace/PATCH_DEPLOYMENT_SUMMARY.md`
- This checklist: `/root/.openclaw/workspace/DEPLOYMENT_CHECKLIST.md`

---

**Status:** All necessary changes implemented. Ready for deployment! 🚀

