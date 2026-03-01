"""Main API router aggregating all route modules."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.trades import router as trades_router
from app.api.stats import router as stats_router
from app.api.rules import router as rules_router
from app.api.analysis import router as analysis_router
from app.api.account import router as account_router
from app.api.webhook import router as webhook_router
from app.api.ws import router as ws_router
from app.api.billing import router as billing_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(trades_router)
api_router.include_router(stats_router)
api_router.include_router(rules_router)
api_router.include_router(analysis_router)
api_router.include_router(account_router)
api_router.include_router(webhook_router)
api_router.include_router(ws_router)
api_router.include_router(billing_router)
