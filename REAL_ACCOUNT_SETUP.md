# Real Account Connection Setup Guide

## Overview

To test TradeCo-Pilot with a real MetaAPI-connected account, you need:

1. **MetaAPI Account** - For connecting real MT4/MT5 accounts
2. **Trading Account** - MT4 or MT5 demo/live account
3. **API Token** - Authentication for MetaAPI access

---

## Step 1: Create MetaAPI Account

1. **Sign up** at [https://app.metaapi.cloud/](https://app.metaapi.cloud/)
2. **Get your API Token**:
   - Go to Account Settings
   - Find "API Token" section
   - Copy your token (format: `eyJhbGciOiJIUzI1NiIs...`)

3. **Set Environment Variable**:
   ```powershell
   # Windows PowerShell
   $env:METAAPI_TOKEN = 'your-api-token-here'
   
   # Or add to .env file in backend directory:
   METAAPI_TOKEN=your-api-token-here
   METAAPI_PROVISIONING_TOKEN=your-provisioning-token-here
   ```

---

## Step 2: Get Trading Account Details

Use a demo or live MT5 account:

### Option A: Use Exness Demo Account
```
Server: Exness-MT5Trial8
Login: (check your Exness account)
Password: (check your Exness account)
```

### Option B: Use Your Own Account
- Get credentials from your broker
- Ensure the account supports API connections

---

## Step 3: Run Real Account Test

### With No MetaAPI Token (Demo Mode)
```powershell
cd backend
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
python real_account_workflow.py
```

**Output**: Shows setup instructions

---

### With MetaAPI Token (Real Connection)
```powershell
cd backend
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
$env:METAAPI_TOKEN='your-api-token'

python real_account_workflow.py `
  --login 19023151 `
  --password your_password `
  --server Exness-MT5Trial8 `
  --metaapi-token your-api-token
```

**Output**: 
- ✓ Account connected
- ✓ Live positions displayed
- ✓ WebSocket streaming active
- ✓ Real trades in P&L streaming

---

## Step 4: What Happens When Connected

### Account Connection Flow
```
1. Backend receives: POST /api/v1/account/connect
   - Login credentials (encrypted)
   - Server name
   - Platform (MT4/MT5)

2. MetaAPI provision service:
   - Creates cloud account in MetaAPI
   - Associates credentials

3. MetaAPI streaming service:
   - Opens WebSocket to MT terminal
   - Monitors positions every 1 second
   - Detects trade opens, closes, updates

4. Database persistence:
   - MetaAccount model stores connection
   - Heartbeat updated every 5 minutes
   - Trade history maintained

5. WebSocket broadcasting:
   - All client connections get:
     * TRADE_OPENED with AI score
     * TRADE_CLOSED with P&L
     * TRADE_UPDATED with SL/TP changes
```

---

## Step 5: Monitor Real Trading

Once connected, you can:

### Via API
```bash
# Check account status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/account/status

# Get trader data
curl http://localhost:8000/api/v1/dev/trader-data?email=trader@example.com
```

### Via WebSocket
```javascript
// Connect
const ws = new WebSocket(
  'ws://localhost:8000/api/v1/ws/trades?token=' + jwtToken
);

// Listen for events
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.event === 'TRADE_OPENED') {
    console.log(`🟢 ${data.symbol} ${data.direction} at ${data.entry_price}`);
    console.log(`   AI Score: ${data.ai_score}/10`);
  }
  
  if (data.event === 'TRADE_CLOSED') {
    console.log(`🔴 ${data.symbol} P&L: ${data.pnl} (${data.pnl_r}%)`);
  }
};
```

---

## Step 6: Test Real Streaming Scenario

### What You'll See

**When a trade opens in your MT5 terminal:**
```
✓ [TRADE_OPENED] EURUSD BUY @ 1.10500
  AI Score: 7/10
  Analysis: 
    - Confidence: 0.85
    - Summary: Good entry on support level
    - Issues: ["Correlated: has existing EURUSD position"]
    - Strengths: ["Follows trend direction"]
```

**When the trade closes:**
```
🟢 [TRADE_CLOSED] EURUSD
  P&L: +250.00 USD (5.23%)
  Exit Price: 1.10750
  Duration: 45 minutes
```

**Real-time position updates:**
```
[TRADE_UPDATED] EURUSD
  SL moved to: 1.10400
  TP moved to: 1.11000
```

---

## Step 7: Architecture with Real Account

```
                    MT5 Terminal
                         |
                         | (MetaAPI Cloud)
                         v
                  MetaAPI Streaming
                         |
                    (WebSocket)
                         v
                  TradeCo-Pilot API
                         |
         +-------+-------+-------+
         |       |       |       |
         v       v       v       v
      Trade   Behavioral  AI    Database
      Detect  Analysis    Score  Store
         |       |       |       |
         +-------+-------+-------+
                  |
                  v
             WebSocket Manager
                  |
         +-------+-------+-------+
         |       |       |       |
         v       v       v       v
       Client  Client  Client  Dashboard
      Browser  App    Mobile   Website
```

---

## Troubleshooting

### Issue: "Invalid credentials"
- ✓ Check login/password are correct
- ✓ Verify server name matches broker
- ✓ Try demo account first

### Issue: "MetaAPI connection failed"
- ✓ Check API token is valid
- ✓ Verify internet connection
- ✓ Check account is provisioned in MetaAPI dashboard

### Issue: "No trades appearing"
- ✓ Open a manual trade in MT5 terminal
- ✓ Wait 2-3 seconds for streaming update
- ✓ Check WebSocket is connected: look for "CONNECTED" message

### Issue: "Token invalid/expired"
- ✓ JWT tokens expire after 7 days
- ✓ Re-authenticate via POST /api/v1/auth/login
- ✓ Use new token in WebSocket URL

---

## Advanced: Docker Deployment

For production, deploy with Docker:

```bash
# Set environment variables
export METAAPI_TOKEN=your-token
export DATABASE_URL=postgresql://user:pass@postgres:5432/db
export REDIS_URL=redis://redis:6379

# Run container
docker run -e METAAPI_TOKEN -e DATABASE_URL -e REDIS_URL \
  -p 8000:8000 tradecopilot:latest
```

---

## Security Notes

🔒 **Important:**
- Never commit API tokens to git
- Use .env file (add to .gitignore)
- Use environment variables in production
- Rotate tokens regularly
- Use strong passwords for MT account
- Enable 2FA on MetaAPI account

---

## Next Steps

1. ✅ Create MetaAPI account
2. ✅ Get API token
3. ✅ Set METAAPI_TOKEN environment variable
4. ✅ Run real account test
5. ✅ Monitor live trading and streaming
6. ✅ Deploy to production with PostgreSQL

---

**For questions or issues**: Check logs in backend terminal or review MetaAPI documentation at https://metaapi.cloud/docs/
