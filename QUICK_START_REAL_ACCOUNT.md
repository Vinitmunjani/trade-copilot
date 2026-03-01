# Quick Reference: Connect Real MetaAPI Account to trader@example.com

## TL;DR - 3 Steps to Connect

### Step 1: Get MetaAPI Token
```
👉 Go to https://app.metaapi.cloud/
👉 Sign up (free trial available)
👉 Copy your API token from Account Settings
```

### Step 2: Set Environment Variable
```powershell
# Windows PowerShell
$env:METAAPI_TOKEN = 'your-api-token-here'
$env:DATABASE_URL = 'sqlite+aiosqlite:///./dev.db'

# Or add to .env file:
METAAPI_TOKEN=your-api-token-here
```

### Step 3: Run Connection Test
```bash
cd backend
python real_account_workflow.py \
  --login 19023151 \
  --password your_password \
  --server Exness-MT5Trial8 \
  --metaapi-token your-api-token
```

---

## Example: Using Exness Demo Account

```bash
# Get your Exness MT5 demo credentials:
# 1. Go to https://www.exness.com/
# 2. Create MT5 account
# 3. Download MT5 terminal
# 4. Note your login number & password

# Then run:
python real_account_workflow.py \
  --login YOUR_EXNESS_LOGIN \
  --password YOUR_PASSWORD \
  --server Exness-MT5Trial8 \
  --metaapi-token YOUR_METAAPI_TOKEN
```

---

## What Happens When Connected

### Real-Time Events Stream Via WebSocket
```
✓ [CONNECTED] WebSocket connected to trader@example.com

📌 [14:25:30] You open EURUSD BUY
✓ [TRADE_OPENED] EURUSD BUY @ 1.10500
ℹ AI Score: 8/10
ℹ Analysis: Excellent entry on support, volume confirmation

📌 [14:31:00] You move stop loss
✓ [TRADE_UPDATED] EURUSD
ℹ SL: 1.10050 → 1.10350 (locking profit)

📌 [14:35:45] Trade hits take profit
✓ [TRADE_CLOSED] EURUSD BUY
ℹ Profit: +400.00 USD (1.91%)
ℹ Duration: 20 minutes 15 seconds
```

---

## Account Dashboard Response

Once connected, you get:

```json
{
  "connected": true,
  "broker": "Exness",
  "platform": "MT5",
  "login": "19023151",
  "server": "Exness-MT5Trial8",
  "balance": 10000.00,
  "equity": 10450.50,
  "free_margin": 9450.50,
  "used_margin": 1000.00,
  "margin_level": 1045.05
}
```

---

## Live Positions with AI Analysis

```
EURUSD BUY     | Entry: 1.10250 | Current: 1.10450 
               | P&L: +$400.00 (+1.91%) | AI: 8/10

GBPUSD SELL    | Entry: 1.27500 | Current: 1.27400
               | P&L: +$150.00 (+0.99%) | AI: 7/10

USDJPY BUY     | Entry: 150.50 | Current: 150.60
               | P&L: -$100.00 (-0.66%) | AI: 5/10
               | ⚠ Correlated position warning
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid token" | Check MetaAPI token at https://app.metaapi.cloud/settings |
| "Invalid credentials" | Verify MT5 login/password with your broker |
| "Server not found" | Use correct server name (e.g., Exness-MT5Trial8) |
| "Connection timeout" | Check internet connection, MetaAPI service status |
| "No trades appearing" | Open a manual trade in MT5, wait 2-3 seconds |

---

## Verify It's Working

### Check Account Status
```bash
curl -H "Authorization: Bearer $JWT_TOKEN" \
  http://localhost:8000/api/v1/account/status
```

### View Trader Data
```bash
curl http://localhost:8000/api/v1/dev/trader-data?email=trader@example.com
```

### Listen for WebSocket Events
```bash
# In Python:
import asyncio, websockets, json

async def listen():
    uri = f"ws://localhost:8000/api/v1/ws/trades?token={your_jwt_token}"
    async with websockets.connect(uri) as ws:
        async for msg in ws:
            data = json.loads(msg)
            print(f"Event: {data['event']}")

asyncio.run(listen())
```

---

## Multi-Account Support

You can connect multiple MT5 accounts to trader@example.com:

```bash
# First account
python real_account_workflow.py \
  --login 12345678 \
  --password password1 \
  --server Exness-MT5Trial8

# Second account (same user)
python real_account_workflow.py \
  --login 87654321 \
  --password password2 \
  --server FxPro-MT5
```

Both accounts will stream events to the same WebSocket connection.

---

## Full System Diagram

```
Your MT5 Terminals
       │
       ├─ Account 1 (Login: 12345678)
       ├─ Account 2 (Login: 87654321)
       └─ Account 3 (Login: 11223344)
               │
              [MetaAPI Cloud]
               │
         [TradeCo-Pilot API]
               │
         [trader@example.com]
               │
        ┌──────┼──────┐
        │      │      │
    [REST API] [WebSocket] [Database]
        │      │      │
        │      │    Trades
        │      │    Accounts
        │      │    Performance
        │      │
    Account   Real-time Events:
    Status    - TRADE_OPENED
    Positions - TRADE_CLOSED
    Balance   - TRADE_UPDATED
```

---

## Environment Variables Quick Reference

```bash
# Required for real MetaAPI
METAAPI_TOKEN=your-api-token-here

# Optional but recommended
METAAPI_PROVISIONING_TOKEN=provisioning-token

# Database (use SQLite for dev, PostgreSQL for prod)
DATABASE_URL=sqlite+aiosqlite:///./dev.db
# or
DATABASE_URL=postgresql://user:pass@localhost:5432/tradeco

# Optional: AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Cache
REDIS_URL=redis://localhost:6379/0
```

---

## Success Indicators

When everything is working, you should see:

✅ `[STEP 1] Prepare user account (trader@example.com)` → ✓ Authenticated  
✅ `[STEP 2] Check MetaAPI requirements` → ✓ Token configured  
✅ `[STEP 3] Connect MetaAPI account` → ✓ Account connected successfully  
✅ `[STEP 4] Retrieve real account data` → ✓ Live data retrieved  
✅ `[STEP 5] Fetch live positions` → ✓ Open positions displayed  
✅ `[STEP 6] Monitor real-time WebSocket` → ✓ Events streaming  

---

## Contact & Support

- **MetaAPI Docs:** https://metaapi.cloud/docs/
- **API Status:** https://app.metaapi.cloud/
- **Report Issues:** Check backend logs for error details

---

**Ready to trade with AI analysis? Connect your account now!** 🚀
