# Trade Co-Pilot Frontend

A Next.js 14 App Router frontend for the AI Trade Co-Pilot MVP. Professional dark trading terminal theme with comprehensive trading analytics and behavioral pattern detection.

## Features

- 🎯 **Real-time Trade Scoring** - AI-powered 1-10 scoring system
- 🧠 **Behavioral Analysis** - Detect revenge trading, FOMO, overtrading patterns
- 📊 **Comprehensive Analytics** - Equity curves, win rate charts, R distribution
- 🛡️ **Rule Management** - Define and track trading rule adherence
- 📱 **Responsive Design** - Works on desktop and tablet
- ⚡ **Real-time Updates** - WebSocket integration for live data

## Tech Stack

- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Zustand** for state management
- **Radix UI** for accessible components
- **Recharts** for data visualization
- **Lucide React** for icons

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
├── components/
│   ├── ui/                # Reusable UI components
│   ├── layout/            # Navigation components
│   ├── dashboard/         # Dashboard-specific components
│   ├── trades/            # Trade management components
│   ├── analytics/         # Chart and analytics components
│   ├── patterns/          # Behavioral pattern components
│   ├── rules/             # Rule management components
│   └── common/            # Shared utility components
├── hooks/                 # Custom React hooks
├── lib/                   # Utilities and API client
├── stores/                # Zustand state management
└── types/                 # TypeScript type definitions
```

## Getting Started

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your backend URL
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Build for production:**
   ```bash
   npm run build
   npm start
   ```

## Key Pages

- **Landing Page** - Marketing homepage with feature overview
- **Authentication** - Login/register with JWT tokens
- **Dashboard** - Today's P&L, open trades, readiness score, alerts
- **Trade History** - Sortable/filterable table with AI scores
- **Analytics** - Equity curve, win rate charts, R distribution
- **Patterns** - Timeline of behavioral patterns with statistics
- **Rules** - Trading rules editor and pre-trade checklist
- **Reports** - Weekly AI-generated performance reports
- **Settings** - Account settings and broker connection

## Theme & Design

Dark trading terminal aesthetic inspired by Bloomberg Terminal:
- **Background:** slate-950 (#020617)
- **Cards:** slate-900 with slate-800 borders
- **Primary:** emerald-500 for profits/positive values
- **Danger:** red-500 for losses/negative values
- **Text:** slate-100 primary, slate-400 secondary
- **Font:** Inter for clean, professional look

## Mock Data

The app includes comprehensive mock data for development:
- Sample trades with AI scores and behavioral flags
- Historical analytics data for charts
- Behavioral alerts and patterns
- Trading rules and checklists

## API Integration

- **Base URL:** `http://localhost:8000` (configurable)
- **WebSocket:** `ws://localhost:8000/ws/trades` for real-time updates
- **Authentication:** JWT tokens stored in localStorage
- **Auto-retry:** Built-in reconnection logic for WebSocket

## Development Notes

- Uses `use client` directives for client-side components
- Zustand stores handle all state management
- Custom hooks abstract API and WebSocket logic
- Responsive design with mobile-first approach
- Accessible components using Radix UI primitives

## Contributing

1. Follow the existing file structure
2. Use TypeScript for all new code
3. Maintain the dark theme consistency
4. Add proper error handling and loading states
5. Write comprehensive mock data for development
