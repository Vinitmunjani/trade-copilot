# AI Trade Co-Pilot MVP

A real-time AI trading assistant that analyzes every trade **before, during, and after** execution.

## Features

- **Pre-Trade Analysis**: AI scores every trade plan (1-10) before execution
- **Real-Time Monitoring**: Live alerts during trades (move SL, take profits, risk warnings)  
- **Post-Trade Reviews**: AI analysis of what went right/wrong
- **Behavioral Pattern Detection**: Revenge trading, overtrading, session weaknesses
- **Trading Dashboard**: P&L tracking, win rates, equity curves, rule adherence
- **Broker Integration**: MT4/MT5 via MetaAPI (real-time trade detection)

## Tech Stack

- **Backend**: Python FastAPI + PostgreSQL + Redis + MetaAPI
- **Frontend**: Next.js 14 + Tailwind + shadcn/ui + Recharts
- **AI**: Claude/GPT-4 for trade analysis
- **Deployment**: Docker Compose

## Quick Start

### 1. Prerequisites

Get these API keys:
- [MetaAPI](https://metaapi.cloud) account (free tier)
- [OpenAI](https://platform.openai.com) or [Anthropic](https://console.anthropic.com) API key

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 3. Run with Docker

```bash
# Start all services (PostgreSQL + Redis + Backend + Frontend)
docker-compose up -d

# Watch logs
docker-compose logs -f
```

### 4. Access the App

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 5. Connect Your Trading Account

1. Register/login at localhost:3000
2. Go to Settings → Connect Account
3. Enter your MetaAPI token + account ID
4. Start trading → get real-time AI scores!

## Development

### Backend Only
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Edit with your keys
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend Only  
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
trade-copilot/
├── backend/           # FastAPI Python backend
│   ├── app/
│   │   ├── api/       # REST endpoints
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic (AI, MetaAPI, etc.)
│   │   └── core/      # Auth, dependencies, config
│   └── alembic/       # Database migrations
├── frontend/          # Next.js React frontend
│   └── src/
│       ├── app/       # App Router pages
│       ├── components/ # UI components
│       ├── stores/    # Zustand state management
│       ├── hooks/     # Custom React hooks
│       └── lib/       # API client, WebSocket, utilities
└── docker-compose.yml # Full stack deployment
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login (returns JWT)
- `GET /auth/me` - Get current user

### Trades
- `GET /trades` - List trades (with filters)
- `GET /trades/open` - Current open trades
- `GET /trades/{id}` - Single trade detail

### Stats & Analytics
- `GET /stats/overview` - Today's P&L, win rate, etc.
- `GET /stats/daily` - Daily stats time series
- `GET /stats/symbol/{symbol}` - Per-symbol performance
- `GET /stats/sessions` - Performance by trading session

### Rules & Patterns
- `GET /rules` - User's trading rules
- `PUT /rules` - Update rules
- `GET /analysis/patterns` - Behavioral patterns detected
- `GET /analysis/readiness` - Current readiness to trade score

### Account Management
- `POST /account/connect` - Connect MetaAPI account
- `GET /account/status` - Connection status
- `POST /dev/simulate-trade` - Simulate trade for testing

### Real-Time
- `WebSocket /ws/trades` - Live trade events + AI scores

## How It Works

1. **Connect Account**: User connects MT4/MT5 via MetaAPI token
2. **Trade Detection**: Backend listens to MetaAPI WebSocket for trade events
3. **Pre-Trade Analysis**: When trade opens → AI analyzes setup → scores 1-10
4. **Real-Time Alerts**: During trade → monitors price action → sends alerts
5. **Post-Trade Review**: When trade closes → AI reviews performance
6. **Pattern Learning**: System learns user's behavioral patterns over time
7. **Dashboard Updates**: All data flows to dashboard via WebSocket

## License

MIT