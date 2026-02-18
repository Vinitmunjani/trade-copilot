# 🚀 Trade Co-Pilot - Cloud Deployment Guide

## Backend Deployment (Railway)

1. **Create Railway Project:**
   - Go to [railway.app](https://railway.app)
   - Connect your GitHub account
   - Create new project from GitHub repo

2. **Configure Environment Variables:**
   ```bash
   DATABASE_URL=sqlite:///./trade_copilot.db
   REDIS_URL=redis://redis.railway.internal:6379
   OPENAI_API_KEY=your-key-here
   ANTHROPIC_API_KEY=your-key-here
   JWT_SECRET=your-secure-secret-here
   METAAPI_PROVISIONING_TOKEN=your-token-here
   ```

3. **Add Redis Service:**
   - In Railway dashboard, add Redis service
   - Connect to your backend service

## Frontend Deployment (Vercel)

1. **Deploy to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Import from GitHub
   - Select the `frontend` folder as root

2. **Configure Environment Variables:**
   ```bash
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
   NEXT_PUBLIC_WS_URL=wss://your-backend.railway.app/ws
   ```

## Post-Deployment

1. **Update CORS Origins:**
   - Add your Vercel domain to backend CORS settings
   - Redeploy backend

2. **Test Endpoints:**
   - Frontend: https://your-app.vercel.app
   - API Docs: https://your-backend.railway.app/docs
   - Health: https://your-backend.railway.app/health

## Database Migration

Your SQLite database will be created automatically on first run.
For production, consider upgrading to PostgreSQL on Railway.
