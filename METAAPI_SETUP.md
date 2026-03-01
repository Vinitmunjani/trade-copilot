# MetaAPI Integration Setup Guide

## Overview
This project now uses **MetaAPI** for cloud-based MT4/MT5 account connections, eliminating the need for local terminals or VPS. MetaAPI automatically:
- Provisions cloud accounts connected to your broker
- Manages account deployment and connectivity
- Streams live trade events via webhooks
- Provides real-time account balance, equity, and statistics

## Prerequisites
- An account at a **supported broker** (Alpari, IC Markets, Exness, etc. — [full list](https://metaapi.cloud/docs/client/supported-brokers))
- Your **broker login credentials** (login, password, server name)

## Step 1: Get MetaAPI Tokens

### 1a. Create MetaAPI Account
1. Visit https://www.metaapi.cloud/
2. Click **Sign Up** → Create free account
3. Verify email

### 1b. Obtain Auth Token
1. Log in to metaapi.cloud dashboard
2. Navigate to **Settings** → **API Tokens**
3. Copy your **Auth Token** (long alphanumeric string starting with `e-...` or similar)
   - This is your `METAAPI_TOKEN`

### 1c. Obtain Provisioning Token
1. In the same **Settings** → **API Tokens** section
2. Copy your **Provisioning Token** (used for account creation)
   - This is your `METAAPI_PROVISIONING_TOKEN`

**⚠️ Security**: Never share these tokens or commit them to git. Always use `.env` files.

## Step 2: Configure Environment Variables

### Option A: Local Development
1. Create `.env` file in `backend/` directory:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Edit `backend/.env` and add your tokens:
   ```env
   METAAPI_TOKEN=your-metaapi-auth-token-here
   METAAPI_PROVISIONING_TOKEN=your-metaapi-provisioning-token-here
   ```

### Option B: Production (Railway, Vercel, etc.)
1. Go to your deployment dashboard (Railway, Vercel, etc.)
2. Add environment variables:
   - `METAAPI_TOKEN`: Your MetaAPI auth token
   - `METAAPI_PROVISIONING_TOKEN`: Your MetaAPI provisioning token

## Step 3: Test the Setup

### Test Endpoint with Valid Broker Credentials
```bash
# Terminal 1: Start the backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Test account connection
curl -X POST http://localhost:8000/account/connect \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "login": "12345678",
    "password": "your-broker-password",
    "server": "Alpari-Demo",
    "platform": "mt5"
  }'
```

### Expected Response (Success)
```json
{
  "connected": true,
  "account_id": "metaapi_account_xxxx",
  "balance": 10000.50,
  "equity": 9950.75,
  "currency": "USD",
  "metaapi_account_id": "metaapi_account_xxxx"
}
```

### Troubleshooting

**Error: "METAAPI_TOKEN not configured"**
- ✅ Check `.env` file exists in `backend/` directory
- ✅ Confirm `METAAPI_TOKEN` and `METAAPI_PROVISIONING_TOKEN` are set
- ✅ Restart backend after editing `.env`

**Error: "Invalid broker credentials"**
- ✅ Verify login, password, and server name match your broker account exactly
- ✅ Check if your broker is [supported](https://metaapi.cloud/docs/client/supported-brokers)
- ✅ Ensure account is active (not suspended)

**Error: "Account deployment timeout"**
- ✅ MetaAPI needs 20-30 seconds to deploy the account
- ✅ This is normal on first connection
- ✅ Subsequent connections reuse the same account

## Step 4: Frontend Integration

Once backend is working, the frontend `/account/connect` flow will:

1. **User submits broker credentials**
   ```
   POST /account/connect
   {
     "login": "12345678",
     "password": "password",
     "server": "Alpari-Demo",
     "platform": "mt5"
   }
   ```

2. **Backend provisions MetaAPI account**
   - Creates read-only cloud account
   - Waits for deployment (≈30s first time)
   - Establishes WebSocket streaming connection

3. **Backend returns account data**
   ```json
   {
     "connected": true,
     "balance": 10000,
     "equity": 9950,
     "currency": "USD"
   }
   ```

4. **Live trade events stream via WebSocket**
   - Individual trades are sent real-time to frontend
   - No polling needed

## Architecture Flow

```
User Credentials
      ↓
MetaAPI Provisioning (create cloud account)
      ↓
MetaAPI Deployment (wait for ready)
      ↓
MetaAPI Streaming Connection
      ↓
Account Metrics (balance, equity)
      ↓
WebSocket Events → Frontend
```

## Key Services

### `backend/app/services/metaapi_provisioning.py`
- `create_account(login, password, server, platform)` → Returns account_id
- `wait_for_deployment(account_id, timeout=30)` → Polls until DEPLOYED

### `backend/app/services/metaapi_service.py`
- `connect(user)` → Establishes streaming, returns account metrics
- `_listen_for_events()` → Broadcasts trade events via WebSocket

### `backend/app/api/account.py`
- `POST /account/connect` → Orchestrates provisioning + connection

## Webhook Events

MetaAPI provides real-time trade events:
- **Trade opened**: New position created
- **Trade closed**: Position closed
- **Trade updated**: Stop loss, take profit modified
- **Account balance updated**: Deposits, withdrawals, swaps

These are automatically broadcast to connected WebSocket clients.

## Switching Brokers

To connect a different broker account:
1. User provides new credentials (different login/password/server)
2. Backend creates new MetaAPI account
3. Previous account remains dormant (can be reactivated)
4. MetaAPI manages multiple accounts per user

## Rate Limits

MetaAPI free tier:
- 100 API calls/minute
- 1 streaming connection per account
- 1-hour event history

For production, consider paid MetaAPI plan.

## Support

- MetaAPI Docs: https://metaapi.cloud/docs/client/
- Supported Brokers: https://metaapi.cloud/docs/client/supported-brokers
- Issues: Check backend logs with `LOG_LEVEL=DEBUG`

---

**Note**: This replaces the previous VPS terminal approach entirely. No local MT5 installation needed.
