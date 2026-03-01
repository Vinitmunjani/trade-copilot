"""FastAPI application entry point.
from typing import Union

Configures the app with lifespan events, CORS, and all routers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, close_db
from app.core.dependencies import init_redis, close_redis
from app.api.router import api_router
from app.api.ws import ws_manager
from app.services.metaapi_service import metaapi_service

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events.

    Startup:
        - Initialize database tables
        - Connect to Redis
        - Wire up WebSocket manager to MetaAPI service

    Shutdown:
        - Close Redis connection
        - Close database connection pool
    """
    logger.info("🚀 Starting AI Trade Co-Pilot Backend...")

    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

    # Initialize Redis
    try:
        redis = await init_redis()
        if redis:
            logger.info("✅ Redis connected")
        else:
            logger.warning("⚠️ Redis unavailable — running without cache")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")

    # Wire up WebSocket manager to MetaAPI service
    metaapi_service.set_ws_manager(ws_manager)
    await metaapi_service.lifespan()
    logger.info("✅ WebSocket manager connected to MetaAPI service")

    logger.info("🟢 AI Trade Co-Pilot Backend ready!")

    yield

    # Shutdown
    logger.info("🔴 Shutting down AI Trade Co-Pilot Backend...")
    await metaapi_service.shutdown()
    await close_redis()
    await close_db()
    logger.info("👋 Shutdown complete")


app = FastAPI(
    title="AI Trade Co-Pilot",
    description=(
        "AI-powered trading assistant that monitors your MT4/MT5 trades in real-time, "
        "scores trade quality, detects behavioral patterns, and provides actionable insights."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "https://vinitmunjanitradecopilot.vercel.app",
        "https://*.vercel.app",
        "https://*.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "AI Trade Co-Pilot",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check with dependency status."""
    from app.core.dependencies import _redis_client

    redis_ok = False
    if _redis_client:
        try:
            await _redis_client.ping()
            redis_ok = True
        except Exception:
            pass

    return {
        "status": "healthy",
        "redis": "connected" if redis_ok else "disconnected",
        "websocket_connections": len(ws_manager.get_connected_users()),
    }


# Dev simulation endpoint
@app.post("/dev/simulate-trade", tags=["Development"])
async def dev_simulate_trade(
    symbol: str = "EURUSD",
    direction: str = "BUY",
    entry_price: float = 1.0850,
    sl: float = 1.0820,
    tp: float = 1.0920,
    lot_size: float = 0.1,
):
    """Quick trade simulation endpoint for development testing.

    No authentication required — for dev/testing only.
    Creates a simulated trade and returns the result.
    """
    if settings.APP_ENV != "development":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Only available in development mode")

    return {
        "message": "Use POST /api/v1/trades/simulate with authentication for full simulation",
        "hint": "Register at POST /api/v1/auth/register first",
    }
